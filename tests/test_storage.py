import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest
import yaml

from reason_commons.adapters import filesystem
from reason_commons.application.ports import StoreError, WriterBusy
from reason_commons.bootstrap import create_case, import_case, open_case
from tests.support import ROOT, ScriptedConsultant, cli, cursor, fixture_app, retain, seed, submit


@pytest.fixture
def session(tmp_path):
    provider = ScriptedConsultant()
    app, faults = fixture_app(tmp_path / "case", provider)
    yield app, faults, provider
    app.close()


def test_only_one_writer_but_offline_reader_can_inspect(session, tmp_path):
    app, _, provider = session
    seed(app, provider)
    with pytest.raises(WriterBusy):
        open_case(tmp_path / "case")
    with open_case(tmp_path / "case", writable=False) as reader:
        assert reader.inspect() == app.inspect()
        with pytest.raises(StoreError):
            reader.export(tmp_path / "readonly.reasoncase")
    result = cli("export", tmp_path / "case", tmp_path / "busy.reasoncase")
    assert result.returncode == 1 and "Another process" in result.stderr


def test_lock_released_on_process_death(tmp_path):
    path = tmp_path / "case"
    with create_case(path):
        pass
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    script = "from reason_commons.bootstrap import open_case; import os,sys; a=open_case(sys.argv[1]); os._exit(19)"
    result = subprocess.run([sys.executable, "-c", script, str(path)], env=env, timeout=15)
    assert result.returncode == 19
    with open_case(path) as app:
        assert app.inspect()["case"]["revision"] == 0


def test_provider_timeout_survives_restart_and_retry_is_idempotent(session, tmp_path):
    app, _, provider = session
    seed(app, provider)
    provider.responses.append(TimeoutError("do not retain provider secrets"))
    result = submit(app, "5\n:options")
    request_id = result["request_id"]
    before = app.inspect()["case"]
    app.close()
    with open_case(tmp_path / "case", consultant=provider) as resumed:
        assert resumed.inspect()["case"] == before
        assert resumed.retry(request_id)["status"] == "saved"
        calls = len(provider.calls)
        assert resumed.retry(request_id)["already_applied"]
        assert len(provider.calls) == calls
        assert resumed.sources()["sources"][request_id]["text"] == "5\n:options"
        assert "do not retain provider secrets" not in str(resumed.receipts(request_id))


@pytest.mark.parametrize("failure_path", ["revisions/000002.yaml", "manifest.yaml"])
def test_interrupted_publication_recovers_retained_response_without_provider_call(session, tmp_path, monkeypatch, failure_path):
    app, _, provider = session
    seed(app, provider)
    original = filesystem.atomic_write
    before = app.inspect()["case"]
    previous_bytes = (tmp_path / "case/revisions/000001.yaml").read_bytes()

    def fail(path, content, immutable=False):
        if str(path).endswith(failure_path):
            raise StoreError("Interrupted durable write")
        return original(path, content, immutable)

    monkeypatch.setattr(filesystem, "atomic_write", fail)
    result = submit(app)
    assert result["status"] == "not_saved"
    assert app.inspect()["case"] == before
    calls = len(provider.calls)
    app.close()
    monkeypatch.setattr(filesystem, "atomic_write", original)
    with open_case(tmp_path / "case", consultant=provider) as resumed:
        assert resumed.inspect()["case"] == before
        assert resumed.retry(result["request_id"])["status"] == "saved"
        assert len(provider.calls) == calls
        assert resumed.retry(result["request_id"])["already_applied"]
        after = resumed.inspect()["case"]
        assert after["parent"] == 1
        # An orphan reserves revision/object IDs and is never mistaken for a commit.
        if failure_path == "manifest.yaml":
            assert after["revision"] == 3
            assert after["current_intervention"] == "I3@1"
            assert [r["revision"] for r in resumed.history()["revisions"]] == [0, 1, 3]
    assert (tmp_path / "case/revisions/000001.yaml").read_bytes() == previous_bytes


def test_receipt_failure_after_commit_cannot_cause_duplicate_application(session, tmp_path):
    app, faults, provider = session
    seed(app, provider)
    faults.fail("receipt")
    result = submit(app)
    assert result["status"] == "saved" and result["receipt_pending"]
    calls = len(provider.calls)
    app.close()
    with open_case(tmp_path / "case", consultant=provider) as resumed:
        assert resumed.retry(result["request_id"])["already_applied"]
        assert resumed.inspect()["case"]["revision"] == 2
        assert len(provider.calls) == calls


def test_crash_immediately_after_manifest_publication(tmp_path):
    script = """
import os, sys
from tests.support import fixture_app, ScriptedConsultant, submit
app, faults = fixture_app(sys.argv[1], ScriptedConsultant())
def crash(*args, **kwargs):
    os._exit(23)
faults.store.receipt = crash
submit(app)
"""
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT))
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path / "case")], env=env, timeout=15)
    assert result.returncode == 23
    provider = ScriptedConsultant()
    with open_case(tmp_path / "case", consultant=provider) as app:
        assert app.inspect()["case"]["revision"] == 1
        assert app.retry("in000001")["already_applied"]
        assert provider.calls == []


def test_fsync_failure_after_rename_requires_durability_confirmation_before_saved(session, tmp_path, monkeypatch):
    app, _, provider = session
    original = filesystem.sync_directory

    def fail(path):
        manifest = tmp_path / "case/manifest.yaml"
        if path == tmp_path / "case" and yaml.safe_load(manifest.read_bytes())["current_revision"] == 1:
            raise OSError("Injected directory flush failure")
        return original(path)

    monkeypatch.setattr(filesystem, "sync_directory", fail)
    result = submit(app)
    assert result["status"] == "not_saved"
    assert app.inspect()["case"]["revision"] == 1  # visible, but unconfirmed publication
    assert app.retry(result["request_id"])["status"] == "not_saved"
    assert len(provider.calls) == 1
    monkeypatch.setattr(filesystem, "sync_directory", original)
    assert app.retry(result["request_id"])["status"] == "saved"
    assert len(provider.calls) == 1


def test_unconfirmed_input_never_starts_provider_work(session, tmp_path, monkeypatch):
    app, _, provider = session
    original = filesystem.sync_directory

    def fail(path):
        if path == tmp_path / "case/inputs":
            raise OSError("Injected input-directory flush failure")
        return original(path)

    monkeypatch.setattr(filesystem, "sync_directory", fail)
    result = submit(app, "Unconfirmed answer")
    assert result["status"] == "not_saved" and provider.calls == []
    # The file can be visible after link even though the application reported a failure.
    assert app.retry(result["request_id"])["status"] == "not_saved"
    assert provider.calls == []
    monkeypatch.setattr(filesystem, "sync_directory", original)
    assert app.retry(result["request_id"])["status"] == "saved"
    assert len(provider.calls) == 1


def test_stale_response_after_provider_started_is_rejected(session):
    app, _, provider = session
    seed(app, provider)
    before_calls = len(provider.calls)
    from tests.support import proposal

    def delayed(request):
        assert submit(app, "A newer contribution")["status"] == "saved"
        return proposal(request)

    provider.responses.append(delayed)
    result = submit(app, "The delayed contribution")
    assert result["status"] == "stale"
    assert len(provider.calls) == before_calls + 2
    assert app.inspect()["case"]["revision"] == 2
    assert result["request_id"] not in app.inspect()["case"]["applied_requests"]


def test_failed_retention_keeps_literal_input_without_call(session):
    app, faults, provider = session
    faults.fail("retain")
    result = submit(app, "5 ? q / :options\nsecond line")
    assert result["status"] == "not_saved"
    assert provider.calls == []
    assert app.unsaved_input["text"] == "5 ? q / :options\nsecond line"
    assert app.sources()["sources"] == {}


def test_failed_input_can_be_exported_to_a_writable_destination(session, tmp_path):
    app, faults, provider = session
    faults.fail("retain")
    assert submit(app, "Unretained\nanswer")["status"] == "not_saved"
    bundle = tmp_path / "recovery.reasoncase"
    app.export(bundle)
    with import_case(bundle, tmp_path / "recovered") as recovered:
        assert recovered.inspect()["cursor"]["draft"] == "Unretained\nanswer"
        assert recovered.inspect()["cursor"]["speaker"] == "Sam"
        assert recovered.inspect()["cursor"]["save_status"] == "input_not_retained"
        assert recovered.inspect()["case"]["revision"] == 0
        assert recovered.sources()["sources"] == {}
    assert provider.calls == []


def test_allocated_ids_survive_export_of_an_unpublished_response(session, tmp_path, monkeypatch):
    app, _, provider = session
    seed(app, provider)
    original = filesystem.atomic_write

    def fail(path, content, immutable=False):
        if path.name == "manifest.yaml":
            raise StoreError("Interrupted publication")
        return original(path, content, immutable)

    monkeypatch.setattr(filesystem, "atomic_write", fail)
    result = submit(app)
    assert result["status"] == "not_saved"
    monkeypatch.setattr(filesystem, "atomic_write", original)
    bundle = tmp_path / "pending.reasoncase"
    app.export(bundle)
    calls = len(provider.calls)
    with import_case(bundle, tmp_path / "imported", consultant=provider) as recovered:
        assert recovered.retry(result["request_id"])["status"] == "saved"
        assert len(provider.calls) == calls
        case = recovered.inspect()["case"]
        assert case["revision"] == 3 and case["current_intervention"] == "I3@1"


def test_archive_view_cannot_edit_or_create_a_writer_lock(session, tmp_path):
    app, _, _ = session
    bundle = tmp_path / "view.reasoncase"
    app.export(bundle)
    with open_case(bundle, writable=False) as view:
        assert not (view._store.root / "writer.lock").exists()
        with pytest.raises(StoreError):
            view.add_source("file", b"contents", "Sam")
    with pytest.raises(StoreError, match="read-only"):
        open_case(bundle)


def test_same_request_id_cannot_be_rebound(session):
    app, _, provider = session
    assert retain(app, "original", "in014")["status"] == "input_retained"
    assert retain(app, "changed", "in014")["status"] == "not_saved"
    assert app.consult("in014")["status"] == "saved"
    assert provider.calls[0]["input"]["text"] == "original"


def test_checkpoint_does_not_change_reasoning_and_failed_checkpoint_keeps_draft(session):
    app, faults, provider = session
    seed(app, provider)
    before = app.inspect()["case"]
    assert app.checkpoint(cursor(app))["status"] == "saved"
    assert app.inspect()["case"] == before
    faults.fail("checkpoint")
    assert app.checkpoint(cursor(app, "new\ndraft"))["status"] == "not_saved"
    assert app.unsaved_input["draft"] == "new\ndraft"
    assert app.inspect()["cursor"]["draft"] == "5 requests?\n:options"


def test_owner_edit_is_detected_by_hash(session, tmp_path):
    app, _, provider = session
    seed(app, provider)
    app.close()
    path = tmp_path / "case/revisions/000001.yaml"
    path.write_bytes(path.read_bytes().replace(b"80%", b"99%"))
    with pytest.raises(StoreError, match="hash"):
        open_case(tmp_path / "case")


def mutate_archive(source, target, transform):
    with zipfile.ZipFile(source) as incoming, zipfile.ZipFile(target, "w") as outgoing:
        for item in incoming.infolist():
            name, content = transform(item.filename, incoming.read(item))
            if name is not None:
                outgoing.writestr(name, content)


@pytest.mark.parametrize("mutation", ["hash", "missing_source", "profile", "traversal", "duplicates"])
def test_import_rejects_corrupt_unsupported_or_unsafe_archives(session, tmp_path, mutation):
    app, _, provider = session
    seed(app, provider)
    bundle = tmp_path / "case.reasoncase"
    bad = tmp_path / "bad.reasoncase"
    app.export(bundle)

    def transform(name, data):
        if mutation == "hash" and name == "revisions/000001.yaml":
            data = data.replace(b"80%", b"99%")
        if mutation == "missing_source" and name.startswith("inputs/"):
            return None, None
        if mutation == "profile" and name == "manifest.yaml":
            data = data.replace(b"p2", b"p5")
        if mutation == "traversal" and name == "cursor.yaml":
            name = "../escaped.yaml"
        return name, data

    mutate_archive(bundle, bad, transform)
    if mutation == "duplicates":
        with zipfile.ZipFile(bad, "a") as archive:
            with pytest.warns(UserWarning):
                archive.writestr("manifest.yaml", b"duplicate")
    with pytest.raises(StoreError):
        import_case(bad, tmp_path / "imported")
    assert not (tmp_path / "imported").exists()
    assert not (tmp_path / "escaped.yaml").exists()


def test_export_refuses_existing_bundle_and_import_refuses_existing_destination(session, tmp_path):
    app, _, _ = session
    bundle = tmp_path / "case.reasoncase"
    app.export(bundle)
    original = bundle.read_bytes()
    with pytest.raises(StoreError):
        app.export(bundle)
    assert bundle.read_bytes() == original
    with pytest.raises(StoreError):
        import_case(bundle, tmp_path / "case")


def test_offline_cli_outputs_one_json_object_and_preserves_inspected_archive(session, tmp_path):
    app, _, provider = session
    seed(app, provider)
    bundle = tmp_path / "case.reasoncase"
    app.export(bundle)
    original = bundle.read_bytes()
    for command in ("inspect", "history"):
        result = cli(command, bundle, "--json")
        assert result.returncode == 0 and result.stderr == ""
        assert json.loads(result.stdout)["schema_version"] == "1"
    assert bundle.read_bytes() == original
    assert cli("--help").returncode == cli("--version").returncode == 0
    assert cli("inspect", tmp_path / "missing", "--json").returncode == 1
