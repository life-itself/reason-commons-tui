"""The offline guide is an ordinary consultant: the application validates every proposal."""

from reason_commons.adapters.guided import GuidedConsultant
from reason_commons.bootstrap import create_case
from tests.support import ScriptedConsultant, proposal


ANSWERS = ["Run 5k under 30 minutes", "Today 34 min; by December", "No knee pain\n- Sleep 7h",
           "Intervals twice a week", "32 min within 3 weeks", "October 24", "",
           "Tuesday 7am intervals", "Ran 5k in 32:40; knees fine", "Close to forecast; keep and adjust"]


def answer(app, text):
    target = app.workspace()["target"]
    result = app.submit(text, "David", target["base_revision"], target["response_target"])
    assert result["status"] == "saved", result
    return app.workspace()


def test_guide_walks_the_complete_loop_and_records_literal_words(tmp_path):
    with create_case(tmp_path / "case", "Running", consultant=GuidedConsultant()) as app:
        steps = [answer(app, text)["question"]["data"]["decision"] for text in ANSWERS]
        case = app.inspect()["case"]
    assert steps == ["Clarify the goal", "Clarify the goal", "Choose a test", "Choose a test", "Choose a test",
                     "Choose a test", "Plan the next action", "Observe the result",
                     "Review against the forecast", "Choose a test"]
    records = {r["kind"]: r for r in case["records"] if r["kind"] != "intervention"}
    assert records["goal"]["data"] == {"statement": "Run 5k under 30 minutes", "measure": "Today 34 min; by December",
                                       "protections": ["No knee pain", "Sleep 7h"]}
    assert records["goal"]["source_refs"] == ["in000001", "in000002", "in000003"]
    test = records["test"]["data"]
    assert test["forecast"][0]["expected"] == "32 min within 3 weeks"
    assert test["review_date"] == "October 24" and test["stop_condition"] is None
    assert records["action"]["data"]["execution"] == "planned"
    assert records["observation"]["data"]["basis"] == "participant_report"
    assert records["review"]["data"]["observation_refs"] == [records["observation"]["ref"]]


def test_guide_reasks_required_steps_instead_of_inventing_content(tmp_path):
    with create_case(tmp_path / "case", "Empty", consultant=GuidedConsultant()) as app:
        workspace = answer(app, "  ")
        assert workspace["question"]["data"]["purpose"] == "guided:goal"
        assert not [r for r in app.inspect()["case"]["records"] if r["kind"] != "intervention"]


def test_guide_continues_after_another_consultant_without_misreading_its_question(tmp_path):
    with create_case(tmp_path / "case", "Switch", consultant=ScriptedConsultant([proposal])) as app:
        answer(app, "Something is off with my mornings")
    from reason_commons.bootstrap import open_case
    with open_case(tmp_path / "case", consultant=GuidedConsultant()) as app:
        workspace = answer(app, "I want calmer mornings")
        assert workspace["question"]["data"]["purpose"] == "guided:goal"
        notes = [r for r in app.inspect()["case"]["records"] if r["kind"] == "note"]
        assert notes[-1]["data"]["text"] == "I want calmer mornings"


def test_guide_keeps_advice_requests_as_notes(tmp_path):
    with create_case(tmp_path / "case", "Advice", consultant=GuidedConsultant()) as app:
        target = app.workspace()["target"]
        result = app.submit("What should I do?", "David", target["base_revision"], target["response_target"],
                            intent="direct_advice")
        assert result["status"] == "saved"
        assert "cannot give advice" in app.workspace()["question"]["data"]["primary_prompt"]


def test_guide_shows_the_change_while_it_is_being_forecast(tmp_path):
    with create_case(tmp_path / "case", "Running", consultant=GuidedConsultant()) as app:
        prompts = [answer(app, text)["question"]["data"]["primary_prompt"] for text in ANSWERS[:8]]
    # Not yet a record: the test is saved with its stop condition, so the questions before it quote the change.
    assert all(prompt.startswith('Your change: "Intervals twice a week" ') for prompt in prompts[3:6])
    assert "Your change" not in prompts[6] and "Your change" not in prompts[2]
