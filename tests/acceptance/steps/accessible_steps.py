"""Executable definitions for the accessible ordered presentation (S49).

The case is built through the application use cases; the presentation is driven with the keys a person
presses, and what it appends is read as a screen reader would receive it.
"""

import re

from behave import given, then, when

from reason_commons.adapters.accessible import AccessibleWorkspace
from reason_commons.bootstrap import create_case, open_case
from tests.acceptance.steps.question_steps import pilot_forecast
from tests.support import ScriptedConsultant


@given("the accessible ordered text presentation in a terminal {width:d} columns wide and {height:d} rows high")
def accessible(context, width, height):
    context.width, context.height = width, height
    pilot_forecast(context)  # the S121 pilot: forecasts, an action and the goal's safeguards
    from tests.acceptance.steps.question_steps import asking
    observations = [{"operation": "record_observation", "temporary_id": f"temp_o{i}", "data": {
        "test_ref": "P1@1", "measure": measure, "value": value, "basis": "participant_report"}}
        for i, (measure, value) in enumerate([("orders delivered on time", "40 of 50 (80%)"),
                                              ("urgent requests acknowledged within four hours", "18 of 20 (90%)")])]
    replies = context.replies + [("40 of 50 on time; 18 of 20 urgent requests acknowledged in time",
                                  asking("Review the pilot", "What do you make of this result?",
                                         "The forecast was written first.", updates=observations), None)]
    create_case(context.path, "Forge", acceptance="automatic", actor="Sam").close()
    builder = ScriptedConsultant([reply for _, reply, _ in replies])
    for words, _, declarations in replies:
        with open_case(context.path, consultant=builder) as app:
            target = app.workspace()["target"]
            assert app.submit(words, "Sam", target["base_revision"], target["response_target"],
                              declarations=declarations or {})["status"] == "saved"
    context.consultant = ScriptedConsultant()
    context.app = open_case(context.path, consultant=context.consultant)
    context.apps.append(context.app)
    context.output = []
    context.presentation = AccessibleWorkspace(context.app, "Sam", width, height, write=context.output.append)
    context.revision_before = context.app.inspect()["case"]["revision"]


def written(context, since=0):
    return "".join(context.output[since:])


def read_section(context, mark=0):
    """The section from ``mark`` in reading order: Page Down to its end, the paging lines left out."""
    while "Page Down: more" in " ".join(written(context, mark).splitlines()[-2:]):
        context.presentation.handle("pagedown")
    lines = [line for line in written(context, mark).splitlines() if not re.match(r"\s*Page \d+ of \d+\.", line)
             and line.strip() not in ("more.", "back.", "Page Up: back.")]
    return " ".join(" ".join(lines).split())


def press(context, *keys):
    for key in keys:
        context.presentation.handle(key)


@when("a test review is rendered")
def review_rendered(context):
    context.presentation.start()
    context.first = written(context)


@then("compact status shows save status and names the focused control")
def status_lines(context):
    lines = context.first.splitlines()
    status = " ".join(" ".join(lines[1:6]).split())
    assert status.startswith("Reason Commons | Forge | Sam (declared) | saved"), status
    assert "View: Next step | Focus: Response (editor)" in status
    mark = len(context.output)
    press(context, "tab")
    assert written(context, mark).startswith("Focus: Send, asks the consultant")


@then("the question shows its consequential goal and protected condition")
def goal_with_question(context):
    mark = len(context.output)
    context.presentation.show()  # the same view again, read to its end
    text = read_section(context, mark)
    assert "NEXT: Review the pilot" in text and "Question: What do you make of this result?" in text
    assert text.index("Goal: 90% of orders delivered on time") > text.index("Question:")
    assert "Protect: Overtime at most 20 hours per week" in text


@then("the Case context control exposes complete current context locally")
def case_context(context):
    mark = len(context.output)
    controls = [c.label for c in context.presentation.controls()]
    press(context, *["tab"] * ((controls.index("Case context") - context.presentation.focus) % len(controls)))
    press(context, "enter")
    text = read_section(context, mark)  # the whole context, a page at a time
    assert "== Case context (replaces the view above) ==" in text
    for words in (f"Saved at revision {context.revision_before}", "Goal G1@1: 90% of orders delivered on time",
                  "Horizon: October 30", "Protect: Overtime at most 20 hours per week",
                  "Test P1@1: Freeze each day's plan by 9:00 with two urgent slots", "Answering: What do you make"):
        assert words in text, (words, text)
    assert len(context.consultant.calls) == 0 and context.app.inspect()["case"]["revision"] == context.revision_before
    press(context, "escape")
    assert "Returned to Next step; your draft is kept." in " ".join(written(context).split())


@then("lines wrap without horizontal scrolling")
def no_wide_lines(context):
    lines = written(context).splitlines()
    assert lines and max(len(line) for line in lines) <= context.width, max(lines, key=len)


@then("additional content is explicitly paged")
def paged(context):
    sections = context.first.split("\n")
    assert len(sections) <= context.height, len(sections)  # one page, its heading and the paging line
    assert re.search(r"Page 1 of (\d+)\. Page Down: more\.", " ".join(context.first.split()))
    mark = len(context.output)
    press(context, "pagedown")
    assert re.search(r"Page 2 of \d+", written(context, mark))


@then('"NEXT", uncertainty, and control labels do not depend on color')
def no_colour(context):
    text = written(context)
    assert "\x1b[" not in text  # no colour or cursor codes at all
    plain = " ".join(text.split())
    assert "NEXT: Review the pilot" in plain and "Attention: BREACH." in plain and "Not known yet:" in plain
    assert "Send, asks the consultant" in plain and "Case context, local" in plain
