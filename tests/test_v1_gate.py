"""The release gate refuses a skipped identity or a lost/duplicated outline row."""
from copy import deepcopy
from behave.parser import parse_feature
import pytest
from scripts.check_v1 import verify_cases


def fixture():
    feature = parse_feature('''Feature: Gate fixture
  @S999 @p0 @v1 @automated
  Scenario Outline: Preserve <value>
    When I save <value>
    Then it remains
    Examples:
      | value |
      | first |
      | second |
''')
    cases = list(feature.walk_scenarios())
    report = [{"elements": [{"type": "scenario", "name": s.name, "tags": s.tags,
                              "status": "passed", "steps": [{"result": {"status": "passed"}}]}
                             for s in cases]}]
    return feature.scenarios, report


def test_all_expanded_rows_are_required():
    expected, report = fixture()
    assert verify_cases(expected, report) == (1, 2)
    for mutation in ("missing", "duplicated", "skipped", "undefined"):
        changed = deepcopy(report)
        rows = changed[0]["elements"]
        if mutation == "missing":
            rows.pop()
        elif mutation == "duplicated":
            rows[1] = deepcopy(rows[0])
        elif mutation == "skipped":
            rows[1]["status"] = "skipped"
        else:
            rows[1]["steps"][0]["result"]["status"] = "undefined"
        with pytest.raises(SystemExit, match="incomplete v1 acceptance coverage"):
            verify_cases(expected, changed)
