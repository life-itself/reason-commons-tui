"""A finished example loop, built through the application with the built-in guide.

The home screen offers it so a newcomer can look at a whole loop (goal, test with a
forecast, action, observation, review) before starting their own. The organiser
accepts what each reply proposes, as anyone would with Accept all, so History shows
those decisions too. The finished example also brings in the six trees of the
analysis the test comes from. She keeps her own goal: she rejects the file's goal,
with the links that need it, and accepts the rest. It is written to a throwaway
folder; the people and numbers are fictional.
"""

from functools import partial
from importlib.resources import as_file, files

from reason_commons.adapters.guided import GuidedConsultant
from reason_commons.adapters.ltp_trees import import_trees
from reason_commons.bootstrap import create_case, open_case

NAME = "Example: from open evening to first practice"
SPEAKER = "Mira (example)"
# One test from the Second Renaissance analysis in the reasoncommons guide: its
# Transition Tree's third action, "prototype one clear next step from a public event to
# a first practice". The organiser, numbers and dates are invented.
ANSWERS = [
    "Newcomers at our open evenings find a clear, no-pressure next step into a first practice "
    "session, so interest turns into sustained practice.",
    "Newcomers at a first practice within 3 weeks (sign-up sheet): now 2 of 30, "
    "aiming for 8 of 30 by 30 November.",
    "Nobody feels recruited or pressured\nOrganisers' hours stay as they are",
    "End each open evening with one clear invitation: the date of a first practice, what it asks "
    "of you, and that no is a fine answer.",
    "6 of 30 newcomers come to a first practice within 3 weeks",
    "Sunday, 9 November",
    "Stop if anyone tells us they felt pushed.",
    "Thursday 16 October: I give the invitation in the last ten minutes and hand out a card with "
    "the date and an easy way to say no.",
    "9 of 31 newcomers came to a first practice within 3 weeks (sign-up sheet). Nobody said they "
    "felt pushed; two said the card helped them decide. Organiser hours were the same.",
    "Keep it. I forecast 6 of 30 and got 9 of 31, and both safeguards held. "
    "Next I will test whether people come back for a second session.",
]


def accept_reply(app, result):
    if result["proposed"]:
        decided = app.accept(result["proposed"], SPEAKER, app.inspect()["case"]["revision"], confirmed=True)
        if decided["status"] != "saved":
            raise RuntimeError(f"Example could not be built: {decided.get('message', decided['status'])}")


def build_sample(path, answers=None, clock=None, view="tests", name=NAME, trees=None):
    """Create the example case at path (which must not exist) and return path.

    By default the whole loop is answered and the trees are brought in; screenshots
    pass fewer answers or a fixed clock.
    """
    create_case(path, name, clock=clock).close()
    with open_case(path, consultant=GuidedConsultant(), clock=clock) as app:
        for answer in ANSWERS if answers is None else answers:
            target = app.workspace()["target"]
            result = app.retain_input(answer, SPEAKER, target["base_revision"], target["response_target"])
            result = app.consult(result["request_id"])
            if result["status"] != "saved":
                raise RuntimeError(f"Example could not be built: {result['status']}")
            accept_reply(app, result)
    if answers is None if trees is None else trees:
        with as_file(files("reason_commons.adapters").joinpath("sample-trees.ltp.yaml")) as source:
            summary = import_trees(path, source, SPEAKER, open_case=partial(open_case, clock=clock))
        with open_case(path, clock=clock) as app:
            goals = [r for r in summary["proposed"] if r.startswith("G")]
            if goals:
                app.reject(goals, SPEAKER, app.inspect()["case"]["revision"], confirmed=True)
            waiting = app.workspace(view="backlog")["membership"]
            accept_reply(app, {"proposed": [r for r in summary["proposed"] if waiting[r] == "proposed"]})
    with open_case(path, clock=clock) as app:
        # Open on Tests, where the original forecast sits next to the reported result.
        target = app.workspace()["target"]
        app.checkpoint({"view": view, "focus": "browse", "draft": "", "caret": 0, "speaker": SPEAKER,
                        "response_target": target["response_target"], "base_revision": target["base_revision"]})
    return path
