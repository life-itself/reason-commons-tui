"""A finished example loop, built through the application with the built-in guide.

The home screen offers it so a newcomer can look at a whole loop (goal, test with a
forecast, action, observation, review) before starting their own. It is written to a
throwaway folder; the people and numbers are fictional.
"""

from reason_commons.adapters.guided import GuidedConsultant
from reason_commons.bootstrap import create_case, open_case

NAME = "Example: in bed by 23:00"
SPEAKER = "Sam (example)"
ANSWERS = [
    "Be in bed by 23:00 more often, so I wake up rested.",
    "Nights in bed by 23:00, from my phone's sleep log. Now 1 of 7 last week. "
    "Goal: 4 of 7 by the end of October.",
    "Evenings with my partner\nMy morning run",
    "No screens after 22:15; the phone charges in the kitchen.",
    "4 of 7 nights in bed by 23:00 in the first week",
    "Sunday, 12 October",
    "Stop if I lie awake for more than an hour on three nights.",
    "Tonight at 22:15: put the phone on the kitchen charger and set a reminder.",
    "5 of 7 nights in bed by 23:00 (sleep log). Two nights I read until 23:30. "
    "Evenings with my partner felt calmer; I ran every morning as usual.",
    "Keep it. I forecast 4 of 7 and got 5 of 7, and both safeguards held. "
    "Next I will try the same on weekends.",
]


def build_sample(path):
    """Create the example case at path (which must not exist) and return path."""
    create_case(path, NAME).close()
    with open_case(path, consultant=GuidedConsultant()) as app:
        for answer in ANSWERS:
            target = app.workspace()["target"]
            result = app.retain_input(answer, SPEAKER, target["base_revision"], target["response_target"])
            result = app.consult(result["request_id"])
            if result["status"] != "saved":
                raise RuntimeError(f"Example could not be built: {result['status']}")
        # Open on Tests, where the original forecast sits next to the reported result.
        target = app.workspace()["target"]
        app.checkpoint({"view": "tests", "focus": "browse", "draft": "", "caret": 0, "speaker": SPEAKER,
                        "response_target": target["response_target"], "base_revision": target["base_revision"]})
    return path
