"""Observable workflow traces and effects, separate from application BDD."""

from reason_commons.adapters.skills import RetainedContributionWorkflow
from reason_commons.application.ports import CaseCapabilities
from tests.support import ScriptedConsultant, fixture_app


class RecordingCapabilities:
    def __init__(self, app):
        self.app = app
        self.trace = []

    def __getattr__(self, name):
        assert name in CaseCapabilities.__dict__ and not name.startswith("_"), "Forbidden capability"

        def call(*args, **kwargs):
            self.trace.append((name, args, kwargs))
            return getattr(self.app, name)(*args, **kwargs)
        return call


def test_workflow_consults_only_after_retention_and_records_attributed_effects(tmp_path):
    provider = ScriptedConsultant()
    app, _ = fixture_app(tmp_path / "case", provider)
    with app:
        recording = RecordingCapabilities(app)
        result = RetainedContributionWorkflow(recording).contribute("5\n:options", "Sam")
        assert [name for name, _, _ in recording.trace] == ["inspect", "retain_input", "consult"]
        assert result["status"] == "saved"
        retained = app.sources()["sources"][result["request_id"]]
        assert retained["text"] == "5\n:options" and retained["speaker"] == "Sam"
        assert app.inspect()["case"]["applied_requests"] == [result["request_id"]]


def test_workflow_stops_after_failed_retention(tmp_path):
    provider = ScriptedConsultant()
    app, faults = fixture_app(tmp_path / "case", provider)
    with app:
        faults.fail("retain")
        recording = RecordingCapabilities(app)
        result = RetainedContributionWorkflow(recording).contribute("A literal answer", "Sam")
        assert result["status"] == "not_saved"
        assert [name for name, _, _ in recording.trace] == ["inspect", "retain_input"]
        assert provider.calls == []


def test_workflow_does_not_automatically_repeat_failed_provider_work(tmp_path):
    provider = ScriptedConsultant([TimeoutError()])
    app, _ = fixture_app(tmp_path / "case", provider)
    with app:
        recording = RecordingCapabilities(app)
        workflow = RetainedContributionWorkflow(recording)
        result = workflow.contribute("original answer", "Sam")
        assert result["status"] == "unavailable" and len(provider.calls) == 1
        request_id = result["request_id"]
        assert workflow.retry_retained(request_id)["status"] == "saved"
        assert recording.trace[-1][0:2] == ("retry", (request_id,))
        assert provider.calls[0]["input"] == provider.calls[1]["input"]


def test_skill_surface_supports_local_sources_inspection_and_handoff(tmp_path):
    from reason_commons.bootstrap import import_case
    app, _ = fixture_app(tmp_path / "case", ScriptedConsultant())
    with app:
        capabilities = RecordingCapabilities(app)
        source = capabilities.add_source("observations.csv", b"measure,value\ndelivery,80%\n", "Sam")
        assert capabilities.sources()["sources"][source]["speaker"] == "Sam"
        result = RetainedContributionWorkflow(capabilities).contribute("Inspect this supplied report", "Sam")
        assert capabilities.receipts(result["request_id"])["attempts"]
        assert capabilities.history() == app.history()
        assert capabilities.storage_help() == app.storage_help()
        bundle = tmp_path / "handoff.reasoncase"
        capabilities.export(bundle)
        with import_case(bundle, tmp_path / "handoff") as imported:
            assert imported.inspect() == capabilities.inspect()
            assert imported.sources() == capabilities.sources()
        assert "add_source" in [name for name, _, _ in capabilities.trace]
        assert "export" in [name for name, _, _ in capabilities.trace]


def test_local_submission_and_skill_submission_have_identical_semantic_outcomes(tmp_path):
    from reason_commons.bootstrap import create_case
    from tests.support import bounded_case

    class FixedClock:
        def now(self):
            return "2026-10-02T08:00:00+00:00"

    with create_case(tmp_path / "local", "Parity", ScriptedConsultant([bounded_case]), clock=FixedClock()) as local:
        with create_case(tmp_path / "skill", "Parity", ScriptedConsultant([bounded_case]), clock=FixedClock()) as agent:
            capabilities = RecordingCapabilities(agent)
            local_result = local.submit("An attributed pilot forecast", "Sam", 0, None)
            skill_result = capabilities.submit("An attributed pilot forecast", "Sam", 0, None)
            assert local_result == skill_result
            local_case, skill_case = local.inspect()["case"], capabilities.inspect()["case"]
            # Independent cases have independent identities; their semantic results match.
            local_case.pop("case_id")
            skill_case.pop("case_id")
            assert local_case == skill_case
            assert local.sources() == capabilities.sources()
            assert local.retry(local_result["request_id"]) == capabilities.retry(skill_result["request_id"])

