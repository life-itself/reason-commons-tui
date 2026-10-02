#!/usr/bin/env python3
"""Validate the acceptance bundle and list tagged delivery slices.

This is a structural document checker, not a Gherkin runner or CLI test.
The contract owns behavior; canonical artifacts own their embedded copies.
"""
from pathlib import Path
import argparse
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
MARKER = '## 7. Full Gherkin acceptance specifications'
PHASE_RE = re.compile(r'@p\d+$')
MODES = {'@automated', '@semantic', '@usability'}
SCOPING = MODES | {'@v1', '@later'}


def parse_scenarios(text, source):
    """Read the bundle's scenario-local tags and outline rows; return diagnostics.

    Deliberately narrower than a full Gherkin parser. Scoped tags on Features
    or Examples are rejected rather than implementing their inheritance.
    """
    errors, scenarios = [], []
    lines = text.splitlines()
    starts = []
    allowed_tag_lines = set()
    for i, line in enumerate(lines):
        match = re.match(r'^\s+Scenario( Outline)?: (.+)$', line)
        if not match:
            continue
        first = i
        while first > 0 and lines[first - 1].strip().startswith('@'):
            first -= 1
        tag_list = re.findall(r'@[^\s]+', '\n'.join(lines[first:i]))
        allowed_tag_lines.update(range(first, i))
        starts.append((first, i, match, tag_list))
    for i, line in enumerate(lines):
        if line.strip().startswith('@') and i not in allowed_tag_lines:
            tags = line.split()
            if any(PHASE_RE.fullmatch(t) or t in SCOPING or re.fullmatch(r'@S\d+', t) for t in tags):
                errors.append(f'{source}:{i+1}: scope/identity tags must be scenario-local')
    for n, (first, header, match, tag_list) in enumerate(starts):
        end = starts[n+1][0] if n+1 < len(starts) else len(lines)
        body = '\n'.join(lines[header+1:end])
        tags = set(tag_list)
        ids = [t for t in tag_list if re.fullmatch(r'@S\d+', t)]
        phases = [t for t in tag_list if PHASE_RE.fullmatch(t)]
        releases = tags & {'@v1', '@later'}
        modes = tags & MODES
        label = f'{source}:{match[2]}'
        if len(tag_list) != len(tags):
            errors.append(f'{label}: duplicate tags')
        for label_name, values in [('identity', ids), ('phase', phases), ('release', releases), ('evaluation', modes)]:
            if len(values) != 1:
                errors.append(f'{label}: exactly one {label_name} tag required')
        for step in ('When', 'Then'):
            if not re.search(r'^\s+' + step + r' ', body, re.M):
                errors.append(f'{label}: missing {step}')
        cases = 1
        if match[1]:
            if 'Examples:' not in body:
                errors.append(f'{label}: outline lacks Examples')
                cases = 0
            else:
                steps, table = body.split('Examples:', 1)
                rows = [x.strip() for x in table.splitlines() if x.strip().startswith('|')]
                cells = [[c.strip() for c in x.strip('|').split('|')] for x in rows]
                if len(cells) < 2:
                    errors.append(f'{label}: outline needs data rows')
                    cases = 0
                else:
                    if any(len(row) != len(cells[0]) for row in cells):
                        errors.append(f'{label}: unequal Examples columns')
                    if set(re.findall(r'<([^>]+)>', steps)) != set(cells[0]):
                        errors.append(f'{label}: outline variables differ from columns')
                    cases = len(cells) - 1
        scenarios.append({'id': ids[0][1:] if len(ids) == 1 else None,
                          'phase': phases[0][1:] if len(phases) == 1 else None,
                          'release': next(iter(releases))[1:] if len(releases) == 1 else None,
                          'mode': next(iter(modes))[1:] if len(modes) == 1 else None,
                          'tags': tags, 'name': match[2], 'body': body,
                          'cases': cases, 'source': source})
    return scenarios, errors


def validate_scope(scenarios, manifest):
    errors = []
    phases = manifest['phases']
    ids = [p['id'] for p in phases]
    if ids != [f'p{i}' for i in range(len(ids))] or len(ids) < 3:
        errors.append('Manifest phases must be a contiguous ordered sequence from p0 through at least p2')
    for i, phase in enumerate(phases):
        if phase['requires'] != ([] if i == 0 else [ids[i-1]]):
            errors.append(f"{phase['id']}: dependency must be the preceding phase")
        if phase['release'] != ('v1' if i < 3 else 'later'):
            errors.append(f"{phase['id']}: only p0-p2 belong to v1")
    releases = {p['id']: p['release'] for p in phases}
    scenario_ids = [s['id'] for s in scenarios]
    if None in scenario_ids or len(set(scenario_ids)) != len(scenario_ids):
        errors.append('Missing or duplicate scenario IDs')
    for scenario in scenarios:
        if scenario['phase'] not in releases:
            errors.append(f"{scenario['id']}: unknown delivery phase")
        elif scenario['release'] != releases[scenario['phase']]:
            errors.append(f"{scenario['id']}: phase and release tags disagree")
    expected = manifest['v1_scenarios']
    actual = {s['id'] for s in scenarios if s['release'] == 'v1'}
    if len(set(expected)) != len(expected) or actual != set(expected):
        errors.append('V1 scenario membership differs from the reviewed manifest')
    return errors


def select_scenarios(scenarios, selection, manifest):
    if selection == 'all':
        return scenarios
    if selection == 'v1':
        return [s for s in scenarios if s['release'] == 'v1']
    phases = [p['id'] for p in manifest['phases']]
    if selection.startswith('through-'):
        end = selection[len('through-'):]
        if end not in phases:
            raise ValueError(f'Unknown delivery selection: {selection}')
        selected = set(phases[:phases.index(end)+1])
    elif selection in phases:
        selected = {selection}
    else:
        raise ValueError(f'Unknown delivery selection: {selection}')
    return [s for s in scenarios if s['phase'] in selected]


def appendix():
    sections = [MARKER + '\n\n']
    for path in sorted((ROOT / 'features').glob('*.feature')):
        sections.append(f'### {path.name}\n\n```gherkin\n{path.read_text().rstrip()}\n```\n\n')
    for title, name in [
        ('## 8. V1 TUI goal action review session', 'example-mvp-session.txt'),
        ('## 9. Complete illustrative roadmap TUI session', 'example-tui-session.txt'),
        ('## 10. TUI cross-tool correction and action review', 'example-review-session.txt'),
    ]:
        sections.append(f'{title}\n\n```text\n{(ROOT / name).read_text().rstrip()}\n```\n\n')
    sections.append('## 11. Accessible ordered presentation\n\n' +
                    (ROOT / 'accessibility.md').read_text().rstrip() + '\n')
    return ''.join(sections).rstrip() + '\n'


def validate_interface_language(text):
    """Guard retired product vocabulary and independently specified command UI.

    Literal command-looking response text is permitted: it must not acquire
    an action grammar. This is an editorial guard, not a proof of usability.
    """
    errors = []
    if re.search(r'\b(?:cardroom|cards?)\b|\.cardcase\b', text, re.I):
        errors.append('retired brand or stationery metaphor')
    if '--plain' in text or 'Actions > Command' in text:
        errors.append('alternate interactive command surface')
    if re.search(r'\b(?:enters?|activates?|selects?)\s+["`]:[a-z]', text, re.I):
        errors.append('human scenario routed through a colon command')
    if re.search(r'`:(?:connections|changes|model|stance|rely|restore|choose|say|compose)\b', text):
        errors.append('specified interactive colon-command grammar')
    return errors


def validate_tui_frames(text, max_width):
    """Check declared fixed frames; never silently accept a clipped row."""
    errors, seen = [], set()
    lines = text.splitlines()
    starts = [(i, re.fullmatch(r'SCREEN (\w+) (\d+)x(\d+)', line))
              for i, line in enumerate(lines) if line.startswith('SCREEN ')]
    if not starts:
        errors.append('no TUI frames')
    for index, match in starts:
        if match is None:
            errors.append(f'line {index+1}: invalid screen declaration')
            continue
        sid, width, height = match[1], int(match[2]), int(match[3])
        if sid in seen:
            errors.append(f'{sid}: duplicate screen identity')
        seen.add(sid)
        if width > max_width or (width, height) not in {(120, 40), (80, 24), (40, 24)}:
            errors.append(f'{sid}: unsupported frame dimensions')
        block = lines[index+1:index+height+1]
        if len(block) != height or any(len(line) != width or not line.isascii() for line in block):
            errors.append(f'{sid}: frame geometry or ASCII differs')
        if any(re.search(r'\b(?:interventions?|question\d{3}|c\d{3})\b', line, re.I) for line in block):
            errors.append(f'{sid}: internal consulting unit leaked into user-facing UI')
        if block and (not block[0].startswith('+') or not block[-1].startswith('+')):
            errors.append(f'{sid}: missing enclosing frame')
        if not any('Focus:' in line or '| F:' in line for line in block[:3]):
            errors.append(f'{sid}: focused control missing')
    return errors


def validate_tui_ledger(text, config):
    errors = []
    semantic = re.findall(r'^EVENT semantic in(\d{3}) r(\d{4}) question(\d{3})$', text, re.M)
    local = re.findall(r'^EVENT local r(\d{4}) target=(\S+) dimension=(\S+) value=(\S+) actor=(\S+)$', text, re.M)
    calls, revisions = config['calls'], config['revisions']
    expected = list(range(1, calls+1))
    if [int(x[0]) for x in semantic] != expected or [int(x[2]) for x in semantic] != expected:
        errors.append('input/question sequence differs from consultant call count')
    commits = [int(x) for x in re.findall(r'^EVENT (?:start|local|semantic in\d{3}) r(\d{4})\b', text, re.M)]
    if commits != list(range(revisions+1)):
        errors.append(f'revision sequence differs: {commits}')
    if len(local) != revisions-calls or any('@' not in x[1] for x in local):
        errors.append('structured decision count or exact-version target differs')
    if f'CONSULTANT CALLS {calls}:' not in text or (
            f'{revisions} reasoning revisions = {calls} semantic commits + {revisions-calls} structured local decisions.' not in text):
        errors.append('final ledger missing')
    return errors


def check_session(name, config, require):
    text = (ROOT / name).read_text()
    require(config.get('format') == 'tui', f'{name}: session must use the TUI format')
    for issue in validate_tui_frames(text, config['width']) + validate_tui_ledger(text, config):
        require(False, f'{name}: {issue}')
    require(f"Delivery profile: {config['profile']} cumulative" in text,
            f'{name}: delivery profile differs')
    if config['profile'] == 'p2':
        require('EVENT local' not in text, f'{name}: later structured decisions leak into v1')
        for token in ['result awaiting observation', 'original', 'goal >=90% remains unmet', '90% BREACH']:
            require(token in text, f'{name}: missing v1 consequence: {token}')
    if name == 'example-tui-session.txt':
        for token in ['P1@1', 'P2@1', '18/24 = 75%', '9/10 = 90%', 'Leo still DISPUTES L3@1',
                      'SCREEN S05A 120x40', 'SCREEN S23 80x24', 'SCREEN S24 40x24']:
            require(token in text, f'{name}: lost consequential record: {token}')


def check(selection='all', list_selected=False):
    errors = []
    def require(condition, message):
        if not condition:
            errors.append(message)
    manifest = json.loads((ROOT / 'delivery-phases.json').read_text())
    require(manifest['schema_version'] == 1, 'Unsupported phase manifest version')
    spec = (ROOT / 'reason-commons-specification.md').read_text()
    require(MARKER in spec and spec.split(MARKER, 1)[1] == appendix().split(MARKER, 1)[1],
            'Embedded artifacts differ; run --sync')
    features = sorted((ROOT / 'features').glob('*.feature'))
    scenarios, jobs = [], set()
    for path in features:
        text = path.read_text()
        require(len(re.findall(r'^Feature:', text, re.M)) == 1, f'{path.name}: one Feature required')
        jobs.update(re.findall(r'@J(\d{2})\b', text))
        parsed, issues = parse_scenarios(text, path.name)
        scenarios.extend(parsed)
        errors.extend(issues)
    errors.extend(validate_scope(scenarios, manifest))
    names = [s['name'] for s in scenarios]
    require(len(names) == len(set(names)), 'Duplicate scenario names')
    require(jobs == {f'{i:02}' for i in range(1, 17)}, 'Job coverage must include J01-J16')
    contract = spec.split(MARKER)[0]
    trace = contract.split('## 5. Gherkin and traceability')[1].split('## 6. Build sequence')[0]
    covered = set()
    for lo, hi in re.findall(r'S(\d+)–S(\d+)', trace):
        covered.update(range(int(lo), int(hi)+1))
    require(covered == {int(s['id'][1:]) for s in scenarios if s['id']}, 'Traceability ranges differ from scenario IDs')
    require(manifest.get('interface') == {
        'product': 'Reason Commons', 'executable': 'reason-commons',
        'default': 'persistent_tui', 'alternate': 'accessible_ordered_text',
        'interactive_command_language': False, 'user_facing_intervention_ids': False},
        'Interface policy differs from the canonical workspace contract')
    require(set(manifest['screens']) == set(manifest['sessions']), 'Screen/session manifest differs')
    screen_count = 0
    for name, config in manifest['sessions'].items():
        text = (ROOT / name).read_text()
        ids = re.findall(r'^SCREEN (\w+) ', text, re.M)
        require(ids == manifest['screens'].get(name), f'{name}: exact screen identities/order differ')
        screen_count += len(ids)
        for number, line in enumerate(text.splitlines(), 1):
            require(line.isascii(), f'{name}:{number}: non-ASCII terminal output')
            require(len(line) <= config['width'], f'{name}:{number}: exceeds {config["width"]} columns')
    active_sources = [ROOT / 'README.md', ROOT.parent / 'README.md', ROOT.parent / 'TUI-DESIGN.md',
                      ROOT / 'reason-commons-specification.md', ROOT / 'tui-reasoning-design.md',
                      ROOT / 'delivery-phases.md', ROOT / 'interface-improvement-plan.md',
                      ROOT / 'accessibility.md', *features, *[ROOT / n for n in manifest['sessions']]]
    for path in active_sources:
        for issue in validate_interface_language(path.read_text()):
            require(False, f'{path.name}: {issue}')
    for old_name in ['cli-wireframes.txt', 'example-shell-session.txt']:
        require(not (ROOT / old_name).exists(), f'Superseded interactive artifact reintroduced: {old_name}')
    envelopes = re.findall(r'```json\n(.*?)\n```', contract, re.S)
    require(bool(envelopes), 'Response envelopes missing')
    for envelope in envelopes:
        try:
            obj = json.loads(envelope)
            require(obj['delivery_profile'] in {'p2', 'p3'}, 'Envelope lacks a delivery profile')
            if obj['delivery_profile'] == 'p3':
                require(obj['intervention']['presentation']['focal_object_refs'] == ['L3@1'], 'Causal envelope lacks exact focus')
            else:
                require(obj['intervention']['goal_ref'] == 'G1@1' and 'diagram' not in obj['intervention'], 'V1 envelope requires a goal purpose and no diagram')
        except (json.JSONDecodeError, KeyError) as exc:
            errors.append(f'Response envelope invalid: {exc}')
    releases = {phase['id']: phase['release'] for phase in manifest['phases']}
    for name, config in manifest['sessions'].items():
        require(config['profile'] in releases, f'{name}: unknown session profile')
        check_session(name, config, require)
    readme = (ROOT / 'README.md').read_text()
    cases = sum(s['cases'] for s in scenarios)
    require(f'{len(features)} `.feature` files' in readme and f'{len(scenarios)} named' in readme and f'{cases} cases' in readme,
            'README feature/scenario/case counts differ')
    require(f'{screen_count} ASCII screens' in readme, 'README screen count differs')
    v1 = [s for s in scenarios if s['release'] == 'v1']
    require(f"V1: {len(v1)} scenarios and {sum(s['cases'] for s in v1)} expanded cases" in readme,
            'README v1 counts differ')
    phase_rows = {phase: (int(count), int(expanded)) for phase, count, expanded in
                  re.findall(r'^\| (p\d+) \| [^|]+\| (\d+) \| (\d+) \|$', readme, re.M)}
    for phase in releases:
        subset = [s for s in scenarios if s['phase'] == phase]
        require(phase_rows.get(phase) == (len(subset), sum(s['cases'] for s in subset)),
                f'README {phase} counts differ')
    try:
        selected = select_scenarios(scenarios, selection, manifest)
    except ValueError as exc:
        errors.append(str(exc))
        selected = []
    if errors:
        print('\n'.join('FAIL: ' + error for error in errors), file=sys.stderr)
        return 1
    print(f'PASS: {len(features)} features; {len(scenarios)} scenarios; {cases} expanded cases; '
          f'{screen_count} TUI screens; synchronized artifacts; delivery tags/profiles; ASCII frames; response envelopes; '
          f'{len(manifest["sessions"])} TUI session ledgers.')
    print(f'Selected {selection}: {len(selected)} scenarios; {sum(s["cases"] for s in selected)} expanded cases.')
    if list_selected:
        for scenario in sorted(selected, key=lambda s:int(s['id'][1:])):
            print(f"{scenario['id']} @{scenario['phase']} @{scenario['release']} @{scenario['mode']} ({scenario['cases']} cases) {scenario['name']}")
    print('Structural checks only; no application behavior, semantic quality, or usability is verified.')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sync', action='store_true', help='rebuild embedded artifacts before checking')
    parser.add_argument('--select', default='all', help='all, v1, pN, or through-pN')
    parser.add_argument('--list', action='store_true', help='list the selected requirements, not run them')
    args = parser.parse_args()
    if args.sync:
        path = ROOT / 'reason-commons-specification.md'
        base = path.read_text().split(MARKER, 1)[0].rstrip()
        path.write_text(base + '\n\n' + appendix())
    return check(args.select, args.list)


if __name__ == '__main__':
    sys.exit(main())
