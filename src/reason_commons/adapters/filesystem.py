"""POSIX single-writer YAML store with a manifest publication boundary.

Immutable files use link rather than replace. Mutable files use atomic rename.
All files and parent directories are fsynced before success is reported.
"""

import base64
from copy import deepcopy
import fcntl
import hashlib
import os
from pathlib import Path
import re
import shutil
import tempfile
import uuid
import zipfile

import yaml

from reason_commons.application.ports import StoreError, WriterBusy
from reason_commons.domain.model import (InvalidCase, Snapshot, StaleWork, require, shape,
                                         validate_ancestry, validate_input)


MAX_FILE = 16 * 1024 * 1024
MAX_BUNDLE = 256 * 1024 * 1024
PATH_PATTERN = re.compile(r"(?:manifest\.yaml|cursor\.yaml|allocations\.yaml|revisions/\d{6,}\.yaml|"
                          r"inputs/in\d{3,}\.yaml|attempts/in\d{3,}-\d{3,}-(?:start|response|result-\d+)\.yaml|"
                          r"sources/s[0-9a-f]{32}\.yaml)")


# The C parser reads the same safe YAML much faster; writing (and so every hash)
# keeps the pure-Python dumper, so stored bytes do not change.
SAFE_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def encoded(value: dict) -> bytes:
    try:
        return yaml.safe_dump(value, sort_keys=True, allow_unicode=True).encode("utf-8")
    except (yaml.YAMLError, TypeError, ValueError, RecursionError) as exc:
        raise StoreError("Record cannot be serialized as safe YAML") from exc


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def wrapped(value: dict) -> bytes:
    return encoded({"sha256": digest(encoded(value)), "data": value})


def read_yaml(path: Path) -> dict:
    try:
        if path.is_symlink() or path.stat().st_size > MAX_FILE:
            raise StoreError("Unsupported storage file")
        value = yaml.load(path.read_bytes(), Loader=SAFE_LOADER)
        if not isinstance(value, dict):
            raise StoreError("Storage record is not an object")
        return value
    except (OSError, yaml.YAMLError, ValueError) as exc:
        raise StoreError(f"Cannot read valid storage record: {path.name}") from exc


def read_wrapped(path: Path) -> dict:
    value = read_yaml(path)
    if set(value) != {"sha256", "data"} or not isinstance(value["data"], dict):
        raise StoreError("Invalid hashed storage record")
    if digest(encoded(value["data"])) != value["sha256"]:
        raise StoreError("Storage hash mismatch")
    return value["data"]


def sync_directory(path: Path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def sync_file(path: Path):
    try:
        with path.open("rb") as stream:
            os.fsync(stream.fileno())
    except OSError as exc:
        raise StoreError(f"Cannot confirm durability of {path.name}") from exc


def atomic_write(path: Path, content: bytes, immutable: bool = False):
    temporary = None
    try:
        if len(content) > MAX_FILE:
            raise StoreError("Storage record exceeds size limit")
        descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if immutable:
            os.link(temporary, path)  # fails if a committed file already exists
            os.unlink(temporary)
        else:
            os.replace(temporary, path)
        temporary = None
        sync_directory(path.parent)
    except OSError as exc:
        raise StoreError(f"Cannot durably write {path.name}") from exc
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass


class FileCaseStore:
    def __init__(self, root, writable=True):
        self.root = Path(root)
        self._lock = None
        self._writable = writable
        try:
            if not self.root.is_dir() or self.root.is_symlink():
                raise StoreError("Case store must be a regular directory")
            for directory in ("revisions", "inputs", "attempts", "sources"):
                if not (self.root / directory).is_dir() or (self.root / directory).is_symlink():
                    raise StoreError("Invalid case directory")
            if writable:
                lock_path = self.root / "writer.lock"
                if lock_path.is_symlink():
                    raise StoreError("Invalid lock file")
                self._lock = open(lock_path, "a+b")
                try:
                    fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise WriterBusy("Another process is editing this case") from exc
            self.validate()
        except Exception:
            self.close()
            raise

    @classmethod
    def create(cls, root, initial: Snapshot):
        root = Path(root)
        initial.validate({})
        # Reserve a new directory exclusively; never overwrite an existing case.
        try:
            root.mkdir(mode=0o700)
        except OSError as exc:
            raise StoreError("New case destination must not exist and its parent must be writable") from exc
        try:
            for name in ("revisions", "inputs", "attempts", "sources"):
                (root / name).mkdir(mode=0o700)
            content = encoded(initial.to_dict())
            atomic_write(root / "revisions/000000.yaml", content, immutable=True)
            atomic_write(root / "cursor.yaml", wrapped({}))
            atomic_write(root / "allocations.yaml", wrapped({"revision": 0, "counters": {}}))
            atomic_write(root / "manifest.yaml", encoded({"schema_version": "1", "delivery_profile": "p2",
                         "case_id": initial.value["case_id"], "current_revision": 0,
                         "revisions": {0: digest(content)}}))
            sync_directory(root)
            sync_directory(root.parent)
            return cls(root)
        except Exception:
            shutil.rmtree(root)
            raise

    def close(self):
        if self._lock is not None:
            self._lock.close()  # OS releases lock even after process termination
            self._lock = None

    def _editing(self):
        if not self._writable or self._lock is None:
            raise StoreError("This session is read-only or closed")

    def _manifest(self):
        value = read_yaml(self.root / "manifest.yaml")
        try:
            shape(value, {"schema_version", "delivery_profile", "case_id", "current_revision", "revisions"},
                  {"schema_version", "delivery_profile", "case_id", "current_revision", "revisions"}, "manifest")
            require(value["schema_version"] == "1" and value["delivery_profile"] == "p2", "Unsupported profile")
            require(type(value["current_revision"]) is int and value["current_revision"] >= 0, "Invalid head")
            require(isinstance(value["revisions"], dict) and bool(value["revisions"]), "Missing revision index")
            require(all(type(k) is int and k >= 0 and isinstance(v, str) and
                        re.fullmatch(r"[0-9a-f]{64}", v) for k, v in value["revisions"].items()), "Invalid revision index")
            require(value["current_revision"] == max(value["revisions"]), "Head/index mismatch")
            return value
        except InvalidCase as exc:
            raise StoreError(str(exc)) from exc

    def _snapshot(self, revision, expected_hash):
        path = self.root / "revisions" / f"{revision:06d}.yaml"
        value = read_yaml(path)
        if digest(path.read_bytes()) != expected_hash or value.get("revision") != revision:
            raise StoreError("Revision hash or identity mismatch")
        return Snapshot(value)

    def current(self):
        manifest = self._manifest()
        revision = manifest["current_revision"]
        return self._snapshot(revision, manifest["revisions"][revision])

    def history(self):
        manifest = self._manifest()
        return [self._snapshot(r, h) for r, h in sorted(manifest["revisions"].items())]

    def sources(self):
        result = {}
        for path in sorted((self.root / "inputs").glob("*.yaml")):
            value = read_wrapped(path)
            validate_input(value)
            require(path.stem == value["request_id"], "Input file identity mismatch")
            result[path.stem] = value
        for path in sorted((self.root / "sources").glob("*.yaml")):
            value = read_wrapped(path)
            shape(value, {"source_id", "name", "speaker", "content_base64", "sha256"},
                  {"source_id", "name", "speaker", "content_base64", "sha256"}, "source")
            require(path.stem == value["source_id"] and re.fullmatch(r"s[0-9a-f]{32}", path.stem), "Invalid source ID")
            try:
                content = base64.b64decode(value["content_base64"], validate=True)
            except (ValueError, TypeError) as exc:
                raise StoreError("Invalid source content") from exc
            require(digest(content) == value["sha256"], "Source hash mismatch")
            result[path.stem] = value
        return result

    def validate(self):
        try:
            history = self.history()
            sources = self.sources()
            validate_ancestry(history, sources)
            manifest = self._manifest()
            require(all(s.value["case_id"] == manifest["case_id"] for s in history), "Case identity mismatch")
            for source in sources.values():
                if "request_id" in source:
                    base = next((s for s in history if s.revision == source["base_revision"]), None)
                    require(base is not None and source["response_target"] == base.target, "Invalid input target")
            self.cursor()
            allocations = self._allocations()
            require(allocations["revision"] >= history[-1].revision and
                    all(allocations["counters"].get(k, 0) >= v for k, v in history[-1].value["counters"].items()),
                    "Allocation ledger precedes committed state")
            for path in (self.root / "attempts").glob("*.yaml"):
                require(PATH_PATTERN.fullmatch(path.relative_to(self.root).as_posix()), "Invalid attempt path")
                value = read_wrapped(path)
                require(value.get("request_id") in sources and type(value.get("attempt")) is int,
                        "Attempt has an unknown input")
        except (InvalidCase, TypeError, KeyError, AttributeError) as exc:
            raise StoreError("Invalid case schema or references") from exc

    def retain(self, value):
        self._editing()
        validate_input(value)
        path = self.root / "inputs" / f"{value['request_id']}.yaml"
        if path.exists():
            old = read_wrapped(path)
            # Time is not semantic identity. A repeated submit may have a new timestamp.
            if {k: v for k, v in old.items() if k != "timestamp"} != {k: v for k, v in value.items() if k != "timestamp"}:
                raise StoreError("Request identity is already bound to a different input")
            sync_file(path)
            try:
                sync_directory(path.parent)
            except OSError as exc:
                raise StoreError("Input durability is unconfirmed") from exc
            return
        atomic_write(path, wrapped(value), immutable=True)

    def input(self, request_id):
        if not isinstance(request_id, str) or not re.fullmatch(r"in\d{3,}", request_id):
            raise InvalidCase("Invalid request ID")
        value = read_wrapped(self.root / "inputs" / f"{request_id}.yaml")
        validate_input(value)
        return value

    def next_request_id(self):
        numbers = [int(p.stem[2:]) for p in (self.root / "inputs").glob("in*.yaml")]
        return f"in{max(numbers, default=0) + 1:06d}"

    def next_revision(self):
        # Orphans reserve IDs but are not part of published history.
        numbers = [int(p.stem) for p in (self.root / "revisions").glob("*.yaml") if p.stem.isdigit()]
        return max([self._allocations()["revision"]] + numbers) + 1

    def _allocations(self):
        from reason_commons.domain.model import PREFIXES
        value = read_wrapped(self.root / "allocations.yaml")
        shape(value, {"revision", "counters"}, {"revision", "counters"}, "allocation ledger")
        require(type(value["revision"]) is int and value["revision"] >= 0, "Invalid allocated revision")
        require(isinstance(value["counters"], dict) and set(value["counters"]) <= set(PREFIXES) and
                all(type(v) is int and v >= 0 for v in value["counters"].values()), "Invalid allocated IDs")
        return value

    def reserved_counters(self):
        counters = self._allocations()["counters"]
        for path in (self.root / "revisions").glob("*.yaml"):
            value = read_yaml(path)
            for key, count in value.get("counters", {}).items():
                if type(count) is int:
                    counters[key] = max(counters.get(key, 0), count)
        return counters

    def checkpoint(self, value):
        self._editing()
        atomic_write(self.root / "cursor.yaml", wrapped(value))

    def cursor(self):
        return read_wrapped(self.root / "cursor.yaml")

    def start_attempt(self, request_id):
        self._editing()
        self.input(request_id)
        sync_file(self.root / "inputs" / f"{request_id}.yaml")
        try:
            sync_directory(self.root / "inputs")
        except OSError as exc:
            raise StoreError("Input durability is unconfirmed") from exc
        attempts = self.attempts(request_id)
        number = max((a["attempt"] for a in attempts), default=0) + 1
        atomic_write(self.root / "attempts" / f"{request_id}-{number:03d}-start.yaml",
                     wrapped({"request_id": request_id, "attempt": number, "status": "started"}), immutable=True)
        return number

    def received(self, request_id, attempt, proposal, version):
        self._editing()
        atomic_write(self.root / "attempts" / f"{request_id}-{attempt:03d}-response.yaml",
                     wrapped({"request_id": request_id, "attempt": attempt, "proposal": proposal, "version": version}),
                     immutable=True)

    def pending_response(self, request_id):
        responses = []
        for path in sorted((self.root / "attempts").glob(f"{request_id}-*-response.yaml")):
            response = read_wrapped(path)
            results = list((self.root / "attempts").glob(f"{request_id}-{response['attempt']:03d}-result-*.yaml"))
            # An invalid response is preserved for audit, never automatically re-applied.
            if not any(read_wrapped(p).get("status") in {"rejected", "stale"} for p in results):
                responses.append(response)
        return responses[-1] if responses else None

    def receipt(self, request_id, attempt, value):
        self._editing()
        paths = list((self.root / "attempts").glob(f"{request_id}-{attempt:03d}-result-*.yaml"))
        sequence = max((int(p.stem.rsplit("-", 1)[1]) for p in paths), default=0) + 1
        value = deepcopy(value)
        value.update(request_id=request_id, attempt=attempt)
        atomic_write(self.root / "attempts" / f"{request_id}-{attempt:03d}-result-{sequence}.yaml",
                     wrapped(value), immutable=True)

    def attempts(self, request_id):
        def order(path):
            parts = path.stem.split("-")
            phase = {"start": 0, "response": 1, "result": 2}[parts[2]]
            return int(parts[1]), phase, int(parts[3]) if phase == 2 else 0
        return [read_wrapped(p) for p in sorted((self.root / "attempts").glob(f"{request_id}-*.yaml"), key=order)]

    def commit(self, snapshot, expected_revision):
        self._editing()
        manifest = self._manifest()
        if manifest["current_revision"] != expected_revision:
            raise StaleWork("Case advanced before publication")
        validate_ancestry(self.history() + [snapshot], self.sources())
        # Persist reservations before writing a candidate snapshot. Export/import
        # preserves these even when a crash leaves an unpublished candidate.
        atomic_write(self.root / "allocations.yaml", wrapped({"revision": snapshot.revision,
                     "counters": snapshot.value["counters"]}))
        content = encoded(snapshot.to_dict())
        atomic_write(self.root / "revisions" / f"{snapshot.revision:06d}.yaml", content, immutable=True)
        manifest["revisions"][snapshot.revision] = digest(content)
        manifest["current_revision"] = snapshot.revision
        atomic_write(self.root / "manifest.yaml", encoded(manifest))

    def add_source(self, name, content, speaker):
        self._editing()
        require(isinstance(content, bytes) and isinstance(name, str) and isinstance(speaker, str), "Invalid source")
        source_id = "s" + uuid.uuid4().hex
        atomic_write(self.root / "sources" / f"{source_id}.yaml", wrapped({"source_id": source_id,
                     "name": name, "speaker": speaker, "content_base64": base64.b64encode(content).decode("ascii"),
                     "sha256": digest(content)}), immutable=True)
        return source_id

    def confirm_durable(self):
        self._editing()
        manifest = self._manifest()
        sync_file(self.root / "revisions" / f"{manifest['current_revision']:06d}.yaml")
        sync_file(self.root / "manifest.yaml")
        sync_file(self.root / "allocations.yaml")
        try:
            sync_directory(self.root / "revisions")
            sync_directory(self.root)
        except OSError as exc:
            raise StoreError("Publication durability is unconfirmed") from exc

    def export(self, destination, cursor_override=None):
        self._editing()  # hold the writer lock across a consistent export
        self.validate()
        destination = Path(destination)
        if destination.suffix != ".reasoncase":
            raise StoreError("Portable exports use the .reasoncase extension")
        descriptor, temporary = tempfile.mkstemp(prefix=".export-", dir=destination.parent)
        try:
            os.close(descriptor)
            manifest = self._manifest()
            paths = [self.root / "manifest.yaml", self.root / "cursor.yaml", self.root / "allocations.yaml"]
            paths += [self.root / "revisions" / f"{r:06d}.yaml" for r in manifest["revisions"]]
            for directory in ("inputs", "attempts", "sources"):
                paths += sorted((self.root / directory).glob("*.yaml"))
            with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in paths:
                    name = path.relative_to(self.root).as_posix()
                    if name == "cursor.yaml" and cursor_override is not None:
                        archive.writestr(name, wrapped(cursor_override))
                    else:
                        archive.write(path, name)
            with open(temporary, "rb") as stream:
                os.fsync(stream.fileno())
            os.link(temporary, destination)  # do not clobber a handoff
            sync_directory(destination.parent)
        except OSError as exc:
            raise StoreError("Cannot publish portable export") from exc
        finally:
            os.unlink(temporary)

    @classmethod
    def import_bundle(cls, archive_path, destination):
        destination = Path(destination)
        if destination.exists():
            raise StoreError("Import destination already exists")
        try:
            with tempfile.TemporaryDirectory(prefix=".reason-import-", dir=destination.parent) as temporary:
                staging = Path(temporary)
                extract_bundle(archive_path, staging)
                staged = cls(staging, writable=False)  # all hashes/schema/references before publication
                staged.close()
                # mkdir reserves the destination; a concurrent importer cannot overwrite it.
                destination.mkdir(mode=0o700)
                try:
                    for path in staging.iterdir():
                        os.rename(path, destination / path.name)
                    sync_directory(destination)
                    sync_directory(destination.parent)
                except Exception:
                    shutil.rmtree(destination)
                    raise
            return cls(destination)
        except (OSError, zipfile.BadZipFile, InvalidCase, RuntimeError) as exc:
            raise StoreError("Bundle could not be validated or imported") from exc


def extract_bundle(archive_path, staging):
    """Validated temporary materialization shared by import and read-only inspection."""
    for directory in ("revisions", "inputs", "attempts", "sources"):
        (staging / directory).mkdir()
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        require(len(members) <= 10000 and sum(m.file_size for m in members) <= MAX_BUNDLE,
                "Bundle exceeds import limit")
        names = set()
        for member in members:
            require(PATH_PATTERN.fullmatch(member.filename) is not None and member.filename not in names,
                    "Unsupported or duplicate bundle path")
            require(member.file_size <= MAX_FILE and (member.external_attr >> 16) & 0o170000 != 0o120000,
                    "Oversized record or symlink")
            names.add(member.filename)
            atomic_write(staging / member.filename, archive.read(member), immutable=True)


class ArchiveCaseStore(FileCaseStore):
    """Read-only archive view; no editable case is imported and no lock is created."""

    def __init__(self, archive_path):
        self._temporary = tempfile.TemporaryDirectory(prefix="reason-inspect-")
        try:
            staging = Path(self._temporary.name)
            extract_bundle(archive_path, staging)
            super().__init__(staging, writable=False)
        except Exception as exc:
            self._temporary.cleanup()
            if isinstance(exc, (OSError, zipfile.BadZipFile, InvalidCase, RuntimeError)):
                raise StoreError("Bundle could not be validated for inspection") from exc
            raise

    def close(self):
        super().close()
        self._temporary.cleanup()
