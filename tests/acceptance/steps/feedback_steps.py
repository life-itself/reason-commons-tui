"""Submission feedback projects durable application results; markers are local UI state."""
from behave import given, when, then

from reason_commons.adapters.commons import build_commons
from reason_commons.adapters.guided import GuidedConsultant
from reason_commons.bootstrap import create_case
from tests.acceptance.workspace import Workspace
from tests.acceptance.steps.workspace_steps import choose_in_menu, menu_labels, remember, revision
from tests.support import ScriptedConsultant
from tests.test_trees import claim, with_updates


class CountingGuide(GuidedConsultant):
    def __init__(self):
        self.calls = []

    def propose(self, request):
        self.calls.append(request)
        return super().propose(request)


@given('the adopted RC import with the offline guide and automatic acceptance')
def offline_import(context):
    build_commons(context.path).close()
    context.consultant = CountingGuide()
    context.workspace = Workspace(context.path, context.consultant, speaker='Sam', provider='guided')
    context.workspaces.append(context.workspace)
    context.trees_before = context.workspace.case(lambda app: app.workspace()['trees'])
    remember(context)


def tree_fixture(context, acceptance):
    create_case(context.path, 'Import prior work', acceptance=acceptance, actor='Sam').close()
    context.consultant = ScriptedConsultant([with_updates(
        claim('burden', 'Re-entering prior reasoning takes attention'),
        claim('import', 'Try importing one plain-text conversation', tree='transition', role='transition_action'))])
    context.workspace = Workspace(context.path, context.consultant, speaker='Sam')
    context.workspaces.append(context.workspace)
    remember(context)


@given('a terminal commons accepting two tree proposals automatically')
def automatic(context):
    tree_fixture(context, 'automatic')


@given('a terminal commons holding two tree proposals for review')
def review(context):
    tree_fixture(context, 'review')


@when('the operator contributes a suggestion about importing conversations')
def contribute(context):
    context.words = 'Explore importing conversations without reconstructing them by hand.'
    context.workspace.read(lambda app: app.query_one('#editor').load_text(context.words))
    context.workspace.press('ctrl+s')
    sources = context.workspace.case(lambda app: app.sources()['sources'])
    assert any(s.get('text') == context.words and s.get('speaker') == 'Sam' for s in sources.values())
    assert len(context.consultant.calls) == context.calls_before + 1


def receipt(context):
    return context.workspace.read(lambda app: str(app.query_one('#receipt').render()))


@then('a lasting receipt names the offline guide and the accepted note')
def saved_note(context):
    text = receipt(context)
    assert 'Offline guide (no AI)' in text and '1 note accepted automatically' in text, text
    assert context.workspace.read(lambda app: app.query_one('#receipt').display)
    assert 'Last contribution saved' in context.workspace.screen_text()
    context.receipt_before = text
    assert len(context.workspace.case(lambda app: app.workspace()['reply']['records'])) == 1


@then('the receipt says the trees are unchanged and how to choose AI analysis')
def no_ai(context):
    text = receipt(context)
    assert 'Trees unchanged' in text and 'Ctrl+P' in text and 'AI analysis' in text, text
    assert context.workspace.case(lambda app: app.workspace()['trees']) == context.trees_before


@then('the same contribution receipt is reconstructed from the saved application state')
def recovered(context):
    assert receipt(context) == context.receipt_before
    assert len(context.consultant.calls) == context.calls_before + 1


@then('the lasting receipt reports automatic acceptance and the affected trees')
def accepted(context):
    text = receipt(context)
    assert '2 proposals accepted automatically' in text, text
    assert 'Current Reality' in text and 'Transition' in text and 'Trees updated' in text, text
    assert context.workspace.read(lambda app: app.view_name) == 'next'
    assert context.workspace.focused() == 'editor'


def marked_destinations(context):
    context.workspace.press('ctrl+p')
    labels = menu_labels(context)
    context.workspace.press('escape')
    return [label for label in labels if label.startswith('Tree:') and 'updated' in label]


@then('Trees and both affected tree destinations are marked updated')
def marked(context):
    prompts = context.workspace.read(lambda app: [str(o.prompt) for o in app.query_one('#views').options])
    assert any('Trees' in p and 'updated' in p and '●' in p for p in prompts), prompts
    labels = marked_destinations(context)
    assert len(labels) == 2 and any('Current Reality' in s for s in labels) and any('Transition' in s for s in labels), labels


@when('the operator opens one affected tree')
def open_one(context):
    remember(context)
    context.workspace.press('ctrl+p')
    choose_in_menu(context, 'Tree: Current Reality')


@then("only that tree's update marker clears without a consultation or revision")
def acknowledged(context):
    labels = marked_destinations(context)
    assert len(labels) == 1 and 'Transition' in labels[0], labels
    assert revision(context) == context.revision_before
    assert len(context.consultant.calls) == context.calls_before


@then('the lasting receipt reports two proposals waiting in Backlog and unchanged trees')
def pending(context):
    text = receipt(context)
    assert '2 proposals wait in Backlog' in text and 'Trees unchanged' in text, text
    assert not any(t['claims'] for t in context.workspace.case(lambda app: app.workspace()['trees']))


@then('no tree destination is marked updated')
def unmarked(context):
    assert not marked_destinations(context)


@when('the operator accepts the waiting proposals')
def adopt(context):
    context.workspace.tab_to('accept-all')
    context.workspace.press('enter')


@then('the receipt reflects acceptance and the affected trees are marked updated')
def accepted_after_review(context):
    text = receipt(context)
    assert '2 proposals in your model' in text and 'wait in Backlog' not in text, text
    assert 'Trees updated' in text, text
    marked(context)
