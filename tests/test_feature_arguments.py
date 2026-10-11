"""The feature's authored argument maps exactly to proposed application records."""
from copy import deepcopy
from pathlib import Path

import pytest

from reason_commons.bootstrap import create_case
from scripts.feature_arguments import load_argument, bind_updates, validate_argument
from tests.support import ScriptedConsultant, proposal

FEATURE = Path(__file__).resolve().parents[1] / 'reason-commons-spec/features/15_contribution_feedback.feature'


def test_feedback_argument_is_complete_and_scenario_links_resolve():
    text = FEATURE.read_text()
    argument = load_argument(text)
    assert validate_argument(argument, text) == []
    assert set(argument['tree_context']) == {'goal', 'current_reality', 'conflict', 'future_reality',
                                             'prerequisite', 'transition'}
    assert argument['tree_context']['conflict'].startswith('Not established')
    assert argument['evidence_required']['frt_benefit'] == 'usability'


@pytest.mark.parametrize('fault', ['duplicate_id', 'missing_source', 'missing_link_end', 'missing_scenario_target',
                                  'automated_proves_benefit'])
def test_argument_checker_rejects_broken_correspondence_and_false_evidence(fault):
    text = FEATURE.read_text()
    argument = deepcopy(load_argument(text))
    if fault == 'duplicate_id':
        argument['updates'].append(deepcopy(argument['updates'][0]))
    elif fault == 'missing_source':
        argument['updates'][0]['source_refs'] = ['unknown_source']
    elif fault == 'missing_link_end':
        link = next(u for u in argument['updates'] if u['operation'] == 'record_link')
        link['data']['from_ref'] = 'missing_claim'
    elif fault == 'missing_scenario_target':
        text = text.replace('@implements_tt_receipt', '@implements_unknown_action')
    else:
        text = text.replace('@verifies_tt_receipt_effect', '@verifies_frt_benefit')
    assert validate_argument(argument, text), fault


def test_repeated_yaml_keys_cannot_silently_replace_a_tree_update():
    text = '# RC-ARGUMENT-BEGIN\n# schema_version: 1\n# schema_version: 2\n# RC-ARGUMENT-END\n'
    with pytest.raises(ValueError, match='Duplicate'):
        load_argument(text)


def test_repeated_readable_claim_cannot_change_its_meaning():
    text = FEATURE.read_text()
    original = 'participants correctly distinguish saved input, AI consultation, waiting proposals and changes to their model [DE frt_benefit]'
    assert text.count(original) == 2
    changed = text.replace(original, 'participants agree with every proposal [DE frt_benefit]', 1)
    with pytest.raises(ValueError, match='Repeated claim frt_benefit'):
        load_argument(changed)


def test_shared_claim_keeps_its_tree_and_declared_source_across_argument_rules():
    argument = load_argument(FEATURE.read_text())
    rows = {u['temporary_id']: u for u in argument['updates']}
    # The FRT benefit first appears in the Goal Rule; its role declares its tree.
    assert rows['frt_benefit']['data']['tree'] == 'future_reality'
    assert rows['crt_ude']['data']['basis'] == 'participant_report'
    assert rows['crt_ude']['source_refs'] == ['user_report']
    assert rows['crt_offline']['source_refs'] == ['editor']
    assert len(rows) == len(argument['updates']) == 30


def test_each_authored_update_becomes_one_pending_record_with_exact_sources(tmp_path):
    text = FEATURE.read_text()
    argument = load_argument(text)
    with create_case(tmp_path / 'commons', 'Contribution feedback', acceptance='review') as app:
        sources = {key: app.add_source(key + '.txt', value['text'].encode('utf-8'), value['speaker'])
                   for key, value in argument['sources'].items()}
        updates = bind_updates(argument, sources)

        def authored(request):
            response = proposal(request)
            response['proposed_updates'] = updates
            return response

        # Reopen through the normal composition boundary with an explicitly authored consultant.
    from reason_commons.bootstrap import open_case
    with open_case(tmp_path / 'commons', consultant=ScriptedConsultant([authored])) as app:
        result = app.submit(text, 'Codex', 0, None)
        assert result['status'] == 'saved'
        assert len(result['proposed']) == len(argument['updates'])
        refs = dict(zip((u['temporary_id'] for u in updates), result['proposed']))
        records = {r['ref']: r for r in app.inspect()['case']['records']}
        statuses = app.workspace()['membership']
        for update in updates:
            record = records[refs[update['temporary_id']]]
            assert record['kind'] == update['operation'].removeprefix('record_')
            expected = deepcopy(update['data'])
            for key in ('from_ref', 'to_ref'):
                if key in expected:
                    expected[key] = refs[expected[key]]
            assert record['data'] == expected
            assert record['source_refs'] == update['source_refs']
            assert statuses[record['ref']] == 'proposed'
        assert all(not t['claims'] for t in app.workspace()['trees'])
