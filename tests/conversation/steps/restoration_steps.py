from pathlib import Path
from behave import given, when, then
from reason_commons.adapters.commons import build_commons
from reason_commons.adapters.guided import GuidedConsultant
from reason_commons.bootstrap import open_case


@given('the source-backed Reason Commons working baseline')
def baseline(context):
    context.app.close()
    context.path = Path(context.temporary.name) / 'commons'
    context.app = build_commons(context.path)


@when('I inspect the imported reasoning and its sources')
def inspect(context):
    context.imported = context.app.inspect()['case']
    context.imported_sources = context.app.sources()['sources']


@then('the six partial trees include the already implemented interface')
def trees(context):
    claims = [r for r in context.imported['records'] if r['kind'] == 'claim']
    assert len({r['data']['tree'] for r in claims}) == 6
    assert any('already built' in r['data']['statement'] for r in claims)
    assert any(s.get('speaker') == 'Human expert (name not supplied)' for s in context.imported_sources.values())


@then('the import has no fabricated prospective test or historical human approval')
def honest(context):
    assert not any(r['kind'] in {'test', 'action', 'observation', 'review'} for r in context.imported['records'])
    assert all(d['actor'] == 'RC reconstruction editor (AI)' for d in context.imported['decisions'])


@when('I contribute a development issue through the offline guide')
def contribute(context):
    context.app.close()
    context.app = open_case(context.path, consultant=GuidedConsultant())
    context.app.set_acceptance('review', 'David', context.app.inspect()['case']['revision'])
    context.literal = 'We need clearer attribution before deciding.\n:options\n?'
    context.result = context.app.submit(context.literal, 'David', **context.app.workspace()['target'])
    assert context.result['status'] == 'saved', context.result


@then('my literal contribution is proposed for review')
def proposed(context):
    case = context.app.inspect()['case']
    note = next(r for r in reversed(case['records']) if r['kind'] == 'note')
    assert note['data']['text'] == context.literal
    assert context.app.workspace()['membership'][note['ref']] == 'proposed'


@then('the current question still invites a contribution to Reason Commons')
def continuing(context):
    assert context.app.workspace()['question']['data']['purpose'] == 'continuation'
    assert not any(r['kind'] == 'test' for r in context.app.inspect()['case']['records'])


@when('I revisit the reconstructed development stages')
def stages(context):
    context.stages = []
    for snapshot in context.app.history()['revisions'][1:]:
        workspace = context.app.workspace(revision=snapshot['revision'])
        context.stages.append(workspace['question']['data']['decision'])


@then('manual use precedes the implemented interface and the import')
def order(context):
    assert context.stages.index('Use RC manually on RC') < context.stages.index('Build the minimal interface')
    assert context.stages.index('Build the minimal interface') < context.stages.index('Import and adopt prior reasoning')


@then('the adopted model retains the argument and has no dismissed proposals')
def adopted(context):
    value = context.app.workspace()
    assert sum(len(tree['claims']) for tree in value['trees']) >= 55
    assert not value['backlog']
    assert not any(s in {'rejected', 'undone'} for s in value['membership'].values())
    assert value['acceptance'] == 'automatic'


@given('the reconstructed development argument imported for review')
def unadopted(context):
    context.app.close()
    context.path = Path(context.temporary.name) / 'review-import'
    context.app = build_commons(context.path, acceptance='review', adopted=False)


@then('its reasoning waits in the backlog instead of appearing as adopted trees')
def waits(context):
    value = context.app.workspace()
    assert len(value['backlog']) > 100
    assert not any(tree['claims'] for tree in value['trees'])


@when('I accept the imported reasoning')
def accept(context):
    refs = [e['ref'] for e in context.app.workspace()['backlog'] if e['entry'] == 'proposal']
    result = context.app.accept(refs, 'David', context.app.inspect()['case']['revision'], confirmed=True)
    assert result['status'] == 'saved', result


@then('the complete development argument appears in the working model')
def complete(context):
    assert sum(len(tree['claims']) for tree in context.app.workspace()['trees']) >= 55
    assert not context.app.workspace()['backlog']


@when('I require acceptance and contribute an additional observation')
def reviewed_contribution(context):
    context.app.close()
    context.app = open_case(context.path, consultant=GuidedConsultant())
    assert context.app.set_acceptance('review', 'David', context.app.inspect()['case']['revision'])['status'] == 'saved'
    result = context.app.submit('The prior history is difficult to understand.', 'David', **context.app.workspace()['target'])
    assert result['status'] == 'saved', result
    context.waiting_note = next(r['ref'] for r in reversed(context.app.inspect()['case']['records']) if r['kind'] == 'note')


@then('the observation waits for my decision')
def waiting_observation(context):
    assert context.app.workspace()['membership'][context.waiting_note] == 'proposed'


@when('I choose automatic acceptance and contribute another observation')
def automatic_contribution(context):
    assert context.app.set_acceptance('automatic', 'David', context.app.inspect()['case']['revision'])['status'] == 'saved'
    result = context.app.submit('I can now follow the implemented interface injection.', 'David', **context.app.workspace()['target'])
    assert result['status'] == 'saved', result
    context.accepted_note = next(r['ref'] for r in reversed(context.app.inspect()['case']['records']) if r['kind'] == 'note')


@then('the new observation enters the model and the earlier one still waits')
def only_future(context):
    value = context.app.workspace()
    assert value['membership'][context.accepted_note] == 'accepted'
    assert value['membership'][context.waiting_note] == 'proposed'
