"""Regression tests for delivery scope tooling; no application is exercised."""
import copy
import json
from pathlib import Path
import unittest

from check_bundle import (parse_scenarios, select_scenarios, validate_scope,
                          validate_tui_frames, validate_tui_ledger)

VALID = '''@J01
Feature: Fixture
  @S01 @p0 @v1 @automated
  Scenario: Save
    Given a store
    When a record is saved
    Then it is durable
'''


class ScopeChecks(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((Path(__file__).parent / 'delivery-phases.json').read_text())
        self.scenarios = []
        for path in sorted((Path(__file__).parent / 'features').glob('*.feature')):
            parsed, errors = parse_scenarios(path.read_text(), path.name)
            self.assertEqual(errors, [])
            self.scenarios.extend(parsed)

    def test_current_manifest_and_release_boundary(self):
        self.assertEqual(validate_scope(self.scenarios, self.manifest), [])
        self.assertEqual({s['id'] for s in select_scenarios(self.scenarios, 'v1', self.manifest)},
                         {s['id'] for s in select_scenarios(self.scenarios, 'through-p2', self.manifest)})

    def test_missing_phase_is_rejected(self):
        _, errors = parse_scenarios(VALID.replace('@p0 ', ''), 'fixture')
        self.assertTrue(any('phase tag' in e for e in errors))

    def test_feature_scope_inheritance_is_rejected(self):
        _, errors = parse_scenarios(VALID.replace('@J01', '@J01 @v1 @p0'), 'fixture')
        self.assertTrue(any('scenario-local' in e for e in errors))

    def test_examples_cannot_change_delivery_scope(self):
        text = VALID.replace('Scenario: Save', 'Scenario Outline: Save').replace(
            'When a record is saved', 'When "<record>" is saved')
        text += '    @p3 @later\n    Examples:\n      | record |\n      | note   |\n'
        _, errors = parse_scenarios(text, 'fixture')
        self.assertTrue(any('scenario-local' in e for e in errors))

    def test_multiple_phases_or_evaluation_kinds_are_rejected(self):
        _, errors = parse_scenarios(VALID.replace('@p0', '@p0 @p1').replace(
            '@automated', '@automated @semantic'), 'fixture')
        self.assertTrue(any('phase tag' in e for e in errors))
        self.assertTrue(any('evaluation tag' in e for e in errors))

    def test_outline_expansion_and_column_validation(self):
        text = VALID.replace('Scenario: Save', 'Scenario Outline: Save').replace(
            'When a record is saved', 'When "<record>" is saved')
        text += '    Examples:\n      | record |\n      | goal   |\n      | test   |\n'
        scenarios, errors = parse_scenarios(text, 'fixture')
        self.assertEqual(errors, [])
        self.assertEqual(scenarios[0]['cases'], 2)
        _, errors = parse_scenarios(text.replace('| test   |', '| test | extra |'), 'fixture')
        self.assertTrue(any('unequal' in e for e in errors))

    def test_later_requirement_cannot_silently_join_v1(self):
        modified = copy.deepcopy(self.scenarios)
        target = next(s for s in modified if s['phase'] == 'p3')
        target['phase'], target['release'] = 'p2', 'v1'
        self.assertTrue(any('membership' in e for e in validate_scope(modified, self.manifest)))

    def test_phase_release_conflict_and_unknown_phase(self):
        modified = copy.deepcopy(self.scenarios)
        modified[0]['release'] = 'later'
        self.assertTrue(any('disagree' in e for e in validate_scope(modified, self.manifest)))
        modified[0]['phase'] = 'p99'
        self.assertTrue(any('unknown' in e for e in validate_scope(modified, self.manifest)))

    def test_invalid_dependency_is_rejected(self):
        modified = copy.deepcopy(self.manifest)
        modified['phases'][2]['requires'] = ['p5']
        self.assertTrue(any('preceding' in e for e in validate_scope(self.scenarios, modified)))

    def test_increment_and_cumulative_selection(self):
        new = select_scenarios(self.scenarios, 'p3', self.manifest)
        cumulative = select_scenarios(self.scenarios, 'through-p3', self.manifest)
        self.assertEqual({s['phase'] for s in new}, {'p3'})
        self.assertEqual({s['phase'] for s in cumulative}, {'p0', 'p1', 'p2', 'p3'})
        with self.assertRaises(ValueError):
            select_scenarios(self.scenarios, 'through-p99', self.manifest)

    def test_untagged_and_duplicate_identity_are_rejected(self):
        _, errors = parse_scenarios(VALID.replace('  @S01 @p0 @v1 @automated\n', ''), 'fixture')
        self.assertTrue(any('identity tag' in e for e in errors))
        modified = copy.deepcopy(self.scenarios)
        modified[1]['id'] = modified[0]['id']
        self.assertTrue(any('duplicate scenario' in e for e in validate_scope(modified, self.manifest)))


class TuiSpecimenChecks(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.text = (root / 'example-tui-session.txt').read_text()
        self.config = json.loads((root / 'delivery-phases.json').read_text())['sessions']['example-tui-session.txt']

    def test_current_frames_and_ledgers(self):
        self.assertEqual(validate_tui_frames(self.text, 120), [])
        self.assertEqual(validate_tui_ledger(self.text, self.config), [])

    def test_truncated_frame_is_rejected(self):
        lines = self.text.splitlines()
        row = next(i+1 for i, line in enumerate(lines) if line.startswith('SCREEN S05 '))
        lines[row+7] = lines[row+7][:-1]
        self.assertTrue(any('geometry' in e for e in validate_tui_frames('\n'.join(lines), 120)))

    def test_duplicate_screen_identity_is_rejected(self):
        modified = self.text.replace('SCREEN S06 120x40', 'SCREEN S05 120x40')
        self.assertTrue(any('duplicate' in e for e in validate_tui_frames(modified, 120)))

    def test_missing_and_duplicate_semantic_commits_are_rejected(self):
        event = 'EVENT semantic in006 r0008 c006'
        self.assertTrue(validate_tui_ledger(self.text.replace(event, ''), self.config))
        self.assertTrue(validate_tui_ledger(self.text.replace(event, event+'\n'+event), self.config))

    def test_local_decision_requires_exact_version(self):
        modified = self.text.replace('target=L3@1 dimension=belief', 'target=L3 dimension=belief')
        self.assertTrue(any('exact-version' in e for e in validate_tui_ledger(modified, self.config)))


if __name__ == '__main__':
    unittest.main()
