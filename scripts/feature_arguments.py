"""Read explicitly authored tree proposals in Gherkin; never infer or execute them."""
from copy import deepcopy
import re

import yaml

from reason_commons.domain.model import InvalidCase, validate_value


class ArgumentLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise ValueError(f'Duplicate argument key: {key}')
        result[key] = loader.construct_object(value_node)
    return result


ArgumentLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def load_argument(text):
    """Read the human argument (or earlier YAML representation), never execute it."""
    begin, end = '# RC-ARGUMENT-BEGIN', '# RC-ARGUMENT-END'
    if begin not in text and end not in text:
        return None
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError('Exactly one complete RC argument block required')
    body = text.split(begin, 1)[1].split(end, 1)[0].strip('\n')
    lines = []
    for line in body.splitlines():
        if line == '#':
            lines.append('')
            continue
        if not line.startswith('# '):
            raise ValueError('Every argument line must be a Gherkin comment')
        lines.append(line[2:])
    if lines and lines[0].startswith('rc-argument:'):
        return read_sentences(lines)
    try:
        result = yaml.load('\n'.join(lines), Loader=ArgumentLoader)
    except yaml.YAMLError as exc:
        raise ValueError('Invalid argument YAML') from exc
    if not isinstance(result, dict):
        raise ValueError('Argument must be an object')
    return result


ROLES = {
    'NC': ('goal', 'necessary_condition'),
    'UDE': ('current_reality', 'undesirable_effect'),
    'cause': ('current_reality', 'intermediate_cause'),
    'injection': ('future_reality', 'injection'),
    'DE': ('future_reality', 'desired_effect'),
    'NBR': ('future_reality', 'undesirable_effect'),
    'objective': ('prerequisite', 'implementation_objective'),
    'obstacle': ('prerequisite', 'obstacle'),
    'IO': ('prerequisite', 'intermediate_objective'),
    'reality': ('transition', 'transition_existing_reality'),
    'need': ('transition', 'transition_need'),
    'action': ('transition', 'transition_action'),
    'effect': ('transition', 'transition_expected_effect'),
}


def read_sentences(lines):
    """Decode declared roles/IDs and fixed lead-ins, without guessing from free prose."""
    from behave.parser import ParserError, parse_feature

    header = re.fullmatch(r'rc-argument: schema 1 \| proposal ([a-z][a-z0-9_-]*) \| status proposed', lines[0])
    if not header:
        raise ValueError('Invalid readable argument header')
    try:
        feature = parse_feature('Feature: Development argument\n' + '\n'.join(lines[1:]))
    except ParserError as exc:
        raise ValueError(f'Invalid readable argument: {exc}') from exc
    result = {'schema_version': 1, 'proposal_id': header[1], 'status': 'proposed',
              'sources': {}, 'tree_context': {}, 'updates': [], 'evidence_required': {}}
    claims, links = {}, {}

    def claim(step):
        match = re.fullmatch(r'(.+) \[([A-Za-z]+) ([a-z][a-z0-9_]*)\]', step.name)
        if not match or match[2] not in ROLES:
            raise ValueError(f'Every argument claim needs a declared role and ID: {step.name}')
        sentence, role, identity = match.groups()
        basis, source = 'hypothesis', 'editor'
        if sentence.startswith('David reports that '):
            sentence, basis, source = sentence.removeprefix('David reports that '), 'participant_report', 'user_report'
        elif sentence.startswith('Codex found that '):
            sentence, basis = sentence.removeprefix('Codex found that '), 'participant_report'
        else:
            for lead in ('this overcomes the obstacle that ', 'we must first ensure that ',
                         'we suspect that ', 'we predict that ', 'we want to ', 'we need to ', 'we '):
                if sentence.startswith(lead):
                    sentence = sentence.removeprefix(lead)
                    break
        sentence = sentence[0].upper() + sentence[1:]
        if not sentence.endswith(('.', '?', '!')):
            sentence += '.'
        tree, native_role = ROLES[role]
        row = {'operation': 'record_claim', 'temporary_id': identity,
               'data': {'tree': tree, 'role': native_role, 'statement': sentence, 'basis': basis},
               'source_refs': [source]}
        if identity in claims and claims[identity] != row:
            raise ValueError(f'Repeated claim {identity} changed its sentence, role or attribution')
        claims[identity] = row
        return identity

    for rule in feature.rules:
        tags = set(map(str, rule.tags))
        if 'argument' not in tags or len(tags) != 2:
            raise ValueError('Each argument Rule needs @argument and one declared tree or @sources')
        tree = next(iter(tags - {'argument'}))
        if tree == 'sources':
            for example in rule.scenarios:
                if len(example.tags) != 1 or len(example.steps) != 1 or example.steps[0].text is None:
                    raise ValueError('Each source needs one identity, declared speaker and literal doc string')
                identity = str(example.tags[0])
                speaker = re.fullmatch(r'(.+) wrote:', example.steps[0].name)
                if identity in result['sources'] or not speaker:
                    raise ValueError('Duplicate source identity or missing declared speaker')
                result['sources'][identity] = {'speaker': speaker[1], 'text': str(example.steps[0].text)}
            continue
        if tree in result['tree_context']:
            raise ValueError(f'Duplicate argument tree: {tree}')
        result['tree_context'][tree] = ' '.join(line.strip() for line in rule.description)
        if rule.background:
            for step in rule.background.steps:
                claim(step)
        for example in rule.scenarios:
            if len(example.tags) != 2:
                raise ValueError('Each argument link needs its identity and relation')
            identity, relation = map(str, example.tags)
            if identity in links or identity in claims:
                raise ValueError(f'Duplicate argument link identity: {identity}')
            ends, assumption = [], None
            for step in example.steps:
                if step.name.startswith('assuming '):
                    if assumption is not None:
                        raise ValueError('Each argument link needs exactly one assumption')
                    assumption = step.name.removeprefix('assuming ')
                elif step.name.startswith('this link still needs '):
                    result['evidence_required'][identity] = step.name.removeprefix('this link still needs ').removesuffix(' evidence')
                elif step.name.startswith('this prediction still needs '):
                    if len(ends) != 2:
                        raise ValueError('Prediction evidence must follow the target claim')
                    result['evidence_required'][ends[1]] = step.name.removeprefix('this prediction still needs ').removesuffix(' evidence')
                else:
                    ends.append(claim(step))
            if len(ends) != 2 or assumption is None:
                raise ValueError('Each argument link needs exactly two claims and one assumption')
            links[identity] = {'operation': 'record_link', 'temporary_id': identity,
                              'data': {'tree': tree, 'relation': relation, 'from_ref': ends[0],
                                       'to_ref': ends[1], 'assumption': assumption}, 'source_refs': ['editor']}
    result['updates'] = list(claims.values()) + list(links.values())
    return result


def validate_argument(argument, text):
    """Check identities, native grammar, explicit citations and scenario/evidence links."""
    tags = re.findall(r'@(addresses|implements|verifies)_([a-z][a-z0-9_]*)\b', text)
    if argument is None:
        return ['Scenario reasoning tags require an RC argument block'] if tags else []
    errors = []
    if set(argument) != {'schema_version', 'proposal_id', 'status', 'sources', 'tree_context',
                         'updates', 'evidence_required'}:
        errors.append('Argument fields differ from the declared version-1 convention')
    if argument.get('schema_version') != 1 or argument.get('status') != 'proposed':
        errors.append('Argument schema must be 1 and its updates must remain proposed')
    if not isinstance(argument.get('proposal_id'), str) or not argument['proposal_id']:
        errors.append('Argument proposal identity required')
    trees = {'goal', 'current_reality', 'conflict', 'future_reality', 'prerequisite', 'transition'}
    if set(argument.get('tree_context', {})) != trees:
        errors.append('State the context or explicit absence of each of the six trees')
    sources = argument.get('sources', {})
    if not sources or any(not isinstance(s, dict) or not s.get('speaker') or not s.get('text') for s in sources.values()):
        errors.append('Every source needs declared attribution and literal retained text')
    updates = argument.get('updates', [])
    if not updates:
        errors.append('An authored argument needs explicit proposed updates')
    known = {}
    for update in updates:
        if set(update) != {'operation', 'temporary_id', 'data', 'source_refs'}:
            errors.append('Every update needs exactly one native operation, identity, data and source list')
        identity = update.get('temporary_id')
        if not isinstance(identity, str) or not re.fullmatch('[a-z][a-z0-9_]*', identity) or identity in known:
            errors.append(f'Missing or duplicate update identity: {identity}')
        operation, data = update.get('operation'), update.get('data', {})
        kind = {'record_claim': 'claim', 'record_link': 'link'}.get(operation)
        if kind is None:
            errors.append(f'{identity}: this precedent authors tree claims and links only')
        else:
            try:
                validate_value(kind, data)
            except (InvalidCase, TypeError, KeyError) as exc:
                errors.append(f'{identity}: invalid native tree grammar: {exc}')
        cited = update.get('source_refs', [])
        if not cited or len(set(cited)) != len(cited) or any(s not in sources for s in cited):
            errors.append(f'{identity}: missing, repeated or unknown source')
        if kind == 'link':
            ends = [known.get(data.get(side)) for side in ('from_ref', 'to_ref')]
            if any(not row or row['operation'] != 'record_claim' for row in ends):
                errors.append(f'{identity}: both link ends must be earlier authored claims')
            elif data.get('tree') not in {row['data']['tree'] for row in ends}:
                errors.append(f'{identity}: neither end belongs to the link tree')
            if data.get('from_ref') == data.get('to_ref'):
                errors.append(f'{identity}: self-link is invalid')
        known[identity] = update
    required = argument.get('evidence_required', {})
    if any(identity not in known or mode not in {'semantic', 'usability'} for identity, mode in required.items()):
        errors.append('Empirical evidence requirements must name an authored update and evaluation mode')
    # Tags belong to one scenario, so automated checks cannot silently authenticate a human benefit.
    headers = list(re.finditer(r'^\s+Scenario(?: Outline)?: .+$', text, re.M))
    for header in headers:
        prefix = text[:header.start()].rstrip('\n').splitlines()
        tag_lines = []
        while prefix and prefix[-1].strip().startswith('@'):
            tag_lines.append(prefix.pop())
        scenario_tags = '\n'.join(tag_lines)
        if not re.search(r'@(addresses|implements|verifies)_', scenario_tags):
            errors.append('Each scenario in an argument feature needs an explicit argument relationship')
        for relation, identity in re.findall(r'@(addresses|implements|verifies)_([a-z][a-z0-9_]*)\b', scenario_tags):
            if identity not in known:
                errors.append(f'Scenario references unknown update: {identity}')
            elif relation == 'implements' and known[identity]['data'].get('role') != 'transition_action':
                errors.append(f'{identity}: implements must name a Transition Tree action')
            elif relation == 'verifies' and identity in required and '@' + required[identity] not in scenario_tags:
                errors.append(f'{identity}: needs {required[identity]} evidence, not automated coverage')
    return errors


def bind_updates(argument, source_refs):
    """One authored update to one native proposal; the caller supplies actual retained source IDs."""
    updates = deepcopy(argument['updates'])
    for update in updates:
        update['source_refs'] = [source_refs[source] for source in update['source_refs']]
    return updates
