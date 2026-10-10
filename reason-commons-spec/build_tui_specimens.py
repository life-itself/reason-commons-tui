#!/usr/bin/env python3
"""Project authored screen content onto fixed character-cell specimens.

This builds specification examples, not a runnable TUI or a causal renderer.
Assertions catch overflowing copy instead of silently clipping it.
"""
from pathlib import Path
from textwrap import dedent, fill
import re

ROOT = Path(__file__).resolve().parent
SCREENS = []
QUESTION_TITLES = {}


def cloud_diagram():
    """An authored Cloud with routed gutters and node-boundary ports."""
    cells = [[' '] * 97 for _ in range(21)]
    def text(x, y, value):
        cells[y][x:x+len(value)] = list(value)
    def box(x, y, w, labels):
        text(x, y, '+'+'-'*(w-2)+'+')
        for n, label in enumerate(labels, 1):
            assert len(label) <= w-4
            text(x, y+n, '| '+label.ljust(w-4)+' |')
        text(x, y+len(labels)+1, '+'+'-'*(w-2)+'+')
    def vertical(x, a, b):
        for y in range(a, b+1):
            cells[y][x] = '|'
    def horizontal(y, a, b):
        for x in range(a, b+1):
            cells[y][x] = '-'
        cells[y][a] = cells[y][b] = '+'
    box(27, 0, 43, ['A  Dependable Payments service'])
    box(0, 6, 43, ['B  Serve urgent customer needs', 'quickly enough'])
    box(49, 6, 43, ['C  Validate standard changes', 'reliably'])
    box(0, 13, 43, ['D  Insert hotfix in active release', 'immediately'])
    box(49, 13, 43, ["D' Keep that active release frozen", 'during validation'])
    for port, target in [(35, 21), (61, 70)]:
        cells[2][port] = '+'
        vertical(port, 3, 3)
        horizontal(4, min(port, target), max(port, target))
        vertical(target, 5, 5)
        cells[6][target] = '+'
        cells[9][target] = '+'
        vertical(target, 10, 12)
        cells[13][target] = '+'
        cells[16][target] = '+'
        vertical(target, 17, 17)
    text(4, 4, 'requires?')
    text(76, 4, 'requires?')
    text(24, 11, 'requires?')
    text(73, 11, 'requires?')
    horizontal(18, 21, 70)
    text(24, 19, 'cannot both hold in this active release window')
    return '\n'.join('        '+''.join(row).rstrip() for row in cells).rstrip()


def joint_inference_diagram(compact=False):
    """Equal-width proposition boxes and ports for the complete L3 inference."""
    w = 73
    inner = w - 4
    premises = [
        'Validation is interrupted and must be repeated for this change.',
        'Net unrecovered recheck time exceeds slack before release cutoff.',
        'No eligible later release occurs before its three-day deadline.',
    ]
    rows = ['+' + '-- ALL / L3@1 '.ljust(w-2, '-') + '+']
    for premise in premises:
        assert len(premise) <= inner-4
        if compact:
            rows.append('| ' + premise.ljust(w-4) + ' |')
        else:
            rows.extend(['| +' + '-'*(inner-2) + '+ |',
                         '| | ' + premise.ljust(inner-4) + ' | |',
                         '| +' + '-'*(inner-2) + '+ |'])
    port = w//2
    rows.append('+' + '-'*(port-1) + '+' + '-'*(w-port-2) + '+')
    rows.extend([' '*port + '| L3: hypothesis', ' '*port + 'v'])
    label = 'This standard change misses the 3-day target'
    ow = len(label)+4
    left = port-ow//2
    top = list('+'+'-'*(ow-2)+'+')
    top[ow//2] = '+'
    rows.extend([' '*left + ''.join(top),
                 ' '*left + '| '+label+' |',
                 ' '*left + '+'+'-'*(ow-2)+'+'])
    return '\n'.join('        '+row for row in rows)


def prose(text, width=118):
    # Ledger lines are records, not prose: wrapping one would hide it from the checker.
    return '\n'.join(fill(p, width=width) if p and not p.startswith('EVENT ') else p
                     for p in text.strip().split('\n')) + '\n\n'


def frame(sid, rev, title, body, *, focus='Response', view='Next', draft='',
          summary='Goal: >=80% within 3 business days | Protect: rollback <=5%; after-hours <=8h/week',
          speaker='Maya', live=None, width=120, height=40, nav=True,
          footer=None, buttons='[Send]  [Explain this]  [Other moves]  [Actions]', case='deploy-flow'):
    match = re.match(r'question(\d{3}) / (.+)', title)
    if match:
        QUESTION_TITLES['question'+match[1]] = match[2]
        title = match[2]
    if live and re.fullmatch(r'question\d{3}', live):
        live = QUESTION_TITLES.get(live, 'current question')
    inner = width - 2
    def row(text):
        assert len(text) <= inner, (sid, len(text), text)
        assert text.isascii(), (sid, text)
        return '|' + text.ljust(inner) + '|'
    border = '+' + '-' * inner + '+'
    header = (f' {case} | {speaker} (declared) | {rev} saved | {title} | Focus: {focus}'
              if width >= 120 else f' {case} | {speaker} | {rev} saved | {title} | Focus: {focus}'
              if width >= 80 else f' {rev} saved | {speaker} | {title} | F:{focus}')
    lines = [border, row(header),
             border, row(' ' + summary), border]
    content = dedent(body).strip('\n').splitlines()
    assert len(content) <= height - 13, (sid, len(content), height-13)
    content += [''] * (height - 13 - len(content))
    navlabels = ['Reason Commons', '', *[('* ' if v == view else '  ') + v for v in
                 ['Next', 'Goal', 'Reasoning', 'Unlinked', 'Tests', 'Actions', 'History']],
                 '', '[Views]', '[Actions]', '', 'Saved locally']
    for i, line in enumerate(content):
        if nav:
            assert len(line) <= inner - 19, (sid, len(line), line)
            left = navlabels[i] if i < len(navlabels) else ''
            lines.append(row(' ' + left.ljust(15) + '| ' + line.ljust(inner - 19) + ' '))
        else:
            lines.append(row(' ' + line))
    lines.append(border)
    live = live or title.split(' / ')[0]
    continuation = (f' Response to {live} | Send asks consultant; Enter adds a line.' if focus == 'Response'
                    else f' Live question: {live} | Draft retained. [Return to question]')
    if width < 80:
        continuation = ' Live question | Draft retained'
    if width == 80:
        continuation = (' Response | Send asks consultant; Enter adds a line.' if focus == 'Response'
                        else f' Live: {live} | Draft retained')
    lines.append(row(continuation))
    drafts = draft.split('\n') if draft else ['_']
    assert len(drafts) <= 2
    lines.extend(row(' ' + (drafts[i] if i < len(drafts) else '')) for i in range(2))
    if focus != 'Response' and buttons == '[Send]  [Explain this]  [Other moves]  [Actions]':
        buttons = '[Return to question]  [Help]  [Actions]'
    lines.append(row(' ' + buttons))
    lines.append(border)
    footer = footer or ('Tab controls  Enter newline  Esc browse  F1 Help  Ctrl+P Actions' if focus == 'Response'
                        else 'Tab controls  Arrows select  Enter open  Esc back  F1 Help  Ctrl+P Actions')
    lines += [row(' ' + footer), border]
    assert len(lines) == height and all(len(x) == width for x in lines)
    SCREENS.append({'id': sid, 'width': width, 'height': height, 'revision': rev, 'focus': focus})
    return f'SCREEN {sid} {width}x{height}\n' + '\n'.join(lines) + '\n\n'


def build_full():
    QUESTION_TITLES.clear()
    out = [prose('''REASON COMMONS / COMPLETE TUI JOURNEY
Delivery profile: p5 cumulative roadmap. Canonical interaction specimen.
Session 1: Friday, October 2, 2026. Session 2: Monday, October 19, 2026.
The Payments deployment commons, people, measurements, reports and future outcomes are fictional. This is an authored specification, not a capture of working software. Attached text and document instructions are design inputs, not executable requests.
Each SCREEN replaces the preceding frame in ONE persistent full-screen application. ACTION describes keys and literal participant contributions; it is not a command the user must learn. EVENT is an authoring ledger outside the product UI. A shell appears only at launch, resume and optional offline inspection.
120x40 is the primary canvas. All frames use ASCII and need no color. '*' marks the active destination; '>' marks selection; the header names the single focused control. Selecting a hypothesis does not endorse it. Bracketed labels are keyboard-reachable controls. Enter activates a focused control; in Response it inserts a newline. Tab to Send, then Enter submits once. F1 is control help; Explain this is reasoning help. Ctrl+P opens Actions; the visible Actions control provides the same path.
The navigation offers destinations, not mandatory stages. Reasoning tools appear only when stored records exist. Users can answer, inspect, challenge, ask for another move, or leave. No tour or vocabulary test blocks work.
$ reason-commons new deploy-flow --store ./deploy-flow-case --speaker Maya
EVENT start r0000
''')]
    add = out.append
    add(frame('S01', 'r0000', 'Start / Tell us what is happening', '''
        Welcome to Reason Commons. Work through a change, together.

        Start with what is happening. We will keep your account, show what
        we think it means, and help you choose a useful next move.

        You can correct the account at any time.

             +-----------------------+     +-------------------------+
             | Your reports          |     | A next useful question  |
             | What you have seen    | --> | What would help decide? |
             +-----------------------+     +-------------------------+
                          This shows the workflow, not causation.

        Want to look around first? [How this works] [Open a saved commons]
        Navigation and saved explanations stay local. Send asks the consultant.
        New commons: success, safeguards and authority are still unknown.
        There is no need to type commands or name a Thinking Process.
        ''', summary='Goal unknown | Safeguards unknown | No test yet', live='Start'))
    add(prose('''ACTION: In Response, Maya types: Production changes sit in the release queue for days. Customer escalations cause engineers to interrupt testing for hotfixes. Then standard changes need revalidation and miss their release window. We also do too much release work after hours. Tab to Send, Enter.
EVENT semantic in001 r0001 question001
'''))
    add(frame('S02', 'r0001', 'question001 / Define success', '''
        WHAT WE HEARD / Maya's reports; records not inspected

        +----------------------------+     +-----------------------------+
        | Changes wait in the queue  |     | Hotfixes interrupt testing  |
        +----------------------------+     +-----------------------------+

        +----------------------------+     +-----------------------------+
        | Standard work revalidated  |     | Release work after hours    |
        +----------------------------+     +-----------------------------+
        Kept as separate reports. Their connections are not established yet.

        DECISION / What would count as an improvement worth keeping?
        What progress do you want, by when, and what must not get worse?

        You might give a measure, a date, and one or two safeguards.
        If a number is unknown, say so; we can keep it open.
        [See the reports]  [Help me define success - asks consultant]
        ''', summary='Goal provisional: shorter release lead time | Safeguards not yet specified'))
    add(prose('''ACTION: Maya enters a multiline response with Enter between lines, then Tab to Send and Enter:
Scope: standard production changes for Payments. For changes marked release-ready October 1-30, at least 80% reach production within 3 business days. September: 12/30 within 3 business days; 3/30 rollbacks; about 11 after-hours engineer-hours per week. Protect rollback <=5% of the deployed cohort and after-hours release work <=8 engineer-hours in any week, outside 08:00-18:00. These are my reports of the dashboard and rota; I have not attached the records. Use Monday-Friday 08:00-18:00 Europe/Berlin as business hours, with no excluded closures. Review October 30, with any immature three-day outcomes marked pending rather than failures.
EVENT semantic in002 r0002 question002
'''))
    add(frame('S03', 'r0002', 'question002 / Connect the reports', '''
        SUCCESS / G1@1                                      BASELINE / September
        +-----------------------------------------------+  +----------------------+
        | >=80% of Oct 1-30 release-ready Payments       |  | Within 3 days: 12/30 |
        | changes reach production within 3 business    |  | = 40%                |
        | days. Oct 30 review; immature outcomes pending.|  | Rollback: 3/30 = 10% |
        +-----------------------------------------------+  | After-hours: ~11h/wk |
                                                           +----------------------+
        Protect rollback <=5%; after-hours <=8 engineer-hours in EVERY week.
        Calendar, timezone and cohort maturation are explicit fields in [Goal].
        Source: Maya's reports. Other people's positions on G1 remain unknown.

        DECISION / Which explanation should we examine before choosing a change?
        Which reported effect do you think causes another?

        [Goal and safeguards]  [Unlinked reports]  [Other moves]
        You can propose a connection or tell us this is the wrong next question.
        ''', draft='Urgent customer escalations cause standard changes to miss the three-day target._'))
    add(prose('''ACTION: Maya activates Send with the displayed draft.
EVENT semantic in003 r0003 question003
'''))
    add(frame('S04', 'r0003', 'question003 / Find the mechanism', '''
        CURRENT REALITY / first proposed connection, not an established cause

        +-------------------------------+            +-------------------------------+
        | Urgent customer escalations   |            | Standard changes miss the     |
        | Maya reports these occur      |-- L1 ? --->| three-business-day target     |
        +-------------------------------+ hypothesis +-------------------------------+

        The arrow needs an explanation of what changes in the work.
        DECISION / Is this a useful mechanism to test?
        How does an escalation make a standard change late?

        Tell us what happens between the two boxes and when it does not happen.
        [Inspect connection]  [Explain this]  [Challenge the question]
        No claim of an operational constraint follows from this diagram.
        '''))
    add(prose('''ACTION: Maya answers: Engineers stop validation to insert the hotfix, then restart checks. This misses the target only when net unrecovered recheck time exceeds slack before release cutoff and no eligible later release occurs before the three-day deadline. Spare capacity or another eligible release could prevent that.
EVENT semantic in004 r0004 question004
'''))
    add(frame('S05', 'r0004', 'question004 / Test the whole inference', '''
        CURRENT REALITY / Payments standard changes / proposed, partial
        Read down: every premise inside ALL belongs to ONE inference.

        __JOINT_INFERENCE__
        Spare capacity could defeat premise 2; another timely release defeats premise 3.
        Missing evidence: dated interruptions, rechecks, slack and release windows.
        Could the threatened release date instead be causing the escalation?
        [Expand reasoning]  [Compare directions]  [Explain ALL]
        '''.replace('        __JOINT_INFERENCE__', joint_inference_diagram())))
    add(prose('''ACTION: Maya types the start of an answer, "Could delay already exist?", then Tabs to Expand reasoning and opens it. Her draft is checkpointed. The larger map and its right-hand inspector use the same r0004, selected L3@1 and exact premises. This is optional inspection, not another answer or consultant call.
'''))
    add(frame('S05A', 'r0004', 'Reasoning / Explore L3@1', '''
        BRANCHES / select a relation      CRT / arrows UP / partial     SELECTED L3@1
        > L3 interruption + delay        +-------------------------+   Hypothesis, not proof
          L1 escalation to hotfix        | Standard change misses  |   Inputs: all 3 required
          Other routes not mapped        | three-day target        |   Scope: this change
                                        +------------^------------+   before release window
        SAME SAVED MODEL                             | L3 hypothesis
        Expand/collapse changes          +-----------+-------------+   MECHANISM
        the view, never the claim.        | ALL                     |   Rechecks consume time;
                                        | Interruption + rechecks  |   time unavailable before
        Unlinked reports retained:       | Net loss exceeds slack  |   release; delay crosses
          After-hours work               | before release cutoff   |   three-day boundary.
          Queue delays                   | No timely later release |
        Unknown links stay unknown.      +------------^------------+   EVIDENCE
                                                     |                Maya's report, in004.
                                        +------------+------------+   Dashboard not attached.
                                        | Validation interrupted  |   Event sequence unknown.
                                        +------------^------------+
                                                     | L1 hypothesis  CHALLENGE
                                        +------------+------------+   Can another release or
                                        | Urgent escalation;      |   recovery route absorb
                                        | hotfix inserted         |   the lost time?
                                        +-------------------------+
        Sources support occurrence separately from inference. Node evidence is not link evidence.
        [Full L3 record]  [Evidence]  [Challenge this]  [Return to question]
        ''', focus='Branch list', view='Reasoning', live='question004',
        draft='Retained response draft: Could delay already exist?',
        buttons='[Full relation]  [Evidence]  [Return to question]  [Actions]'))
    add(prose('''ACTION: Esc restores the question, its diagram, draft text and editor cursor. The draft remains unsent and attributed to Maya.
'''))
    add(prose('''OPTIONAL INSPECTION: Before switching, Maya opens Explain ALL from the question. This worked counterfactual was stored with the question. Its numbers are illustrative assumptions, not measured Payments evidence, and add no revision or call. It shows why missing a release depends on lost time versus slack, and why missing one release does not alone prove the three-day target was missed.
'''))
    add(frame('S05B', 'r0004', 'Explain L3 / Test the boundary', '''
        AN ILLUSTRATION, NOT COMMONS EVIDENCE / same change and release availability
        Minutes from one chosen origin; deployment occurs at an eligible release.
        +-- SHARED TIMING -------------------------------------------------------+
        | Planned validation finish: 90 | release cutoff: 120 | deadline: 180    |
        | Next eligible release if current one is missed: 240                   |
        +-----------------------------------------------------------------------+

        SAME FIELDS                      MORE NET RECHECKS     FEWER NET RECHECKS
        Planned validation finish        90 min                90 min
        Added recheck time               60 min                20 min
        Recoverable time                  0 min                 0 min
        Final validation finish         150 min               110 min
        Slack before cutoff              30 min                30 min
        Release cutoff                  120 min               120 min
        Eligible deployment             240 min               120 min
        Three-day deadline              180 min               180 min
        Predicted target outcome        MISSED                MET

        Even with NO recovery, 20 min rechecks fit the 30 min slack.
        And if an eligible later release were at 160, the first example could meet 180.
        Both conditions matter. The boxes help us test a claim, not certify it.
        These calculations do not establish how often either situation occurs.
        [Return to question]  [Show actual evidence - reports only]
        ''', focus='Worked explanation', view='Reasoning', live='question004',
        draft='Retained Maya draft for the question: Could delay already exist?',
        buttons='[Return to question]  [Actual sources]  [Actions]'))
    add(prose('''ACTION: Esc returns to the question and its retained draft. The following switch opens Leo's separate response to the question; Maya's unsent text remains labeled for its original question and actor even after a new response arrives.
'''))
    add(prose('''ACTION: Maya chooses Actions > Change speaker, enters Leo, then activates Use label. Cursor changes only. Leo answers in Response: Threatened dates may cause escalation. Interruptions could amplify an existing delay rather than start it. Your wording represents my objection, but I dispute the claim that interruptions are the main cause.
EVENT semantic in005 r0005 question005
'''))
    add(frame('S06', 'r0005', 'question005 / Compare explanations', '''
        SAME OUTCOME / standard change misses 3 business days
        These accounts can coexist. Neither is established by an association.

        +-- H1 / interruption first -------------+ +-- H2 / delay first ----------------+
        | Interruption + required rechecks      | | Existing queue or complexity       |
        | AND net delay exceeds release slack        | | threatens the release date         |
        | AND no timely later release      | |                 |                  |
        |                 | hypothesis          | |                 v hypothesis       |
        |                 v                     | | Escalation follows threatened date |
        | Three-day target missed               | | It may add more delay: not settled |
        +---------------------------------------+ +------------------------------------+

        Distinguish with: event order, queue/load, recheck duration, release slack.
        Evidence so far: Maya's and Leo's reports. No event series inspected.
        DECISION / What observation would change the pilot we choose?
        What happens in a similar low-queue period when a hotfix interrupts checks?
        [Inspect L3]  [Sources]  [Record a position]  [Other moves]
        ''', speaker='Leo'))
    add(prose('''ACTION: Leo opens Inspect L3, then Record a position. This opens stored records locally. His earlier natural-language objection is a reported objection; the structured fields below remain unrecorded until he explicitly saves them.
'''))
    add(frame('S07', 'r0005', 'Position / L3@1', '''
        RECORD FOR / Leo (declared) / exact formulation L3@1
        Validation interruption + rechecks; net unrecovered time exceeds release slack;
        no eligible later release before three-day deadline -> standard change misses target.

        WORDING / Does this accurately represent the claim being discussed?
          ( ) Accurate    ( ) Inaccurate    ( ) Unknown     Current: unrecorded

        BELIEF / What is your position on that claim?
          ( ) Supported   ( ) Disputed      ( ) Unknown     Current: unrecorded

        RELIANCE / Will you run a particular bounded test?
          No test version selected. This is a separate decision.

        Saving wording never changes belief. Saving belief never commits a test.
        No substantive choice is preselected. Space selects a focused radio.
        [Save position - local]  [Choose test - none yet]  [Cancel]
        ''', speaker='Leo', focus='Wording', live='question005', view='Reasoning'))
    add(prose('''ACTION: Leo selects only Accurate in Wording and activates Save position.
EVENT local r0006 target=L3@1 dimension=representation value=accurate actor=Leo
ACTION: In the same panel he selects only Disputed in Belief and activates Save position.
EVENT local r0007 target=L3@1 dimension=belief value=disputed actor=Leo
Receipt: r0007 saved. Leo: wording accurate; belief disputed on L3@1. Reliance unrecorded. No consultant calls. Esc returns to the question with the response draft intact.
ACTION: Actions > Change speaker > Maya. Maya answers: When the queue is small, interrupted testing often recovers before the next release window. With a large queue, standard work waits longer. But hotfixes also tend to arrive when the queue is already bad, so that comparison does not isolate the cause.
EVENT semantic in006 r0008 question006
'''))
    add(frame('S08', 'r0008', 'question006 / Keep the qualification visible', '''
        REPORTED COMPARISON / Maya; no controlled comparison
                           Lower queue                 Higher queue
        Recovered time     Often before release        Often not recovered
        Target missed      Not necessarily             Reported more often
        Hotfix frequency   Unknown                     Reported higher
        Source             Maya's account              Maya's account

        L3@1 remains a conditional hypothesis. Leo's belief: DISPUTED.
        H2 remains plausible: queue/load may influence both escalation and delay.
        [Event evidence]  [Compare directions]  [Inspect L3]

        DECISION / Should we test interruption policy under these uncertainties?
        What makes Support and Engineering choose different actions now?
        You can describe both needs or ask for a different route.
        [Describe conflict]  [Give me direct help - asks consultant]
        '''))
    add(prose('''ACTION: Maya answers: Support needs urgent customer issues addressed quickly and thinks that requires inserting hotfixes immediately. Engineering needs standard releases validated reliably and thinks that requires freezing the active release. Both want dependable Payments changes and customer service.
EVENT semantic in007 r0009 question007
'''))
    add(frame('S09', 'r0009', 'question007 / Examine a necessity assumption', '''
        CONFLICT CLOUD / scoped necessity claims, all proposed
''' + cloud_diagram() + '''
        FOCUS / B requires D? Assumption: quick service needs immediate insertion.
        The need matters. Is this action the only way to meet it?
        Acknowledgement alone would not establish that the customer need was served.
        [Inspect B requires D]  [Other side's assumptions]  [Explain Cloud]
        '''))
    add(prose('''ACTION: Maya answers: We could acknowledge within four business hours, triage severity, state when the deployment decision will be made, freeze active validation and reserve one urgent slot in the next release. Keep the existing emergency path for genuinely critical incidents.
EVENT semantic in008 r0010 question008
'''))
    add(frame('S10', 'r0010', 'question008 / See benefits AND possible harm', '''
        FUTURE REALITY / I1@1 candidate change / predictions, not observations
        +-- CHANGE -------------------------------------------------------------+
        | Freeze active validation; reserve one urgent slot in the next release. |
        | Daily triage; timely acknowledgement; existing emergency path retained.|
        +---------------------+----------------------------+--------------------+
                              |                            |
                     expected benefit                possible adverse path
                              v                            v
        +--------------------------------------+ +--------------------------------------+
        | Fewer interruptions / less rework    | | Urgent work waits for the next slot |
        +------------------+-------------------+ +------------------+-------------------+
                           | ALL                                | ALL
        +--------------------------------------+ +--------------------------------------+
        | Saved time usable before release;   | | Wait exceeds legitimate need;       |
        | standard work ready; no other delay | | emergency path cannot serve it      |
        +------------------+-------------------+ +------------------+-------------------+
                           v prediction                         v prediction
        +--------------------------------------+ +--------------------------------------+
        | More standard work within 3 days    | | An urgent customer need goes unmet  |
        +--------------------------------------+ +--------------------------------------+
        Harm remains open: capacity, severity and emergency-path feasibility unknown.
        DECISION / What guardrail and response would make a bounded trial acceptable?
        [Inspect benefit]  [Inspect harm]  [Trace to goal]  [Other moves]
        '''))
    add(prose('''ACTION: Maya chooses Actions > Coaching > Direct help. Preference saved; no call or revision. In Response she types: Give me a concrete bounded pilot. Queue size, incident mix and change complexity vary; do not claim this isolates a cause.
EVENT semantic in009 r0011 question009
'''))
    add(frame('S11', 'r0011', 'question009 / Choose a bounded pilot', '''
        RECOMMENDATION / a two-week operational trial, with several interacting changes
        Trial the freeze + reserved urgent slot + 09:30 daily triage for Oct 5-16.
        Keep the existing critical-incident emergency path.

        +-- FORECAST / propose before results ---+ +-- PROTECT ------------------------+
        | >=70% standard pilot changes deploy   | | Rollback <=5% deployed pilot cohort |
        | within 3 business days                | | After-hours <=8 engineer-hours/week |
        +---------------------------------------+ | Urgent acknowledgement >=95%/4h     |
                                                  +-------------------------------------+
        Log release-ready/deployment times, queue size, change type, urgent requests,
        interruptions, rechecks, emergency-path use and rule exceptions.
        Escalate any breach to an agreed owner; do not expand before review.

        LIMIT / acknowledging a request does not establish that its need was met.
        Historical September comparison will not isolate this policy's effect.
        DECISION / Which version are you willing and authorized to run?
        Specify owner, dates, preparation, safeguards and stopping conditions.
        [Use this as a draft]  [Change the proposed plan]  [Inspect the harm]
        '''))
    add(prose('''ACTION: Maya chooses Use this as a draft (local form). She fills Owner: Maya; pilot Oct 5-16; review Oct 19; scope standard Payments changes release-ready during the window. She retains the 70% forecast, <=5% rollback, <=8h in EACH week and >=95% urgent acknowledgement within four business hours. September 12/30 is a historical baseline. Escalate breaches to Maya; pause expansion until review. Use emergency handling for a critical incident and log it. Record urgent need served or unserved; numeric fulfillment bound unknown. Maya states authority to run this bounded trial and pause expansion. Before Oct 5 name triage owner/backup and rehearse response, escalation and emergency handling. Roles must demonstrate all three before start. She activates Save forecast - asks consultant to structure this input. Saving a forecast is distinct from committing to run it.
EVENT semantic in010 r0012 question010
'''))
    add(frame('S12', 'r0012', 'question010 / Original pilot forecast saved', '''
        P1@1 / saved prospectively Oct 2 / proposed, not yet committed to run
        OWNER Maya | Oct 5-16 | Review Oct 19 | no reminder scheduled
        Scope: standard Payments changes marked release-ready Oct 5-16.
        Forecast: >=70% within 3 business days. September baseline: 12/30 = 40%.
        Cohort rule: follow every eligible change through its full 3-day window.
        Rollback denominator: deployed eligible changes; no deployment = pending.
        Acknowledgement denominator: urgent requests received during pilot.
        Protect: rollback <=5%; after-hours <=8h EACH week; acknowledgement >=95%/4h.
        Calendar: Mon-Fri, 08:00-18:00, Europe/Berlin; excluded closures: none stated.
        Oct 19 review flags immature outcomes pending and schedules their data check.
        Escalate any breach to Maya; no expansion before review.
        Emergency path allowed for critical incidents; record use, not automatic failure.
        Urgent-need fulfillment is observed separately; numeric bound UNKNOWN.

        +-- READY TO RUN? ------------------------------------------------------+
        | Roles named: not started | Roles demonstrate response: unknown         |
        | Logging operational: unknown | Stop authority: Maya declares it        |
        +-----------------------------------------------------------------------+
        DECISION / Can this version be implemented before its trial window?
        [Preparation map]  [Immediate action]  [Original forecast]  [Record reliance]
        [Correct the record]  Other participants' agreement remains unknown.
        '''))
    add(prose('''ACTION: Maya opens Preparation map locally. The prerequisite and transition fragments were authored with the question; browsing them makes no consultant call.
'''))
    add(frame('S13', 'r0012', 'Preparation / Required states', '''
        PREREQUISITE TREE / P1@1 / states that must hold, not a task checklist
        +-- Pilot operates as specified ----------------------------------------+
        | requires ALL the states below; sufficiency of this set is still open  |
        +--------------+-----------------------+------------------+-------------+
                       |                       |                  |
        +-------------------------+ +-----------------------+ +------------------------+
        | IO1 Roles acknowledged  | | IO2 Logs operational  | | IO3 Roles demonstrate  |
        | owner + backup          | | timestamps + scope    | | response + escalation  |
        +-------------------------+ +-----------------------+ | + emergency handling   |
        | Obstacle: no cover      | | Obstacle: missing     | +------------------------+
        | Criterion: both roles   | | records               | | Obstacle: ambiguous    |
        | explain authority       | | Criterion: one sample | | operating rule         |
        | Attainment: unknown     | | change + request      | | Criterion: demonstrate |
        +-------------------------+ | correctly logged      | | all 3 cases correctly  |
                                    | Attainment: unknown   | | Attainment: unknown    |
                                    +-----------------------+ +------------------------+

        IO3 requires IO1; IO1 and IO2 can be prepared in parallel.
        The connector above means requires, not causes. Unknown is not a green check.
        Completing a meeting does not establish that either role understands the rule.
        [Inspect IO1]  [Inspect IO2]  [Inspect IO3]  [Actions that may create these states]
        ''', focus='Preparation map', view='Reasoning', live='question010'))
    add(prose('''ACTION: Maya selects IO1 and opens Actions that may create these states. Same revision, local.
'''))
    add(frame('S14', 'r0012', 'Immediate action / Why it should work', '''
        TRANSITION TREE / T1@1 expected to create IO1 / a proposed causal step
        NEED: a legitimate, understood response and escalation rule before the pilot.
        +-- ALL ----------------------------------------------------------------+
        | REALITY: triage response and cover are not yet assigned.               |
        | ACTION: Maya names owner + backup, reads back rule and rehearses it.   |
        | CONDITIONS: Maya has stated authority; both roles participate;         |
        | wording resolves their authority and response questions.              |
        +----------------------------------+------------------------------------+
                                           | LT1: predicted effect
                                           v
                    +-------------------------------------------------+
                    | IO1 Roles acknowledge who responds/escalates    |
                    +-------------------------------------------------+
        OBSERVE / ask both roles to explain responsibility and backup cover.
        FAILURE / if either is unclear, revise and rehearse before starting.

        Action execution: NOT STARTED      Expected state: UNKNOWN
        Separate records. A completed action cannot set attainment automatically.
        DECISION / What happened when you tried the preparation?
        [Record completed action - asks consultant]  [Record observation separately]
        ''', focus='Immediate action', view='Actions', live='question010'))
    add(prose('''ACTION: Esc to the question. Maya answers: I have named the triage owner and backup and walked them through the draft. The rehearsal has not happened, and I have not checked the logs yet.
EVENT semantic in011 r0013 question011
'''))
    add(frame('S15', 'r0013', 'question011 / Observe readiness', '''
        PREPARATION RECEIPT / Maya's report; no organizational action executed here

        +-- ACTION ----------------------------+  +-- EXPECTED STATE -------------------+
        | Owner/backup named; rule read back   |  | Roles can explain and apply rule    |
        | Execution: COMPLETED as reported    |  | Attainment: UNKNOWN                 |
        +-------------------------------------+  +-------------------------------------+
                completed action  =/=  observed effect  =/=  pilot improvement

        Original P1@1 forecast and dates are unchanged.
        IO2 logging operational: unknown. IO3 demonstration: unknown.
        DECISION / Are the required states attained before Oct 5?
        What does the rehearsal and sample log check actually show?

        [Original forecast]  [Preparation]  [Observation fields]
        '''))
    add(prose('''ACTION: Maya answers on Oct 2: Both roles correctly explained who responds and when to escalate. They demonstrated acknowledgement with no deployment estimate, a request needing backup cover and a critical incident requiring the existing emergency path. All three cases were correct after a wording clarification, which we read back. One sample change and one sample request were correctly logged with timestamps and scope. This is a rehearsal report, not a pilot result.
EVENT semantic in012 r0014 question012
'''))
    add(frame('S16', 'r0014', 'question012 / Decide on this exact trial', '''
        READY STATES / reported rehearsal, not proof of live performance
        IO1 owner/backup authority explained: MET according to Maya's report.
        IO2 sample change + request logged: MET according to Maya's report.
        IO3 all three response cases demonstrated: MET according to Maya's report.

        +-- P1@1 / ORIGINAL FORECAST --------------------------------------------+
        | Oct 5-16 | >=70% standard changes within 3 business days               |
        | Rollback <=5% | after-hours <=8h EACH week | urgent ack >=95%/4h        |
        | Escalate to Maya; no expansion before Oct 19 review                    |
        +-----------------------------------------------------------------------+
        Reliance: unrecorded. Authority: Maya's declaration; not independently verified.
        L3@1 remains provisional. Leo's belief remains DISPUTED.
        DECISION / Will you run this exact bounded version?
        [Record reliance on P1@1]  [Revise forecast - asks consultant]  [Leave undecided]
        Record reliance is local; it records a decision, not execution or consensus.
        '''))
    add(prose('''ACTION: Maya opens Record reliance on P1@1. The panel repeats the exact window, forecast, safeguards and actor, with no substantive value preselected. She selects Will run this bounded test and activates Record reliance.
EVENT local r0015 target=P1@1 dimension=reliance value=will_run actor=Maya
Receipt: r0015 saved. Maya will run P1@1. Leo's dispute unchanged; no group agreement inferred. No consultant call. Live the current question now uses its stored continuation: run P1 and return with observations on Oct 19.
ACTION: Maya opens Goal from the sidebar to check how this trial relates to the system goal.
'''))
    add(frame('S17', 'r0015', 'Goal / What success requires', '''
        GOAL TREE / partial requirements / current goal G1@1
        +-- G1 -----------------------------------------------------------------+
        | >=80% of Oct 1-30 release-ready Payments changes deploy within 3 days. |
        | Protect rollback <=5%; after-hours <=8h in each week.                  |
        +---------------------+----------------------+--------------------------+
                       requires?                requires?
        +------------------------------------+ +---------------------------------------+
        | Adequate usable validation and     | | Feasible release access before each   |
        | recovery time for the due changes  | | change's three-day deadline            |
        +------------------------------------+ +---------------------------------------+
        Warrant: these changes need completed validation and an eligible release.
        These requirements are proposed in this scope. Others are not yet mapped.
        Freezing an active release is a method to test, not itself a necessary condition.

        TRACE / P1@1 tests I1@1; I1 addresses interruption/rework; that route threatens G1.
        Typed trace references are not causal arrows between tools.
        PILOT >=70%  =/=  SYSTEM GOAL >=80%  |  neither is yet an observed result.
        [Inspect requirement]  [Trace P1 to G1]  [Return to question]
        ''', focus='Goal', view='Goal', live='question012'))
    add(prose('''ACTION: Actions > Export portable commons > path ./deploy-flow-before-pilot.reasoncase > Export. Local receipt: exported r0015 with ancestry, source inputs, exact positions, P1 original forecast and cursor. Actions > Save and quit returns to the shell and releases the writer lock.
$ reason-commons inspect ./deploy-flow-before-pilot.reasoncase --offline
Offline read-only inspection: r0015; original P1 forecast; Maya relies on P1@1; Leo disputes L3@1. Schema, references, ancestry and content hashes pass. This command does not run the consultant.
Monday, October 19, 2026 - the following outcomes are simulated.
$ reason-commons resume ./deploy-flow-case
'''))
    add(frame('S18', 'r0015', 'question012 / Resume and review P1', '''
        WELCOME BACK / saved state restored; no consultant call
        P1@1 original forecast stays pinned while you record results.
        +-------------------------------+---------------------------------------+
        | Delivery                      | >=70% within 3 business days          |
        | Rollback                      | <=5% deployed eligible cohort         |
        | After-hours                   | <=8 engineer-hours EACH week          |
        | Urgent acknowledgement        | >=95% within 4 business hours         |
        +-------------------------------+---------------------------------------+
        Window Oct 5-16 | owner Maya | review Oct 19 | no reminder scheduled
        Preparation: reported met. Pilot execution and effects: awaiting observations.
        System goal: >=80% October cohort; end-of-month attainment not yet known.
        DECISION / Keep, change or stop this trial?
        Supply outcomes, whether the rule was followed and comparison limitations.
        Do any eligible changes still lack their full three-day follow-up?
        [Original forecast]  [Outcome fields]  [Sources]  [Other moves]
        '''))
    add(prose('''ACTION: Maya enters: Pilot ran Oct 5-16. Freeze followed; 09:30 triage on all ten working days; urgent slot available each release window; one Sev-1 used the emergency path. All 24 eligible standard changes have complete follow-up and reached production; 18 within three business days (75%). One rolled back (1/24). After-hours 7h in week one and 8h in week two. Ten urgent requests; nine acknowledged within four business hours (90%). The late one waited almost seven hours for an engineer's deployment estimate. Queue smaller in week two; broadly similar mix but one fewer large migration than September. We escalated the acknowledgement miss and did not expand. Urgent need fulfillment has not been assessed consistently; retain it as unknown.
EVENT semantic in013 r0016 question013
'''))
    add(frame('S19', 'r0016', 'question013 / Review the unchanged forecast', '''
        ! BREACH / urgent acknowledgement 9/10 = 90%, below original 95% bound
        Do not expand. Escalated to Maya according to her report.

        MEASURE                  ORIGINAL P1@1                 REPORTED RESULT
        -----------------------  ----------------------------  ---------------------------
        Within 3 business days   >=70%; September 12/30 = 40%   18/24 = 75%   SUPPORTED
        Rollback                 <=5% deployed pilot cohort    1/24 = 4.2%   WITHIN BOUND
        After-hours EACH week    <=8 engineer-hours            7h; 8h        WITHIN BOUND
        Urgent acknowledgement   >=95% within 4 business hours  9/10 = 90%    BREACH

        P1 forecast saved Oct 2: unchanged. Scope/denominators above match the report.
        System G1 >=80% October cohort: NOT DEMONSTRATED; pilot target is different.
        Fidelity: freeze + ten triages + urgent slot reported; emergency use logged.
        Lower queue, migration mix and simultaneous changes limit causal attribution.
        Leo's L3@1 dispute remains. Customer need fulfillment remains UNKNOWN.

        DECISION / What must change before another bounded trial?
        Why did the unacknowledged request wait?
        [Inspect breach]  [Original P1]  [Evidence and limits]  [Compare H1/H2]
        ''', summary='! P1 acknowledgement BREACH 90% <95% | Goal >=80% not demonstrated | No expansion'))
    add(prose('''ACTION: Before answering, Maya opens Inspect breach. This selection does not erase the delivery result or change the forecast.
'''))
    add(frame('S20', 'r0016', 'Breach / Follow the adverse path', '''
        NEGATIVE BRANCH / a reported acknowledgement failure, separate from need fulfillment
        +-- ALL / NB2@1 --------------------------------------------------------+
        | Support waits for a firm deployment estimate before acknowledging.    |
        | Estimate remains unavailable beyond the four-business-hour bound.     |
        +----------------------------------+------------------------------------+
                                           | proposed mechanism from report
                                           v
                       +-----------------------------------------+
                       | Acknowledgement sent almost 7h later    |
                       | This request misses the 4h protection   |
                       +-----------------------------------------+
        P1 proposed >=95% timely acknowledgements. Reported result: 9/10 = 90%.
        This mechanism does not settle whether the customer's urgent need was served.
        Earlier NB1 (urgent work waits) also remains: fulfillment data UNKNOWN.
        Acknowledgement and fulfillment are separate branches and observations.
        [Source input]  [NB1 urgent need]  [Return to question]
        ''', focus='Breach', view='Reasoning', live='question013',
        summary='! P1 acknowledgement BREACH 90% <95% | Original P1 preserved | No expansion'))
    add(prose('''ACTION: Esc returns to the same question. Maya answers: Support believed a useful acknowledgement needed a firm fix time. While Engineering investigated, nothing was sent. We can acknowledge receipt, name an owner and give the next-update time without inventing a deployment promise.
EVENT semantic in014 r0017 question014
'''))
    add(frame('S21', 'r0017', 'question014 / Change the assumption and test it', '''
        ASSUMPTION TO CHALLENGE / Useful acknowledgement requires a firm deployment estimate.
        Proposed communication change I2@1: acknowledge receipt; name owner;
        give next-update time while investigation and deployment decision continue.

        +-- EXPECTED BENEFIT ------------------+  +-- STILL AT RISK --------------------+
        | Estimate missing no longer blocks    |  | Timely acknowledgement can coexist |
        | acknowledgement before 4h            |  | with an unserved urgent need        |
        +--------------------------------------+  +-------------------------------------+
        Retain freeze, urgent slot, triage, emergency path and existing protections.
        Observe acknowledgement TIME and whether the agreed customer NEED was served.
        A numeric acceptable fulfillment bound has not been agreed.

        DECISION / Who will own a follow-up with what prediction and review window?
        [Draft follow-up]  [Inspect original breach]  [Ask a different question]
        ''', summary='! P1 historical breach retained | Follow-up proposed | No expansion'))
    add(prose('''ACTION: Switch declared speaker to Leo. Leo enters: I will own and run P2 October 20-30, review October 30. Support acknowledges within four business hours, names owner and next-update time without requiring a deployment estimate. Keep all release-flow rules, emergency path, rollback <=5% and after-hours <=8h each week. Predict >=95% timely acknowledgements and >=70% standard delivery within three business days. Record each agreed customer need and whether it was served, plus exceptions. Numeric fulfillment bound remains unknown. Escalate an unserved urgent need or existing guardrail breach to me; pause expansion until review. I have authority for this bounded follow-up. That does not mean I agree with L3. At the October 30 review mark any immature delivery outcomes pending; review the complete cohort after its three-day window closes.
EVENT semantic in015 r0018 question015
'''))
    add(frame('S22', 'r0018', 'question015 / Follow-up saved; open issues remain', '''
        P2@1 / prospective follow-up / Leo's explicit bounded commitment
        Oct 20-30 | review Oct 30; incomplete three-day windows pending, not failures
        Owner/stop authority: Leo declares both. No reminder scheduled.
        Acknowledge receipt + owner + next-update time; no final estimate required.
        Retain freeze, reserved urgent slot, daily triage and existing emergency path.
        Forecast: urgent acknowledgement >=95%/4h; standard delivery >=70%/3 days.
        Protect: rollback <=5% deployed eligible cohort; after-hours <=8h EACH week.
        Same calendar and cohort rules as P1; follow immature outcomes to completion.
        Record agreed urgent customer need and whether it was served; bound UNKNOWN.
        Escalate any unserved urgent need or guardrail breach; no expansion before review.

        +-- WHAT THIS DECISION DOES NOT SETTLE ----------------------------------+
        | P1 acknowledgement breach remains recorded. Original forecast unchanged.|
        | Leo still DISPUTES L3@1. No causal conclusion or group agreement inferred.|
        | System October goal is not yet demonstrated. P2 effects not observed.   |
        +-----------------------------------------------------------------------+
        NEXT / Run this bounded follow-up; return with comparable observations.
        [Original P1 + outcome]  [P2 forecast]  [Open issues]  [History]
        ''', speaker='Leo', summary='P1 breach retained | P2@1 committed by Leo | System goal not yet demonstrated'))
    add(prose('''ACTION: Leo opens History, selects r0016, then Return to question. The selected revision is historical; the live response target stays Follow-up saved. Actions > Consultant calls shows 15 completed semantic calls. All inspection, navigation, preference changes, export, quit and resume made zero calls. The three structured local decisions created revisions without consultant responses.
The next two screens demonstrate resize of saved L3@1 at r0018, with the question and its draft retained. They are the SAME inference as S05; the current breach/dispute remain visible. They are not new sessions or additional calls.
'''))
    add(frame('S23', 'r0018', 'L3@1',
        '        L3 hypothesis / Leo DISPUTES / H2 reversal also unresolved\n' +
        joint_inference_diagram(compact=True),
        width=80, height=24, nav=False, focus='L3', live='question015', speaker='Leo',
        summary='P1 breach retained | L3 disputed | Goal >=80% not demonstrated',
        buttons='[Evidence]  [Compare H2]  [Return]', footer='Tab controls  Enter open  Esc back  F1 Help  Actions'))
    add(frame('S24', 'r0018', 'L3', '''
        L3 hypothesis; Leo disputes it.
        IF ALL (3 premises):
        1 Validation interrupted;
          rechecks needed for this change.
        2 Net unrecovered recheck time
          exceeds release-cutoff slack.
        3 No eligible later release before
          its three-business-day deadline.
        THEN standard change misses target.
        H2: delay may cause escalation.
        [Evidence] [Compare] [Explain]
        ''', width=40, height=24, nav=False, focus='L3', live='question015', speaker='Leo',
        summary='P1 breach retained; L3 disputed', buttons='[Return] [Views] [Actions]',
        footer='Tab  Enter open  Esc back  Help'))
    add(prose('''ACTION: Restoring 120x40 restores the same selected L3 version, semantic scroll anchor, response draft and focus. No commons change. Actions > Export portable commons > ./deploy-flow-after-review.reasoncase > Export; Actions > Save and quit.
$ reason-commons inspect ./deploy-flow-after-review.reasoncase --offline
Offline inspection: r0018. P1 delivery 18/24 = 75% supports its original >=70% forecast; P1 acknowledgement 9/10 = 90% breaches its original >=95% bound. Full October goal remains unestablished. P2@1 prospective; owner Leo; Oct 20-30. Fulfillment bound unknown; Leo disputes L3@1; causal attribution provisional. Forecasts, observations, ancestry, references and hashes preserved.
CONSULTANT CALLS 15: in001 through in015; all completed in this specimen.
18 reasoning revisions = 15 semantic commits + 3 structured local decisions.
No deployment, notification, assignment or reminder was executed by the application.
'''))
    return ''.join(out)


def build_mvp():
    QUESTION_TITLES.clear()
    # The v1 narrative as well as its frames fits an 80-column terminal.
    def prose80(text):
        return prose(text, width=78)
    out = [prose80('''REASON COMMONS / FIRST-RELEASE TUI JOURNEY
Delivery profile: p2 cumulative v1; deterministic adapter acceptance specimen.
Fictional Forge commons; an authored specimen, not a recording of the application. Frames are 80x24. V1 has no structured graph browser, participant stance registry or formal tree authoring. Its persistent workspace, literal response editor, visible local controls, proposals that wait for the operator and forecast/result comparison ARE required from p1-p2. No typed commands are needed inside this session.
$ reason-commons new forge --store ./forge-v1 --speaker Sam
EVENT start r0000
''')]
    def s(sid, rev, title, body, **kw):
        return frame(sid, rev, title, body, width=80, height=24, nav=False,
                     speaker='Sam', case='forge',
                     summary=kw.pop('summary', 'Goal >=90% October delivery | Protect overtime <=20h/wk; defects <=2%'),
                     buttons='[Send]  [Explain this]  [Other moves]  [Views]  [Actions]', **kw)
    out.append(s('M01', 'r0000', 'Start', '''
        Welcome to Reason Commons.
        What is happening, and what would count as better?
        You can begin in ordinary words. Unknown measures can stay open.

        [How this works]  [Open a commons]
        Send asks the consultant. Browsing and saved explanations stay local.
        Enter adds a line. Tab to Send, then Enter sends once.
        All typing, including 5, ?, q and punctuation, is literal in Response.
        ''', summary='Goal unknown | Safeguards unknown | No test'))
    out.append(prose80('''ACTION: Sam enters: Goal: >=90% of October due orders on time, original promised dates; review October 30. September 32/50 = 64%. Protect overtime <=20h each week and defects <=2% of inspected units each week. These are my reported records. Tab to Send, Enter.
EVENT semantic in001 r0001 question001
'''))
    out.append(s('M02', 'r0001', 'question001 / Choose a test', '''
        PROPOSED from your words / waiting for you; not yet in the model
          Goal: >=90% October due orders on original dates; review Oct 30
          Baseline: September 32/50 = 64%, reported by Sam
          Protect: overtime <=20h EACH week; defects <=2% inspected units/week
        [Accept all]  [Backlog]   Accepting admits it; it does not prove it.

        DECISION / What change can you authorize and observe?
        Choose a small trial with an original forecast we can review later.
        Other people's agreement and authority remain unknown.
        [Goal]  [Reported sources]  [Explain this]  [Other moves]
        ''', live='question001', summary='Goal proposed, waiting | Safeguards proposed | No test'))
    out.append(prose80('''ACTION: Sam Tabs to Accept all and presses Enter. The goal with its baseline and protections enters the model in one local revision; no consultant call. The band now shows the accepted goal.
EVENT local r0002 target=G1@1 dimension=membership value=accepted actor=Sam
ACTION: Sam types a draft "5 requests?", then Tabs to Other moves and presses Enter. This menu keeps the question and draft. No consultant call has been made.
'''))
    out.append(frame('M02A', 'r0002', 'Other moves', '''
        Choose a route. Nothing is sent until you activate an item.

        > Understand why this question    LOCAL: saved explanation
          Inspect goal and safeguards     LOCAL: saved records
          Help plan an observation        ASKS CONSULTANT
          Give direct advice              ASKS CONSULTANT
          Ask a different question        ASKS CONSULTANT
          Leave this question open        LOCAL: retains draft

        Arrows select; Enter activates. Esc returns without a choice.
        Your draft stays attributed to Sam and the current question.
        ''', width=80, height=24, nav=False, speaker='Sam', case='forge',
        focus='Other moves', live='question001', draft='5 requests?',
        summary='Goal >=90% October delivery | Protect overtime <=20h/wk; defects <=2%',
        buttons='[Return to question]  [Help]  [Views]  [Actions]'))
    out.append(prose80('''ACTION: Sam activates the selected Understand why this question item. The local Explain this view says: A bounded trial and prospective forecast let you compare results later, while protecting overtime and defects. The question asks for work you can authorize. Esc restores the same question, draft and cursor; no call. Sam replaces the draft and sends:
I have authority to name a triage owner and backup before Oct 5. Rehearse two requests; both roles must explain response and escalation before start. Pilot daily triage Oct 5-16; review Oct 19. Predict delivery >=80%, urgent acknowledgement >=95% within 24h. Retain overtime/defect bounds. Record original dates, mix, suppliers and rule use. Stop expansion on any breach. If either role cannot explain escalation, resolve that before start. Urgent fulfillment is a separate unknown.
EVENT semantic in002 r0003 question002
'''))
    out.append(s('M03', 'r0003', 'question002 / Prepare P1@1', '''
        PROPOSED / waiting for you: test P1@1 and its preparation action
        P1@1 forecast, saved before results / Oct 5-16; review Oct 19
        Forecast: delivery >=80%; urgent acknowledgement >=95% within 24h.
        Protect overtime <=20h EACH week; defects <=2% inspected units/week.
        Owner and stop authority: Sam declares both; no expansion on breach.
        ACTION: name owner/backup and rehearse two requests before Oct 5.
        EXPECTED STATE: both roles can explain response and escalation.
        Execution: NOT STARTED | expected state: UNKNOWN | no reminder scheduled
        Urgent-need fulfillment: UNKNOWN.
        [Accept all]  [Backlog]  [Original forecast]  [Sources]
        DECISION / What happens when you perform this preparation?
        ''', live='question002'))
    out.append(prose80('''ACTION: Sam activates Accept all. P1@1 and its action enter the model; one local revision, no call.
EVENT local r0004 target=P1@1,A1@1 dimension=membership value=accepted actor=Sam
ACTION: Sam opens Actions > Accept proposals automatically and confirms. From now on a reply's ready proposals enter the model with the reply, recorded as accepted under Sam's setting, and each can be undone from History. Proposals already waiting would keep waiting; none are. No call.
EVENT local r0005 target=case dimension=acceptance value=automatic actor=Sam
ACTION: Sam answers: I named owner and backup today. Rehearsal has not happened; I do not know whether they can explain the rule.
EVENT semantic in003 r0006 question003
'''))
    out.append(s('M04', 'r0006', 'question003 / Observe the result', '''
        PREPARATION / reported by Sam; added under Sam's setting, can be undone
        +-- ACTION ---------------------+ +-- EXPECTED STATE --------------------+
        | Roles named: COMPLETED        | | Rule understood: UNKNOWN             |
        +-------------------------------+ +--------------------------------------+
        Action completed; result awaiting observation.
        Naming roles does not establish understanding or better delivery.
        P1 original forecast and G1 goal are unchanged.
        DECISION / Does rehearsal establish readiness before the pilot?
        What did both roles demonstrate?
        [P1 forecast]  [Reported sources]  [History]
        ''', live='question003'))
    out.append(prose80('''ACTION: Actions > Export > ./forge-v1-before-review.reasoncase. Actions > Save and quit. Local export and cursor save, no call.
$ reason-commons resume ./forge-v1
M04 is restored at r0006 with Observe the result as the current question. Goal, safeguards and P1 remain pinned; preparation state still unobserved. No consultant call.
ACTION: Sam submits: Both roles correctly explained response and escalation in the two rehearsals. Pilot then ran as planned. Fifty due orders, 40 on time. Overtime 18h then 19h; defects 1/50 then 0/50 inspected units. Urgent acknowledgements 18/20 within 24h. Original dates unchanged; similar mix but steadier suppliers. This does not isolate triage as cause.
EVENT semantic in004 r0007 question004
'''))
    out.append(s('M05', 'r0007', 'question004 / Review P1', '''
        ! Urgent acknowledgement BREACH: 18/20 = 90%, original bound >=95%
        MEASURE             ORIGINAL             REPORTED RESULT
        Delivery            >=80%                40/50 = 80% supported
        Acknowledgement     >=95% within 24h     18/20 = 90% BREACH
        Overtime EACH week  <=20h                 18h; 19h within bound
        Defects EACH week   <=2% inspected units  1/50 = 2%; 0/50 = 0%
        G1 goal >=90% remains unmet. Supplier changes limit attribution.
        Rehearsal state: met by report. Original P1 unchanged; do not expand.
        DECISION / What delayed the two acknowledgements?
        [Original forecast]  [Source report]  [Other moves]
        ''', live='question004', summary='! Acknowledgement BREACH 90% <95% | Goal >=90% remains unmet'))
    out.append(prose80('''ACTION: Sam answers: They waited for supplier dates. The owner thought the first response must promise a final date. We can acknowledge receipt before that date is known.
EVENT semantic in005 r0008 question005
'''))
    out.append(s('M06', 'r0008', 'question005 / Adapt the trial', '''
        RECOMMENDATION / separate receipt acknowledgement from date commitment
        Expected effect: supplier uncertainty no longer blocks acknowledgement.
        Need: respond promptly without inventing a delivery promise.
        Keep the prior protections; measure urgent-need fulfillment separately.
        No numeric fulfillment bound has been agreed.
        P1 breach remains; original forecast unchanged; no causal proof.
        DECISION / Name follow-up owner, forecast, window and stopping response.
        [Draft follow-up]  [Original P1]  [Ask a different question]
        ''', live='question005', summary='! P1 acknowledgement breach retained | Follow-up proposed'))
    out.append(prose80('''ACTION: Sam answers: I will run the follow-up Oct 20-30; review Oct 30. Acknowledge receipt within 24h without waiting for supplier dates. Predict delivery >=80% and acknowledgement >=95%/24h. Retain overtime <=20h each week and defects <=2% weekly; record mix, suppliers, rule use and whether urgent needs were served. Stop expansion and escalate an unserved need or safeguard breach to me.
EVENT semantic in006 r0009 question006
'''))
    out.append(s('M07', 'r0009', 'question006 / Follow-up saved', '''
        P2@1 prospective / Sam's explicit bounded commitment / Oct 20-30
        Review Oct 30; no reminder scheduled.
        Predict delivery >=80%; acknowledgement >=95% within 24h.
        Protect overtime <=20h each week; defects <=2% inspected units/week.
        Record whether urgent needs were served; numeric bound remains UNKNOWN.
        Escalate unserved need or breach to Sam; no expansion before review.
        P1 original prediction and 90% BREACH remain unchanged.
        G1 >=90% remains unmet; P2 effects not observed.
        NEXT / Run bounded P2, then return with observations.
        [P2 forecast]  [P1 outcome]  [Goal]  [History]
        ''', live='question006', summary='P1 breach retained | P2 committed | Goal >=90% remains unmet'))
    out.append(prose80('''ACTION: Actions > Export portable commons > ./forge-v1-after-review.reasoncase; Actions > Save and quit. No call.
CONSULTANT CALLS 6: in001 through in006.
9 reasoning revisions = 6 semantic commits + 3 structured local decisions.
'''))
    return ''.join(out)


def build_review():
    QUESTION_TITLES.clear()
    out = [prose('''ILLUSTRATIVE CROSS-TOOL TUI CORRECTION AND ACTION REVIEW
Delivery profile: p5 cumulative roadmap; independent fictional fixture.
The r0000 fixture contains goal G1, CRT L1@1, Cloud A4@1, FRT I1@1, prerequisite IO2@1 and action T1@1. Dependencies are stored exact references, not discovered by a renderer. Frames are 120x40; keyboard and focus follow the main TUI specimen.
$ reason-commons resume ./setup-review-fixture
EVENT start r0000
''')]
    def s(sid, rev, title, body, **kw):
        return frame(sid, rev, title, body, speaker='Sam', case='setup',
                     summary='Goal: timely delivery + agreed throughput floor | Reviews and uncertainty remain visible', **kw)
    out.append(s('R01', 'r0000', 'Start / Challenge the setup route', '''
        CURRENT CLAIM / L1@1: every urgent insertion adds setup time (hypothesis).
        DECISION / What counterexample would change this explanation or admission rule?
        [Inspect L1]  [Sources]  [Cross-tool references]

        Stored future I1@1: check setup/delivery consequences before admission.
        Stored Cloud A4@1: every sequence change jeopardizes due work (proposed).
        IO2@1 setup information adequate: UNKNOWN. T1@1 authority meeting: NOT STARTED.
        These exact formulations can be inspected; none is established by its placement.
        '''))
    out.append(prose('''ACTION: Sam submits: A same-setup insertion added no setup time. Qualify the causal route to insertions adding setup changes. We still have late orders. Review whether the admission rule can allow setup-neutral jobs.
EVENT semantic in001 r0001 question001
'''))
    out.append(s('R02', 'r0001', 'question001 / Correction and dependent review', '''
        CHANGE / source in001, Sam's report / late-order report UNCHANGED
        +-- BEFORE / L1@1 ----------------------+ +-- AFTER / L1@2 -----------------------+
        | Every urgent insertion adds setup time| | Only insertions adding setup changes |
        | Hypothesis                            | | use this setup-loss route.            |
        +---------------------------------------+ +---------------------------------------+
        A setup-neutral insertion can still consume PROCESSING time: separate route.

        +-- REGISTERED CONSEQUENCES / current r0001 -----------------------------+
        | L1@2  ---- used by ---- Cloud A4@1: REVIEW NEEDED                      |
        |       ---- used by ---- FRT I1@1:   REVIEW NEEDED                      |
        |       ---- used by ---- PRT IO2@1:  REVIEW NEEDED                      |
        +-----------------------------------------------------------------------+
        Trace labels are dependencies, not causal arrows. List is not exhaustive reality.
        Past reviews remain on OLD versions. No belief, assent or test reliance transfers.
        T1 execution unchanged; pilot effects UNOBSERVED; no delivery gain established.
        DECISION / Can admission distinguish setup-neutral work AND its processing load?
        What information and accuracy would support that decision?
        [Compare versions]  [Review Cloud]  [Review future]  [Review prerequisite]
        '''))
    out.append(prose('''ACTION: Sam opens Compare versions, then Esc. Same question, draft and scroll restored; no call. He submits: Sponsor held the authority meeting and named owner/backup. Record T1 completed. We have not checked that roles understand escalation or can apply the admission rule.
EVENT semantic in002 r0002 question002
'''))
    out.append(s('R03', 'r0002', 'question002 / Observe what the action achieved', '''
        ACTION T1@1 / reported by Sam
        +------------------------------------+  +---------------------------------------+
        | Meeting and naming: COMPLETED     |  | Roles acknowledge authority: UNKNOWN |
        +------------------------------------+  +---------------------------------------+
        Completion cannot set the expected state automatically.
        Observe: both roles explain response, escalation and backup cover.
        If either fails: clarify authority and rehearse; retain the failure record.

        Setup-information adequacy remains UNKNOWN. Registered reviews remain open.
        DECISION / What did the roles demonstrate rather than merely attend?
        [Observation fields]  [Action rationale]  [Open dependent reviews]
        '''))
    out.append(prose('''ACTION: Sam submits: Both roles explained escalation correctly in rehearsal. I will run a small supervised test under my stated authority while setup accuracy remains uncertain. Retain that uncertainty and admission-rule review; do not expand on this rehearsal alone.
EVENT semantic in003 r0003 question003
'''))
    out.append(s('R04', 'r0003', 'question003 / Bounded decision under uncertainty', '''
        Authority state: MET according to reported rehearsal; real pilot UNOBSERVED.
        Sam's explicit bounded intention recorded; authority is his declaration.
        Setup accuracy: UNKNOWN. Admission-rule and dependent reviews: OPEN.
        Original claims, observations and positions remain attached to their versions.
        No belief or consensus inferred from the willingness to test.

        DECISION / Is the accuracy criterion adequate for this supervised trial?
        Specify accuracy criterion, scope and stopping observation before operation.
        A willingness to test has not filled these missing conditions.
        [Unresolved reviews]  [Original forecast]  [Exact versions]
        '''))
    out.append(prose('''ACTION: Actions > Consultant calls, then Save and quit. Local.
CONSULTANT CALLS 3: in001 through in003.
3 reasoning revisions = 3 semantic commits + 0 structured local decisions.
'''))
    return ''.join(out)


if __name__ == '__main__':
    (ROOT / 'example-tui-session.txt').write_text(build_full())
    (ROOT / 'example-mvp-session.txt').write_text(build_mvp())
    (ROOT / 'example-review-session.txt').write_text(build_review())
