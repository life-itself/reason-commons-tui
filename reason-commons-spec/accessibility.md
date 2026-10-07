# Accessible ordered presentation

Reason Commons has one set of human actions. The default is the spatial TUI;
`reason-commons new` or `resume` with `--accessible` selects ordered text for a
reader that cannot use alternate-screen redrawing. This is a presentation of
the same workspace, with the same records, explicit submission, attribution,
version validation and recovery. It has no command prompt or phrase parser.

Use a stable reading order: case/save/actor/view/focus, urgent status, decision,
complete question and relevant context, what the last reply proposes (each
record with its source, under "Proposed, not yet in the model"), reasoning as
relation sentences or an aligned table, local evidence/actions, Response, Send,
other destinations. The Backlog reads as an ordered list in which each entry says
what it waits for, and its Accept, Reject, Still holds and Undo controls are the
same labeled controls as in the spatial TUI.
Describe each control by label, role, consequence and current focus. Announce
focus changes and important new status once. Never announce each animation or
reprint the entire case on every keystroke. Append an explicit replacement section
on meaningful view changes; identify superseded sections so scrollback is not
mistaken for current state. An optional Repeat current view control is local.

For example, the same pilot review can read in this order:

```text
Reason Commons | forge | Sam (declared) | r0004 saved
Review P1 | Focus: Review results
Attention: urgent acknowledgement 90% against original >=95%: BREACH.
Decision: adapt the trial; expansion remains stopped.
Delivery: original >=80%; reported 40/50 = 80%. Pilot target supported.
System goal: >=90%; remains unmet.
Evidence: participant report; supplier comparability uncertain.
Controls: Inspect sources (local), Explain this (local), Return to question.
Response editor: retained draft; Enter adds a line.
Send (asks consultant), Other moves, Views, Actions, Help.
```

Tab/Shift+Tab moves to labeled controls, arrows select list entries, Enter/Space
activates them, and Esc returns while retaining the draft. Printable keys edit
Response or an explicitly focused filter. Enter in Response adds a newline;
only activating Send submits. Focus announcements must distinguish the editor
from Send. Multiline text needs no escape syntax. Selecting a list item and
activating it remains distinct from typing a number as an answer. This keyboard
model also works without color, cursor-addressed panels or Unicode borders.

Read graphs as exact typed relations: all joint premises, output, conditions,
scope, warrant, support, disagreement and alternative routes. A relation sentence
may occupy several sections; explicitly mark continuation and keep premises
reachable before judgment. Historical wording and current response target remain
distinct. Compare original forecasts with results using labeled rows when aligned
columns are unsuitable. Never reduce an adverse path to a success-only summary.

At less than 40x24 retain state and offer resize or this ordered presentation.
S49 covers narrow ordered context; S50 equivalent relation text; S51 drafts;
S54-S71 focus/selection/target behavior; S115-S120 deliberate submission, restoration
and recovery; S135-S147 decisions about proposals. The participant gates in delivery-phases.md include assistive
technology users. These requirements need implementation and actual reader tests;
a text specimen or passing document check is not evidence of accessibility.
