"""Executable definitions for the nine p0 specification scenarios (S108 amended for tree records)."""

from copy import deepcopy
from pathlib import Path
import zipfile

from behave import given, when, then

from reason_commons.bootstrap import open_case
from tests.support import (ScriptedConsultant, cli_json, cursor, fixture_app, proposal,
                           retain, seed, submit)


def new_app(context):
    context.provider = ScriptedConsultant()
    context.app, context.faults = fixture_app(context.path, context.provider)
    context.apps.append(context.app)


@given("a saved case with a current question, attributed notes, a bounded test, and an answer draft")
def saved_with_draft(context):
    new_app(context)
    seed(context.app, context.provider)
    assert context.app.checkpoint(cursor(context.app))["status"] == "saved"
    context.before = context.app.inspect()


@when("the participant quits and resumes the same case in a new process")
def resume_process(context):
    context.calls = len(context.provider.calls)
    context.app.close()
    context.resumed = cli_json("inspect", context.path, "--json")


@then("the same reasoning revision, response target, view cursor, and draft are restored")
def restored_cursor(context):
    assert context.resumed == context.before


@then("the goal, notes, test, and last prediction are unchanged")
def unchanged_reasoning(context):
    assert context.resumed["case"]["records"] == context.before["case"]["records"]
    assert {r["kind"] for r in context.resumed["case"]["records"]} >= {"goal", "note", "test"}


@then("resumption makes no consultant call")
def no_resume_call(context):
    assert len(context.provider.calls) == context.calls


@given("committed revision 13")
def committed13(context):
    new_app(context)
    seed(context.app, context.provider, 13)
    context.before = context.app.inspect()["case"]
    context.before_bundle = Path(context.temporary.name) / "before.reasoncase"
    context.app.export(context.before_bundle)


@when("a valid semantic response is committed")
def commit_response(context):
    context.result = submit(context.app)


@then("a complete revision 14 is available with parent 13 and source input references")
def complete14(context):
    case = context.app.inspect()["case"]
    assert case["revision"] == 14 and case["parent"] == 13
    assert context.result["request_id"] in case["source_input_refs"]
    assert context.result["request_id"] in context.app.sources()["sources"]


@then("revision 13 remains byte-for-byte unchanged")
def bytes_unchanged(context):
    after = Path(context.temporary.name) / "after.reasoncase"
    context.app.export(after)
    with zipfile.ZipFile(context.before_bundle) as a, zipfile.ZipFile(after) as b:
        assert a.read("revisions/000013.yaml") == b.read("revisions/000013.yaml")


@then("the intervention and its supported goal, note, or test updates appear together")
def atomic_records(context):
    case = context.app.inspect()["case"]
    additions = case["records"][len(context.before["records"]):]
    assert {r["kind"] for r in additions} == {"note", "intervention"}
    assert all(context.result["request_id"] in r["source_refs"] for r in additions)


@then('"saved" is shown only after the local commit succeeds')
def saved_after_commit(context):
    assert context.result["status"] == "saved"
    assert cli_json("inspect", context.path, "--json")["case"] == context.app.inspect()["case"]


@given("a saved case containing interventions, sources, attributed notes, a goal, and a bounded test")
def saved_portable(context):
    new_app(context)
    source = context.app.add_source("pilot.csv", b"measure,value\ndelivery,80%\n", "Sam")
    from tests.support import bounded_case
    context.provider.responses.append(lambda request: bounded_case(request, source))
    assert submit(context.app)["status"] == "saved"
    context.before = context.app.inspect()
    context.sources = context.app.sources()
    context.history = context.app.history()


@when('Sam exports a ".reasoncase" bundle and imports it into a fresh process')
def export_import(context):
    context.calls = len(context.provider.calls)
    bundle = Path(context.temporary.name) / "handoff.reasoncase"
    context.app.export(bundle)
    context.imported_path = Path(context.temporary.name) / "imported"
    context.imported = cli_json("import", bundle, "--store", context.imported_path)


@then("stable identifiers and revision ancestry are preserved")
def portable_ancestry(context):
    assert context.imported == context.before
    assert cli_json("history", context.imported_path, "--json") == context.history


@then("all referenced source records and the original prediction can be inspected offline")
def inspect_sources(context):
    with open_case(context.imported_path, writable=False) as app:
        assert app.sources() == context.sources
        assert app.inspect()["case"]["records"] == context.before["case"]["records"]


@then("no hidden provider conversation is required")
def no_conversation(context):
    # A separate interpreter imports only portable files, with no consultant configured.
    assert cli_json("inspect", context.imported_path, "--json") == context.before


@then("the imported case opens without a consultant call")
def no_import_call(context):
    assert len(context.provider.calls) == context.calls


@given('Sam\'s input has been stored under request "in014"')
def input14(context):
    new_app(context)
    seed(context.app, context.provider)
    context.request_id = "in014"
    assert retain(context.app, "5\n:options", context.request_id)["status"] == "input_retained"
    context.before = context.app.inspect()
    context.provider.responses.append(TimeoutError("Provider timeout"))


@when("the consultant adapter times out")
def timeout(context):
    context.result = context.app.consult(context.request_id)


@then("the current question and committed reasoning revision remain unchanged")
def failed_unchanged(context):
    assert context.app.inspect() == context.before


@then('"Input retained; consultant unavailable" is displayed with a visible Retry retained input control')
def retry_control(context):
    assert context.result["message"] == "Input retained; consultant unavailable"
    assert "retry_retained_input" in context.result["recovery_actions"]
    assert context.app.sources()["sources"][context.request_id]["text"] == "5\n:options"


@when('Sam retries "in014" successfully')
def retry14(context):
    context.result = context.app.retry(context.request_id)
    assert context.result["status"] == "saved"
    assert context.app.retry(context.request_id)["already_applied"]


@then("the accepted response creates exactly one committed intervention and one revision")
def exactly_once(context):
    case = context.app.inspect()["case"]
    assert case["revision"] == context.before["case"]["revision"] + 1
    assert sum(r["kind"] == "intervention" and context.request_id in r["source_refs"] for r in case["records"]) == 1


@then("the failed attempt is preserved separately from reasoning revisions")
def failed_receipt(context):
    attempts = context.app.receipts(context.request_id)["attempts"]
    assert any(a.get("status") == "unavailable" for a in attempts)
    assert any(a.get("status") == "saved" for a in attempts)


@given("a stored semantic input and current revision 14")
def input_at14(context):
    new_app(context)
    seed(context.app, context.provider, 14)
    context.request_id = retain(context.app)["request_id"]
    context.before = context.app.inspect()


@when("the adapter returns an unknown goal reference or an ownership claim without cited explicit input")
def invalid_response(context):
    # Exercise both alternatives in isolation without accepting either proposal.
    for operation, data in [("record_test", {"statement": "test", "goal_ref": "G999@1", "scope": "pilot",
                                              "forecast": [{"measure": "delivery", "expected": "80%",
                                                            "scope": "pilot", "denominator": "deliveries"}]}),
                            ("record_action", {"statement": "Run pilot", "test_ref": "P1@1", "owner": "Sam"})]:
        def invalid(request, operation=operation, data=data):
            value = proposal(request)
            value["proposed_updates"].append({"operation": operation, "data": data,
                                              "source_refs": [request["input"]["request_id"]]})
            return value
        context.provider.responses.append(invalid)
        context.result = context.app.consult(context.request_id)
        assert context.result["status"] == "rejected"


@then("no intervention or case update is committed")
def rejected_atomic(context):
    assert context.app.inspect() == context.before


@then("the input and failure receipt remain available")
@then("the raw input and failure receipt remain available")
def rejection_retained(context):
    assert context.request_id in context.app.sources()["sources"]
    assert any(a.get("status") == "rejected" for a in context.app.receipts(context.request_id)["attempts"])


@then("a local recovery message explains the next available action")
def recovery(context):
    assert context.result["message"] and "reevaluate_current_revision" in context.result["recovery_actions"]


@given("the case store cannot complete a durable write")
def failing_store(context):
    new_app(context)
    context.faults.fail("retain")


@when("the participant submits an answer")
def submit_failed(context):
    context.result = submit(context.app, "Exact answer\n5")


@then('"not saved" is visible')
def not_saved(context):
    assert context.result["status"] == "not_saved" and "not saved" in context.result["message"]


@then("no consultant call begins if the raw input cannot first be retained")
def no_call_failed_write(context):
    assert context.provider.calls == []
    assert context.app.inspect()["case"]["revision"] == 0


@then("the text remains in the editor or memory while the process is open")
def in_memory(context):
    assert context.result["draft"] == context.app.unsaved_input["text"] == "Exact answer\n5"


@then("the participant can copy it or choose a writable export destination")
def copy_recovery(context):
    assert {"copy_text", "choose_writable_export"} <= set(context.result["recovery_actions"])


@given("an adapter request was based on revision 14")
def stale_base(context):
    input_at14(context)


@given("the case has advanced to revision 15")
def advanced15(context):
    assert submit(context.app)["status"] == "saved"
    context.advanced = context.app.inspect()


@when("that adapter response arrives")
def late_response(context):
    context.result = context.app.consult(context.request_id)


@then("it is not applied to revision 15")
def no_apply(context):
    assert context.result["status"] == "stale"
    assert context.app.inspect() == context.advanced


@then("the receipt offers a re-evaluation against the current revision")
def stale_receipt(context):
    assert "reevaluate_current_revision" in context.result["recovery_actions"]
    assert any(a.get("status") == "stale" for a in context.app.receipts(context.request_id)["attempts"])


@then("no last-write-wins merge is performed")
def no_merge(context):
    assert context.request_id not in context.app.inspect()["case"]["applied_requests"]


@given("the store uses YAML revisions and content hashes")
def yaml_store(context):
    new_app(context)


@when("Sam opens storage help")
def storage_help(context):
    context.help = context.app.storage_help()


@then("it explains that the app never overwrites committed revisions")
def immutable_help(context):
    assert "never overwrites" in context.help and "application policy" in context.help


@then("it does not claim protection from an owner editing files outside the app")
def owner_help(context):
    assert "An owner can edit files outside the app" in context.help
    assert "not tamper-proof" in context.help


@given("the v1 schema allows only goal, note, intervention, test, action, observation, bounded review, and typed tree claim, link and retraction records")
def v1_case(context):
    new_app(context)
    seed(context.app, context.provider)
    context.request_id = retain(context.app)["request_id"]
    context.before = context.app.inspect()


@when("an adapter proposal includes an untyped relationship graph or structured stance update")
def later_fields(context):
    for kind in ("relationship", "stance"):
        def invalid(request, kind=kind):
            value = proposal(request)
            value["proposed_updates"].append({"operation": "record_" + kind, "data": {},
                                              "source_refs": [request["input"]["request_id"]]})
            return value
        context.provider.responses.append(invalid)
        context.result = context.app.consult(context.request_id)
        assert context.result["status"] == "rejected"


@then("the entire proposal is rejected before commit")
def entire_rejected(context):
    assert context.result["status"] == "rejected" and context.app.inspect() == context.before


@then("later fields are not silently stored or partially applied")
def no_later(context):
    assert context.app.history()["revisions"][-1] == context.before["case"]
    assert {r["kind"] for r in context.app.inspect()["case"]["records"]} <= {"note", "goal", "test", "intervention"}
