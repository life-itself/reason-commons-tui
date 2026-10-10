"""Reconstruct the supplied development argument through application capabilities.

The chronology is explicitly reconstructed. Native dates and acceptance decisions
belong to this import, not to imagined historical participants. No local history
or original ledger is consulted to recover the story.
"""
from copy import deepcopy
from importlib.resources import files
import json
from pathlib import Path

VERSION = 'commons-import/2'
EDITOR = 'RC reconstruction editor (AI)'


def resource(name):
    return files('reason_commons.adapters').joinpath('commons/' + name).read_bytes()


class Reconstruction:
    version = VERSION

    def __init__(self, sources):
        self.sources, self.refs, self.chapter = sources, {}, None

    def propose(self, request):
        chapter = self.chapter
        local = {u['temporary_id'] for u in chapter['updates']}
        updates = []
        for authored in chapter['updates']:
            update = deepcopy(authored)
            spans = update.pop('spans')
            for field in ('from_ref', 'to_ref', 'replaces'):
                value = update['data'].get(field)
                if value and value not in local:
                    update['data'][field] = self.refs[value]
            update['source_refs'] = list(dict.fromkeys([self.sources[s] for s in spans] +
                                                       [request['input']['request_id']]))
            updates.append(update)
        goal = 'goal' if 'goal' in local else self.refs['goal']
        final = chapter.get('continue_work', False)
        return dict(schema_version='1', delivery_profile='p2',
                    request_id=request['input']['request_id'], base_revision=request['input']['base_revision'],
                    proposed_updates=updates, intervention=dict(
                        kind='recommendation' if final else 'question',
                        purpose='continuation' if final else 'reconstructed_development',
                        decision=chapter['title'], primary_prompt=chapter['question'],
                        rationale=chapter['why'], goal_ref=goal,
                        required_context_refs=[self.refs['receipt']] if final else [], options=[]))


def build_commons(destination, acceptance='automatic', adopted=True):
    from reason_commons.bootstrap import create_case
    if not adopted and acceptance != 'review':
        raise ValueError('An unadopted import requires review mode')
    manifest = json.loads(resource('development.json'))
    sources = {}
    narrator = Reconstruction(sources)
    app = create_case(destination, 'Reason Commons · development', consultant=narrator,
                      acceptance=acceptance, actor=EDITOR)
    try:
        for turn in json.loads(resource('conversation.json')):
            sources[turn['id']] = app.add_source('Original conversation ' + turn['id'],
                                                turn['text'].encode('utf-8'), turn['speaker'])
        sources['brief'] = app.add_source('Original builders brief', resource('builders-brief.txt'),
                                          'User-supplied builders brief')
        sources['scenario'] = app.add_source('Hypothetical implementation premise', resource('scenario.txt'),
                                             'User (hypothetical scenario)')
        sources['acceptance_request'] = app.add_source('Acceptance setting requested by the user',
            resource('acceptance-request.txt'), 'User (current design requirement)')
        for number, chapter in enumerate(manifest['chapters'], 1):
            chapter = deepcopy(chapter)
            if not adopted:
                if chapter['title'] == 'Import and adopt prior reasoning':
                    chapter['story'] = ('This is the reconstructed import boundary. The prior argument and '
                        'its sources are retained, but its reasoning is not yet adopted. Backlog contains '
                        'the proposals; adopting them will make the argument visible in the working trees. '
                        'Native dates are import dates, not unknown historical dates.')
                for update in chapter['updates']:
                    if update['temporary_id'] == 'receipt':
                        update['data']['text'] = ('Prior development is imported for review. Its proposals wait in '
                            'Backlog until adopted. History retains the reconstructed stages and source words.')
            narrator.chapter = chapter
            before = len(app.inspect()['case']['records'])
            text = (f'Reconstructed stage {number}: {chapter["title"]}\n\n{chapter["story"]}\n\n'
                    f'Reason for the next step: {chapter["why"]}')
            result = app.submit(text, EDITOR, **app.workspace()['target'])
            if result['status'] != 'saved':
                raise ValueError('Reconstruction proposal failed: ' + str(result))
            made = [r for r in app.inspect()['case']['records'][before:] if r['kind'] != 'intervention']
            for authored, record in zip(chapter['updates'], made):
                narrator.refs[authored['temporary_id']] = record['ref']
            if acceptance == 'review' and adopted and made:
                result = app.accept([r['ref'] for r in made], EDITOR,
                                    app.inspect()['case']['revision'], confirmed=True)
                if result['status'] != 'saved':
                    raise ValueError('Reconstruction acceptance failed: ' + str(result))
        app.close()
        from reason_commons.bootstrap import open_case, configured_consultant
        return open_case(destination, consultant=configured_consultant(provider='guided'))
    except Exception:
        app.close()
        raise


def continue_commons(root):
    """Resume this reconstruction or create a new commons without replacing earlier work."""
    from reason_commons.bootstrap import open_case
    root = Path(root)
    if root.exists():
        for path in sorted(root.iterdir()):
            if not path.is_dir() or path.name.startswith('.'):
                continue
            try:
                with open_case(path, writable=False) as app:
                    if VERSION in app.inspect()['case']['adapter_versions'].values():
                        return path
            except (OSError, ValueError, RuntimeError):
                continue
    root.mkdir(parents=True, exist_ok=True)
    path, suffix = root / 'reason-commons-development', 2
    while path.exists():
        path, suffix = root / f'reason-commons-development-{suffix}', suffix + 1
    with build_commons(path):
        pass
    return path
