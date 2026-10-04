# Reason Commons: a three-minute demo, recorded with VHS (https://github.com/charmbracelet/vhs).
#
# From the repository root:
#
#     vhs scripts/video/demo.tape
#
# It runs this checkout offline with the built-in guide, in a throwaway folder
# (see demo-env.sh), and writes docs/video/reason-commons-demo.mp4.
#
#   0:00  What it is
#   0:10  First start, and a new goal answered in ordinary words
#   1:05  A real commons: how one movement's reasoning grew, and its six trees
#   2:00  A goal a few weeks in: the forecast beside the result, and its History
#   2:30  The same goals from the command line: trees, export, plain files

Output docs/video/reason-commons-demo.mp4

Require uv

Set Shell "bash"
Set FontSize 16
Set Width 1440
Set Height 900
Set Padding 24
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 35ms
Set CursorBlink false

Hide
Type "source scripts/video/demo-env.sh && clear"
Enter
Sleep 6s
Show

# ---- 0:00  What it is -----------------------------------------------------------
Sleep 500ms
Type "# Reason Commons: see a hard problem whole, then change it one honest test at a time."
Sleep 2s
Enter
Type "# Offline, in your terminal. Everything is saved as plain files you own."
Sleep 2s
Enter
Type "reason-commons"
Sleep 600ms
Enter

# ---- 0:10  First start, and a new goal --------------------------------------------
Sleep 5s                                   # the four ways to start
Enter                                      # Start my first goal (offline guide, as Mira)
Sleep 1.5s
Type "More neighbours at our monthly meeting"
Sleep 1s
Enter
Sleep 3s                                   # the guide asks the first question

Type "More neighbours come to our monthly community meeting, without burning out the organisers."
Sleep 1s
Ctrl+S
Sleep 4s                                   # saved; the next question: how will you know?

Type "Neighbours at the meeting (sign-in sheet): now 12, aiming for 20 by March."
Sleep 1s
Ctrl+S
Sleep 4s                                   # what must not get worse?

Type "Organisers' hours stay as they are"
Enter
Type "Nobody feels guilted into coming"
Sleep 1s
Ctrl+S
Sleep 5s                                   # goal and safeguards pinned at the top

Type "Ask each regular to bring one neighbour"
Sleep 2s                                   # a draft: kept even if we quit now
Ctrl+Q
Sleep 1.5s

# ---- 1:05  A real commons ----------------------------------------------------------
Type "# Bigger problems need more than a list. Here is a real movement's shared reasoning."
Sleep 1.5s
Enter
Type "reason-commons"
Enter
Sleep 2.5s
Up 3                                       # Explore a real commons
Sleep 1s
Enter
Sleep 7s                                   # the decision it waits on, and its next action

Left
Sleep 4s                                   # one step back: who said what, and what changed
Left
Sleep 4s
Left
Sleep 4s
Right 3                                    # back to now
Sleep 1s

Ctrl+T                                     # the six trees, as they stand now
Sleep 6s
Ctrl+N
Sleep 5s
Ctrl+N
Sleep 5s
Ctrl+N
Sleep 5s
Ctrl+N
Sleep 5s
Ctrl+N
Sleep 5s
Ctrl+N                                     # all six together
Sleep 6s
Ctrl+Q
Sleep 1.5s

# ---- 2:00  A goal a few weeks in ----------------------------------------------------
Type "# Trees say what might work. A test finds out: the forecast is written before you act."
Sleep 1.5s
Enter
Type "reason-commons"
Enter
Sleep 2.5s
Down                                       # From open evening to first practice
Sleep 1s
Enter
Sleep 8s                                   # the original forecast beside the result

Ctrl+P
Sleep 1s
Type "view: history"
Sleep 1.5s
Enter
Sleep 6s                                   # every step: when, who, what changed
Ctrl+Q
Sleep 1.5s

# ---- 2:30  The command line ----------------------------------------------------------
Type "reason-commons trees ReasonCommons/first-practice --tree conflict"
Sleep 500ms
Enter
Sleep 7s

Type "reason-commons export ReasonCommons/first-practice first-practice.reasoncase"
Sleep 500ms
Enter
Sleep 1.5s

Type "clear; cd ReasonCommons/more-neighbours-at-our-monthly-meeting && ls"
Sleep 500ms
Enter
Sleep 4s

Type "cat inputs/in000003.yaml                    # your words, exactly as written"
Sleep 500ms
Enter
Sleep 5s

Type "grep draft cursor.yaml                      # and the unsent draft, waiting"
Sleep 500ms
Enter
Sleep 5s

Type "# github.com/life-itself/reason-commons-tui"
Sleep 5s
