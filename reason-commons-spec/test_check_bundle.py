"""Regression tests for delivery scope tooling; no application is exercised."""
import copy
import json
from pathlib import Path
import unittest

from check_bundle import (parse_scenarios, select_scenarios, validate_scope, validate_tui_frames,
                          validate_tui_ledger, validate_interface_language, validate_v1_decisions)

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
        event = 'EVENT semantic in006 r0008 question006'
        self.assertTrue(validate_tui_ledger(self.text.replace(event, ''), self.config))
        self.assertTrue(validate_tui_ledger(self.text.replace(event, event+'\n'+event), self.config))

    def test_local_decision_requires_exact_version(self):
        modified = self.text.replace('target=L3@1 dimension=belief', 'target=L3 dimension=belief')
        self.assertTrue(any('exact-version' in e for e in validate_tui_ledger(modified, self.config)))


class V1SessionChecks(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.text = (root / 'example-mvp-session.txt').read_text()
        self.config = json.loads((root / 'delivery-phases.json').read_text())['sessions']['example-mvp-session.txt']

    def test_current_v1_session(self):
        self.assertEqual(validate_tui_frames(self.text, 80), [])
        self.assertEqual(validate_tui_ledger(self.text, self.config), [])
        self.assertEqual(validate_v1_decisions(self.text), [])

    def test_accepting_proposals_is_a_v1_decision_but_a_stance_is_not(self):
        accept = 'dimension=membership value=accepted'
        self.assertIn(accept, self.text)
        stance = self.text.replace(accept, 'dimension=belief value=supported', 1)
        self.assertTrue(validate_v1_decisions(stance))

    def test_the_acceptance_setting_targets_the_case(self):
        setting = 'target=case dimension=acceptance'
        self.assertIn(setting, self.text)
        modified = self.text.replace(setting, 'target=G1@1 dimension=acceptance', 1)
        self.assertTrue(any('exact-version' in e for e in validate_tui_ledger(modified, self.config)))


class InterfaceContractChecks(unittest.TestCase):
    def test_retired_brand_and_stationery_terms_are_rejected(self):
        for text in ['Cardroom', 'Open card 17', 'Browse cards', 'case.cardcase']:
            with self.subTest(text=text):
                self.assertTrue(validate_interface_language(text))

    def test_parallel_command_ui_is_rejected(self):
        for text in ['Launch with --plain', 'Actions > Command',
                     'When Sam enters ":stance belief disputed"',
                     'Use `:connections [ID]` to inspect']:
            with self.subTest(text=text):
                self.assertTrue(validate_interface_language(text))

    def test_literal_editor_text_and_offline_utilities_are_permitted(self):
        self.assertEqual(validate_interface_language(
            'Type "5 ? q / :options" in Response; Enter adds a line. '
            'reason-commons inspect case.reasoncase --json'), [])

    def test_internal_intervention_schema_is_permitted(self):
        self.assertEqual(validate_interface_language('Internal `intervention` records store the response.'), [])

    def test_internal_unit_cannot_leak_into_a_frame(self):
        root = Path(__file__).parent
        text = (root / 'example-tui-session.txt').read_text()
        modified = text.replace('Define success', 'c001 / success', 1)
        self.assertTrue(any('leaked' in e for e in validate_tui_frames(modified, 120)))


class ReasoningDiagramChecks(unittest.TestCase):
    def test_resize_keeps_the_exact_joint_premises(self):
        from build_tui_specimens import joint_inference_diagram
        full = joint_inference_diagram()
        compact = joint_inference_diagram(compact=True)
        for premise in [
            'Validation is interrupted and must be repeated for this change.',
            'Net unrecovered recheck time exceeds slack before release cutoff.',
            'No eligible later release occurs before its three-day deadline.',
        ]:
            self.assertEqual(full.count(premise), 1)
            self.assertEqual(compact.count(premise), 1)
        self.assertIn('ALL / L3@1', full)
        self.assertIn('ALL / L3@1', compact)

    def test_joint_output_terminates_at_matching_boundary_ports(self):
        from build_tui_specimens import joint_inference_diagram
        for compact in [False, True]:
            rows = joint_inference_diagram(compact=compact).splitlines()
            arrow = next(i for i, row in enumerate(rows) if row.strip() == 'v')
            column = rows[arrow].index('v')
            self.assertEqual(rows[arrow-2][column], '+')
            self.assertEqual(rows[arrow-1][column], '|')
            self.assertEqual(rows[arrow+1][column], '+')
            # Every premise sits inside the same continuous ALL boundary.
            outer_width = len(rows[0])
            for row in rows[1:arrow-2]:
                self.assertEqual(len(row), outer_width)
                self.assertTrue(row.endswith('|'))


if __name__ == '__main__':
    unittest.main()
