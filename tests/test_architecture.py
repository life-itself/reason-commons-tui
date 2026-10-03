"""Mechanical enforcement of inward dependencies, including future modules."""

import ast
import importlib.util
import inspect
import json
from pathlib import Path
import sysconfig

from reason_commons.application.ports import CaseCapabilities
from reason_commons.application.service import CaseApplication


def test_domain_and_application_do_not_depend_on_adapters_or_skills():
    root = Path(__file__).resolve().parents[1] / "src/reason_commons"
    rules = json.loads((root.parents[1] / ".workflow.json").read_text())["dependency_rules"]
    standard_library = Path(sysconfig.get_path("stdlib")).resolve()
    for layer, permitted in [("domain", {"domain"}), ("application", {"domain", "application"})]:
        for path in (root / layer).rglob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                modules = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    assert node.level == 0, f"Use explicit imports for auditable dependencies: {path}"
                    modules = [node.module or ""]
                for module in modules:
                    if module.startswith("reason_commons."):
                        dependency = module.split(".")[1]
                        assert dependency in permitted and dependency in (rules[layer] + [layer]), f"Outward dependency in {path}: {module}"
                    else:
                        spec = importlib.util.find_spec(module.split(".")[0])
                        assert spec is not None, f"Unknown dependency in {path}: {module}"
                        origin = spec.origin or "built-in"
                        assert origin in {"built-in", "frozen"} or (
                            Path(origin).resolve().is_relative_to(standard_library) and
                            "site-packages" not in Path(origin).parts
                        ), f"Nonstandard dependency in {path}: {module}"


def test_every_semantic_application_use_case_is_on_the_skill_surface():
    """Adding a UI-only semantic use case fails until its capability is published."""
    root = Path(__file__).resolve().parents[1]
    guarantee = json.loads((root / ".workflow.json").read_text())["interface_guarantees"]["semantic_parity"]
    exemptions = set(guarantee["presentation_only_use_cases"] + guarantee["session_lifecycle"])
    assert exemptions == {"checkpoint", "close"}

    def methods(cls):
        return {name: method for name, method in vars(cls).items()
                if not name.startswith("_") and inspect.isfunction(method)}

    application, capabilities = methods(CaseApplication), methods(CaseCapabilities)
    assert set(application) - exemptions == set(capabilities), "Publish semantic use cases to CaseCapabilities"
    for name, capability in capabilities.items():
        # Protocols and concrete use cases must accept the same arguments/defaults.
        def arguments(method):
            return [(p.name, p.kind, p.default) for p in inspect.signature(method).parameters.values()]
        assert arguments(application[name]) == arguments(capability), f"Capability signature differs: {name}"
