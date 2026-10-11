"""Accepted-v1 inventory: application fixtures and real keyboard interaction."""
from pathlib import Path
from behave import given, when, then

from reason_commons.adapters.commons import build_commons, continue_commons
from reason_commons.adapters.guided import GuidedConsultant
from reason_commons.adapters.settings import Settings
from reason_commons.bootstrap import create_case, open_case
from tests.acceptance.workspace import Workspace
from tests.acceptance.steps.workspace_steps import choose_in_list, choose_in_menu, remember, revision, draft, menu_labels
from tests.support import ScriptedConsultant


@given('the adopted RC import in the terminal workspace')
def imported(context):
    build_commons(context.path).close()
    settings = Settings.load()
    settings.save()
    context.consultant = ScriptedConsultant()
    context.workspace = Workspace(context.path, context.consultant, speaker='Sam', settings=settings)
    context.workspaces.append(context.workspace)
    remember(context)


@then('the sidebar omits the empty supporting view "{view}"')
def omitted(context, view):
    ids = context.workspace.read(lambda app: [o.id for o in app.query_one('#views').options])
    assert view not in ids, ids


@when('the operator chooses "{label}" through Commands')
def command(context, label):
    context.workspace.press('ctrl+p')
    assert any(label in entry for entry in menu_labels(context)), f'missing Commands entry: {label}'
    choose_in_menu(context, label)


@then('the supporting view "{view}" opens locally with the live target unchanged')
def local_view(context, view):
    assert context.workspace.read(lambda app: app.view_name) == view
    unchanged(context)
    assert context.workspace.read(lambda app: app.workspace_value['target']) == context.target_before


@when('the workspace is closed and reopened')
def reopen(context):
    context.theme_before = context.workspace.read(lambda app: app.theme)
    context.workspace.press('ctrl+q')
    context.workspace.close()
    context.workspace = Workspace(context.path, context.consultant, speaker='Sam', settings=Settings.load())
    context.workspaces.append(context.workspace)


@then('expanded density is retained without a revision or consultant call')
def expanded(context):
    assert context.workspace.read(lambda app: app.density) == 'expanded'
    unchanged(context)


def settings_row(context, label):
    context.workspace.press('f2')
    # Arrow keys choose the row; Enter is deliberately not used to change it.
    w = context.workspace
    w.tab_to('settings-rows')
    labels = w.read(lambda app: [str(o.prompt) for o in app.screen.query_one('#settings-rows').options])
    target = next(i for i, text in enumerate(labels) if label in text)
    current = w.read(lambda app: app.screen.query_one('#settings-rows').highlighted) or 0
    w.press(*(['down'] * (target-current) if target >= current else ['up'] * (current-target)))


@when('the operator changes Reasoning to Require acceptance using Settings')
def review_policy(context):
    settings_row(context, 'Reasoning')
    context.workspace.press('right', 'escape')


@then("the application records the operator's review policy without consulting")
def policy(context):
    value = context.workspace.case(lambda app: app.inspect()['case'])
    assert context.workspace.case(lambda app: app.workspace()['acceptance']) == 'review'
    assert value['revision'] == context.revision_before + 1
    assert value['decisions'][-1]['actor'] == 'Sam'
    assert len(context.consultant.calls) == context.calls_before


@then('the already adopted argument remains in the model')
def remains(context):
    value = context.workspace.case(lambda app: app.workspace())
    assert sum(s == 'accepted' for s in value['membership'].values()) == 119
    assert not value['backlog']


@when('the operator chooses a tree statement and begins an answer about it')
def answer_about(context):
    context.workspace.press('ctrl+t')
    context.workspace.press('ctrl+p')
    choose_in_menu(context, 'Tree: Current Reality')
    context.workspace.tab_to('canvas')
    context.workspace.press('down')
    context.selected_words = context.workspace.read(lambda app: next(c['statement'] for c in app.tree_of(app.drawn_selection())['claims'] if c['ref'] == app.drawn_selection()))
    context.workspace.press('a')


@then('its words enter the editable draft without a revision or consultant call')
def quoted(context):
    assert context.selected_words in draft(context)
    assert 'Current Reality' in draft(context)
    sources = context.workspace.case(lambda app: app.sources()['sources'])
    assert not any(s.get('text') == draft(context) for s in sources.values())
    unchanged(context)


@then('the draft still answers the same live question')
def same_target(context):
    assert context.workspace.read(lambda app: app.workspace_value['target']) == context.target_before


@given('a new commons with the offline guide')
def guided(context):
    context.app = create_case(context.path, 'Running', consultant=GuidedConsultant())
    context.apps.append(context.app)


@when('the operator supplies a goal, protections, forecast, action, observation and review')
def loop(context):
    context.answers = ['Run 5k under 30 minutes', 'Today 34 min; by December', 'No knee pain\n- Sleep 7h',
                       'Intervals twice a week', '32 min within 3 weeks', 'October 24', '',
                       'Tuesday 7am intervals', 'Ran 5k in 32:40; knees fine', 'Close to forecast; keep and adjust']
    for words in context.answers:
        assert context.app.submit(words, 'Sam', **context.app.workspace()['target'])['status'] == 'saved'


@then('the guide retains the literal contributions and their attribution')
def literal(context):
    sources = [s for s in context.app.sources()['sources'].values() if 'request_id' in s]
    assert [s['text'] for s in sources] == context.answers
    assert all(s['speaker'] == 'Sam' for s in sources)


@then('the original test forecast and reported result remain distinct')
def forecast(context):
    records = context.app.inspect()['case']['records']
    test = next(r for r in records if r['kind'] == 'test')
    observation = next(r for r in records if r['kind'] == 'observation')
    assert test['data']['forecast'][0]['expected'] == context.answers[4]
    assert observation['data']['value'] == context.answers[8]
    assert observation['data']['basis'] == 'participant_report'


@then('the next loop is available without a completed tree')
def next_loop(context):
    assert context.app.workspace()['question']['data']['decision'] == 'Choose a test'
    assert not any(r['kind'] == 'claim' for r in context.app.inspect()['case']['records'])


@given('a disposable goals home')
def home(context):
    context.home = Path(context.temporary.name) / 'goals'


@when('Continue Reason Commons is opened and a draft is saved')
def first_open(context):
    context.first = continue_commons(context.home)
    with open_case(context.first) as app:
        app.checkpoint({'view': 'next', 'focus': 'editor', 'speaker': 'Sam', 'caret': 0,
                        'draft': 'My next contribution', **app.workspace()['target']})
        context.original = app.inspect()['case']
        context.original_sources = app.sources()


@when('Continue Reason Commons is opened again')
def second_open(context):
    context.second = continue_commons(context.home)


@then('the same commons, revision, sources and draft are resumed')
def same_import(context):
    assert context.first == context.second
    with open_case(context.second) as app:
        assert app.inspect()['case'] == context.original
        assert app.sources() == context.original_sources
        assert app.workspace()['draft']['draft'] == 'My next contribution'


@when('the operator changes light or dark using Settings')
def appearance(context):
    context.old_theme = context.workspace.read(lambda app: app.theme)
    settings_row(context, 'Mode')
    context.workspace.press('right', 'escape')


@then('the appearance preference is retained outside the commons')
def retained_appearance(context):
    assert context.workspace.read(lambda app: app.theme) == context.theme_before
    assert context.theme_before != context.old_theme
    settings = Settings.load()
    assert settings.get('theme') == context.theme_before


@then('the personal setting creates no revision or consultant call')
def unchanged(context):
    assert revision(context) == context.revision_before
    assert len(context.consultant.calls) == context.calls_before


@when('the operator sets a monthly budget of five dollars using Settings')
def budget(context):
    settings_row(context, 'Budget')
    context.workspace.press('enter')
    context.workspace.tab_to('budget')
    context.workspace.press('ctrl+a')
    context.workspace.type('5')
    context.workspace.press('enter', 'escape')


@then('the personal settings retain the budget outside the commons')
def personal_budget(context):
    assert Settings.load().get('usage', 'monthly_budget_usd') == '5'
    assert 'monthly_budget_usd' not in str(context.workspace.case(lambda app: app.inspect()))


class ModelStandIn(ScriptedConsultant):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.version = 'offline-stand-in/' + model


@given('a workspace with two offline model stand-ins')
def two_models(context):
    create_case(context.path, 'One reply').close()
    context.models = {model: ModelStandIn(model) for model in ('claude-haiku-5-5', 'claude-sonnet-5-5')}
    context.consultant = context.models['claude-haiku-5-5']
    context.workspace = Workspace(context.path, context.consultant, provider='anthropic',
                                  factory=lambda provider, model=None: context.models[model or 'claude-haiku-5-5'])
    context.workspaces.append(context.workspace)


@when('the operator sends an answer with deeper reasoning through Commands')
def deeper(context):
    context.workspace.type('We keep missing deliveries')
    command(context, 'Send with deeper reasoning')


@when('the operator sends an ordinary answer')
def ordinary(context):
    context.workspace.tab_to('editor')
    context.workspace.type('Measured weekly')
    context.workspace.press('ctrl+s')


@then('each applied request names the model stand-in that produced it')
def versions(context):
    versions = context.workspace.case(lambda app: app.inspect()['case']['adapter_versions'])
    assert versions == {'in000001': 'offline-stand-in/claude-sonnet-5-5',
                        'in000002': 'offline-stand-in/claude-haiku-5-5'}


@then('the ordinary answer uses the original consultant')
def original_model(context):
    assert len(context.models['claude-sonnet-5-5'].calls) == 1
    assert len(context.models['claude-haiku-5-5'].calls) == 1
    assert context.workspace.read(lambda app: app.chosen.once) is None


@given('a disposable guided practice workspace')
def practice(context):
    create_case(context.path, 'Practice').close()
    context.consultant = GuidedConsultant()
    context.workspace = Workspace(context.path, context.consultant, tour=True)
    context.workspaces.append(context.workspace)


@when('the operator fills and sends each tour example using its visible controls')
def tour_examples(context):
    context.tour_words = []
    while context.workspace.read(lambda app: app.tour_state()) != 'done':
        assert len(context.tour_words) < 20, 'tour did not finish'
        context.workspace.tab_to('fill')
        context.workspace.press('enter')
        assert draft(context).strip(), 'visible example control left an empty answer'
        context.tour_words.append(draft(context))
        context.workspace.press('ctrl+s')


@then('the tour reaches Loop complete with attributed literal example words')
def tour_complete(context):
    assert 'Loop complete' in context.workspace.screen_text()
    sources = context.workspace.case(lambda app: app.sources()['sources'])
    assert [s['text'] for s in sources.values() if 'request_id' in s] == context.tour_words
    assert all(s['speaker'] == 'Sam' for s in sources.values() if 'request_id' in s)


@then('Finish tour returns to the goals home')
def finish_tour(context):
    from reason_commons.adapters.tui import TOUR_FINISHED
    context.workspace.tab_to('finish')
    context.workspace.press('enter')
    assert context.workspace.app.return_value == TOUR_FINISHED


@given('the packaged editorial example in a disposable reading workspace')
def editorial_sample(context):
    from importlib.resources import files
    from reason_commons.adapters.story import load_story
    from reason_commons.adapters.tui import STORY_ARCHIVE
    from reason_commons.bootstrap import import_case
    import_case(str(files('reason_commons.adapters').joinpath(STORY_ARCHIVE)), str(context.path)).close()
    context.consultant = ScriptedConsultant()
    context.workspace = Workspace(context.path, context.consultant, story=load_story())
    context.workspaces.append(context.workspace)
    remember(context)


@when('the operator steps back through its history and opens its trees')
def browse_example(context):
    context.workspace.press('escape', 'left', 'ctrl+t')


@then('its attributed sources and earlier formulations remain locally inspectable')
def example_sources(context):
    assert context.workspace.read(lambda app: app.revision) < context.revision_before
    sources = context.workspace.case(lambda app: app.sources()['sources'])
    assert any(s.get('speaker') == 'David Joseph' for s in sources.values())
    assert context.workspace.read(lambda app: app.has_trees())


@then('reading hides the response editor and creates no revision or consultant call')
def read_only_example(context):
    unchanged(context)
    assert context.workspace.read(lambda app: app.query_one('#response').has_class('hidden'))
