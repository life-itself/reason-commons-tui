"""A note for a new goal's first screen, and How this works: the workspace drawn with each part labelled.

The note sits under the answer box while a goal has no question yet. It gates nothing: the answer box keeps
focus, and typing, Send, browsing, Help and leaving work exactly as they do without it (S114; the
specification's first screen offers How this works). It goes once the first answer is sent, and Hide this
stops it on every new goal from then on. How this works is the same page wherever it opens: from the note,
from Commands and from the tour. Nothing here reads or changes a case.
"""

import textwrap

from rich.cells import cell_len, set_cell_size
from rich.console import Group
from rich.table import Table
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

# Who asks the questions, as the note and the page say it.
ASKER = {"guided": "the offline guide", "anthropic": "Claude", "lm-studio": "your local model"}
# The note's rows besides its numbered lines: the gap above it, its title and its buttons.
FRAME_ROWS = 3


def asker(provider):
    """Who asks: a provider's name for people, or words that already say who ("the built-in guide")."""
    return ASKER.get(provider, provider or "your consultant")


def welcome_lines(provider):
    """The note's four lines, for whoever asks the questions. Each fits one row of an 80-column screen."""
    who = asker(provider)
    return [f"{who[0].upper() + who[1:]} asks one question at a time, here.",
            "You answer in your own words. Enter starts a new line; Ctrl+S sends.",
            "Each reply proposes what to record; you decide what enters your goal.",
            "The top line shows your place in the loop; Views lists what's recorded."]


def numbered(lines, mark=str):
    """Numbered lines, each one's wrapped text hanging under its first word rather than under its number."""
    grid = Table.grid(padding=(0, 2, 0, 0))
    grid.add_column(no_wrap=True, style="bold")
    grid.add_column()
    for number, line in enumerate(lines, start=1):
        grid.add_row(mark(number), line)
    return grid


def numbered_rows(lines, width, mark=str):
    """How many rows ``numbered`` takes in this many columns (rich and textwrap both wrap at spaces)."""
    number = max(cell_len(mark(n)) for n in range(1, len(lines) + 1)) + 2
    return sum(len(textwrap.wrap(line, max(10, width - number))) or 1 for line in lines)


class WelcomePanel(Vertical):
    """The note: a quiet title, the numbered lines, How this works and Hide this. Its form is "full",
    "line" (just "New here?" and the two buttons, when the screen is short) or "hidden"."""

    def compose(self) -> ComposeResult:
        yield Static("NEW HERE", id="welcome-title")
        yield Static(id="welcome-lines")
        with Horizontal(id="welcome-controls"):
            yield Static("New here?", id="welcome-lead")
            yield Button("How this works", id="how-it-works")
            yield Button("Hide this", id="hide-welcome")

    def say(self, provider):
        self.lines = welcome_lines(provider)
        self.query_one("#welcome-lines", Static).update(numbered(self.lines))

    def full_rows(self, width):
        """The rows the full note takes in a column this many cells wide (its margins and padding are 2 each)."""
        return FRAME_ROWS + numbered_rows(getattr(self, "lines", welcome_lines(None)), width - 4)

    def show_form(self, form):
        self.set_class(form == "hidden", "hidden")
        self.set_class(form == "line", "line")


def sketch(width):
    """The workspace in outline, ``width`` cells wide, with each part's number on its right, as a list of
    (line, number) pairs. Drawn rather than typed so every row is exactly as wide as the others."""
    views = 13 if width >= 70 else 12
    inner = width - 4  # between "│ " and " │"
    right = width - views - 6  # the reading side, between its "│ " and the outer " │"
    pad = lambda text, size: set_cell_size(text, size)

    def full(text):
        return "│ " + pad(text, inner) + " │"

    def split(left, right_text):
        return "│ " + pad(left, views) + "│ " + pad(right_text, right) + " │"

    def ends(left_text, right_text):
        return left_text + " " * max(1, inner - cell_len(left_text) - cell_len(right_text)) + right_text

    def box(top, middle, bottom):
        line = lambda start, label, end: start + label + "─" * (right - 2 - cell_len(label)) + end
        return [line("┌", top, "┐"), "│ " + pad(middle, right - 4) + " │", line("└", bottom, "┘")]

    loop = ("● Goal ─ ○ Test + forecast ─ ○ Action ─ ○ Observe ─ ○ Review" if inner >= 62
            else "● Goal  ○ Test  ○ Action  ○ Observe  ○ Review")
    answer = box(" Answer as you ", "your own words", " Send ")
    rows = [("┌" + "─" * (width - 2) + "┐", None),
            (full(ends("Your goal's name", "You · Saved")), 1),
            (full(loop), 2),
            ("├" + "─" * (views + 1) + "┬" + "─" * (width - views - 4) + "┤", None),
            (split("VIEWS", "The question"), 3),
            (split("▸ Next step", answer[0]), None),
            (split("  Goal", answer[1]), 4),
            (split("  Trees …", answer[2]), None),
            ("├" + "─" * (views + 1) + "┴" + "─" * (width - views - 4) + "┤", None),
            (full(ends("the keys that work where you are", "Help")), 5),
            ("└" + "─" * (width - 2) + "┘", None)]
    return rows


def show_drawing(holder, room):
    """Put the widest sketch that fits ``room`` cells in ``holder``, each part's number after its row, or hide
    it on a very narrow screen."""
    width = 76 if room >= 80 else 52 if room >= 56 else 0  # and four more cells for each part's number
    holder.display = bool(width)
    if width:
        lines = []
        for line, number in sketch(width):
            text = Text(line, style="dim")
            if number:
                text.append(f" ({number})", style="bold")
            lines.append(text)
        holder.update(Group(*lines))


def explanations(provider):
    who = asker(provider)
    return ["The goal's name, who you are, and that it is saved. Everything is saved as you type.",
            "The loop: a goal, then a test with a forecast written first, the action, what happened, and a "
            "review. ● marks where you are and ✓ what is done; the goal's measure sits on the right.",
            f"One question at a time, from {who}. Views, on the left (or the Views button on a narrow screen), "
            "are everything recorded so far: the goal, the tests, the six trees, everyone's words and the history.",
            "Your answer, in your own words. Enter starts a new line; Ctrl+S sends it. What comes back is marked "
            "proposed: Accept all takes it into your goal, or it waits in Backlog for you.",
            "The keys that work where you are, then Commands, which lists everything you can do. Explain this, "
            "beside Send, says why a question is asked."]


class HowItWorksScreen(ModalScreen):
    """How this works: the workspace drawn in outline with its parts numbered, then what each part is for.
    The drawing appears only where it fits; the numbered lines say everything without it."""

    BINDINGS = [Binding("escape", "dismiss", "Close")]
    LEAD = ("Reason Commons helps you make progress on something that matters, one small step at a time, and "
            "keeps an honest record of how you got there. This is the screen you work in.")
    CLOSING = "Nothing is sent anywhere until you press Send. Everything is kept on this computer."

    def __init__(self, provider="guided"):
        super().__init__()
        self.provider = provider

    def compose(self) -> ComposeResult:
        mark = lambda n: f"({n})"
        with Vertical(id="dialog"):
            yield Label("How this works", classes="dialog-title")
            with VerticalScroll(id="how-body"):
                yield Static(self.LEAD, id="how-lead")
                yield Static(id="how-sketch")
                yield Static(numbered(explanations(self.provider), mark), id="how-parts")
                yield Static(self.CLOSING, classes="hint")
            yield Button("Close", id="close", variant="primary")

    def on_mount(self):
        self.draw()

    def on_resize(self):
        self.draw()

    def draw(self):
        """The widest drawing the dialog has room for, or none on a very narrow screen."""
        body = self.query_one("#how-body")
        room = (body.size.width or min(90, int(self.app.size.width * 0.8)) - 6) - body.styles.scrollbar_size_vertical
        show_drawing(self.query_one("#how-sketch", Static), room)

    @on(Button.Pressed, "#close")
    def close(self):
        self.dismiss()
