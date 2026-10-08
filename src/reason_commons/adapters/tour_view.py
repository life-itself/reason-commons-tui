"""The guided tour on screen: story pages, the contents, and the strip that narrates the workspace.

A story page covers the workspace while the story is told, in the first-start screen's grammar: a quiet line
above, a heading in the accent colour, plain words, and the choices as rows to pick with the arrows and Enter.
Koans and people's words sit behind a bar, as quoted words do in a story's steps. Back, Contents and Leave the
tour are always one key or click away. The strip sits under the workspace, in the story strip's place and grammar:
which part, in its frame; at most three lines of narration; and quiet buttons.

Nothing here reads or changes a goal. The workspace (tui.py) tells the tour what happened, asks it what to say,
and does what a choice asks for.
"""

import re

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.content import Content
from textual.screen import Screen
from textual.widgets import Button, OptionList, Static
from textual.widgets.option_list import Option

from reason_commons.adapters.welcome import HowItWorksScreen, explanations, numbered, show_drawing, sketch

HOW = {"kicker": "Before you open it", "heading": "How this works",
       "lead": "This is the screen you'll work on, with each part numbered. Ruth's goal is already in it."}
CLOSING_KICKER = "At the pass"
CONTENTS_NOTE = "A part starts fresh, with Ruth's answers for everything before it."
TOUR_CSS = """
StoryPage, ContentsPage { background: $background; }
StoryPage #page, ContentsPage #page { padding: 0 2; height: 1fr; }
#page-top { height: 1; }
#page-name { width: 1fr; color: $text-muted; }
#page-part { width: auto; color: $text-muted; }
#page-kicker { margin-top: 1; color: $text-muted; }
#page-heading { color: $accent; text-style: bold; }
#page-body { height: auto; margin: 1 0; }
#page-body > Static { margin-bottom: 1; }
#page-body > .voice { margin-bottom: 0; }
#page-body > .voice-last { margin-bottom: 1; }
#page-body > Static:last-child { margin-bottom: 0; }
.quote { background: $boost; border-left: outer $text-primary 50%; padding: 0 1; }
.quote:light { border-left: outer $text-secondary; }
.page-quiet { color: $text-muted; }
#page-choices { height: auto; border: none; background: transparent; padding: 0; }
#page-choices > .option-list--option-highlighted { background: transparent; color: $accent; text-style: bold; }
#page-choices:focus > .option-list--option-highlighted { background: $hand-tint; color: $foreground; }
#page-nav { height: 1; }
#page-nav.hidden, #page-nav Button.hidden { display: none; }
#page-nav Button { min-width: 8; height: 1; border: none; margin-right: 1; background: transparent;
                   color: $text-muted; text-style: none; }
#page-nav Button:hover { color: $text; }
#page-nav Button:focus { background: $hand-tint; color: $foreground; text-style: bold; }
"""
STRIP_CSS = """
#tour-strip { height: auto; border: $frame $border-blurred; padding: 0 1; border-title-color: $text-muted;
              border-title-background: transparent; }
#tour-strip:focus-within { border: $frame $accent; }
#tour-strip.hidden { display: none; }
#tour-controls { height: 1; }
#tour-controls Button { min-width: 8; height: 1; border: none; margin-right: 1; background: transparent;
                        color: $text-muted; text-style: none; }
#tour-controls Button:hover { color: $text; }
#tour-controls #tour-next { color: $accent; }
#tour-controls Button:focus { background: $hand-tint; color: $foreground; text-style: bold; }
#tour-controls Button.hidden { display: none; }
"""


def styled(text):
    """Words from the tour script, as text: **this** is bold. Never markup, so any character is safe."""
    out = Text()
    for number, part in enumerate(re.split(r"\*\*(.+?)\*\*", text or "")):
        out.append(part, style="bold" if number % 2 else "")
    return out


def part_place(tour, part=None):
    """'Part 3 of 9', or nothing for the prologue and the epilogue."""
    number = tour.number(part)
    return f"Part {number} of {len(tour.numbered)}" if number else ""


def continue_detail(tour):
    """What Continue opens: the workspace, How this works, or the next part."""
    steps = tour.steps()
    if tour.at + 1 < len(steps):
        return {"beat": "to the workspace", "loop": "to the workspace", "how": "how the screen works"}.get(
            steps[tour.at + 1]["kind"], "")
    if tour.index + 1 < len(tour.parts):
        following = tour.parts[tour.index + 1]
        return part_place(tour, following) or following["title"]
    return ""


class TourPage(Screen):
    """A full screen of the tour: the tour's name and the part above, a heading, words, then choices. Calls
    ``choose`` with what was chosen; the workspace decides what follows."""

    BINDINGS = [Binding("escape", "choose('back')", "Back", show=False),
                Binding("ctrl+q", "choose('leave')", "Leave tour", priority=True, show=False),
                Binding("f1", "app.help", "Help", show=False),
                # Before the choices' own paging: the choices are a few rows, and the words are what runs on.
                Binding("pagedown", "page(1)", "More", show=False, priority=True),
                Binding("pageup", "page(-1)", "Back up", show=False, priority=True)]
    DEFAULT_CSS = TOUR_CSS
    SCOPED_CSS = False

    def __init__(self, tour, choose):
        super().__init__()
        self.tour, self.choose = tour, choose

    def compose(self) -> ComposeResult:
        from reason_commons.adapters.tui import HintBar  # the workspace's footer, drawn the same way here

        with Vertical(id="page"):
            with Horizontal(id="page-top"):
                yield Static(id="page-name")
                yield Static(id="page-part")
            yield Static(id="page-kicker")
            yield Static(id="page-heading")
            yield VerticalScroll(id="page-body")
            yield OptionList(id="page-choices")
            with Horizontal(id="page-nav"):
                yield Button("◀ Back", id="page-back")
                yield Button("Contents", id="page-contents")
                yield Button("Leave the tour", id="page-leave")
        yield HintBar()

    def on_mount(self):
        self.show()
        # Whether there is more below changes as the words are laid out: the footer follows.
        self.watch(self.query_one("#page-body"), "virtual_size", lambda _: self.refresh_hints(), init=False)

    def refresh_hints(self):
        self.query_one("HintBar").update_hints(self.hints(), controls=False)

    def show(self):
        """Draw what this page says now."""
        kicker, heading, blocks, choices, place = self.content()
        self.query_one("#page-name", Static).update(Content.assemble(("Reason Commons", "bold"), " · guided tour"))
        self.query_one("#page-part", Static).update(place)
        self.query_one("#page-kicker", Static).update(kicker or "")
        self.query_one("#page-kicker").display = bool(kicker)
        self.query_one("#page-heading", Static).update(heading or "")
        body = self.query_one("#page-body", VerticalScroll)
        body.remove_children()
        body.mount_all(blocks)
        body.scroll_home(animate=False)
        listing = self.query_one("#page-choices", OptionList)
        listing.clear_options()
        listing.add_options([Option(Content.assemble((label, "bold"), ("  " + detail, "$text-muted") if detail
                                                     else ""), id=key) for key, label, detail in choices])
        listing.highlighted = 0
        listing.focus()
        offered = {key for key, _, _ in choices}
        shown = {"page-back": self.can_go_back() and "back" not in offered,
                 "page-contents": "contents" not in offered,
                 "page-leave": not offered & {"leave", "home"}}
        for name, visible in shown.items():
            self.query_one("#" + name).set_class(not visible, "hidden")
        self.query_one("#page-nav").set_class(not any(shown.values()), "hidden")
        self.refresh_hints()
        self.call_after_refresh(self.fit)

    def can_go_back(self):
        return not self.tour.first()

    def more(self):
        """The words go on below: PgDn shows them, and the footer says so."""
        bodies = self.query("#page-body")
        return [("pgdn", "More", "pagedown")] if bodies and bodies.first().max_scroll_y > 0 else []

    def hints(self):
        back = [("esc", "Back", "escape")] if self.can_go_back() else []
        return [("↑↓", "Choose", None), ("⏎", "Open", "enter"), *self.more(), *back,
                ("^q", "Leave tour", "ctrl+q", "Leave"), ("f1", "Help", "f1")]

    def content(self):
        """(kicker, heading, body widgets, choices, the part's place) for the tour's step."""
        step, part = self.tour.step, self.tour.part
        place = part_place(self.tour)
        onward = [("next", "Continue", continue_detail(self.tour))]
        if step["kind"] == "how":
            sketch = Static(id="page-sketch")
            return (HOW["kicker"], HOW["heading"],
                    [Static(HOW["lead"]), sketch,
                     Static(numbered(explanations("guided"), lambda n: f"({n})")),
                     Static(HowItWorksScreen.CLOSING, classes="page-quiet")], onward, place)
        if step["kind"] == "closing":
            closing = step["closing"]
            return (CLOSING_KICKER, closing["title"],
                    [Static(styled(closing["koan"]), classes="quote"),
                     Static(styled(closing["key"]), classes="page-quiet"),
                     Static(Text.assemble(("Next: ", "bold"), closing["next"]))], onward, place)
        page = step["page"]
        blocks = [Static(styled(page["text"]))] if page.get("text") else []
        voices = page.get("quotes", [])
        for number, (speaker, role, words) in enumerate(voices, start=1):
            who = speaker + (f", {role}" if role else "")
            blocks.append(Static(Text.assemble((who, "dim"), "\n", f"“{words.strip(chr(34))}”"),
                                 classes="quote voice" + (" voice-last" if number == len(voices) else "")))
        if page.get("after"):
            blocks.append(Static(styled(page["after"])))
        if page.get("koan"):
            blocks.append(Static(styled(page["koan"]), classes="quote"))
        choices = [tuple(choice) for choice in page.get("choices", [])] or onward
        return page.get("kicker"), page.get("heading") or part["title"], blocks, choices, place

    def fit(self):
        """The words take the room the heading and the choices leave, and scroll only when they need more, so
        the choices sit right under them. How this works draws the screen only where the drawing leaves room
        for its numbered explanations, which say everything without it. The footer then says whether there is
        more below."""
        page, body = self.query_one("#page"), self.query_one("#page-body")
        rows = lambda widget: widget.outer_size.height + widget.styles.margin.top + widget.styles.margin.bottom
        taken = sum(rows(widget) for widget in page.children if widget is not body and widget.display)
        room = max(3, page.size.height - taken - body.styles.margin.top - body.styles.margin.bottom)
        body.styles.max_height = room
        holder = self.query("#page-sketch")
        if holder:
            drawing = holder.first(Static)
            words = sum(rows(widget) for widget in body.children if widget is not drawing)
            fits = room >= words + len(sketch(52)) + drawing.styles.margin.bottom
            show_drawing(drawing, body.size.width - body.styles.scrollbar_size_vertical if fits else 0)

    def action_page(self, direction):
        body = self.query_one("#page-body")
        (body.scroll_page_down if direction > 0 else body.scroll_page_up)(animate=False)

    def on_resize(self):
        self.call_after_refresh(self.fit)

    @on(OptionList.OptionSelected, "#page-choices")
    def chosen(self, event):
        self.choose(event.option.id)

    @on(Button.Pressed, "#page-nav Button")
    def nav_pressed(self, event):
        self.choose(event.button.id.removeprefix("page-"))

    def action_choose(self, key):
        if key == "back" and not self.can_go_back():
            return
        self.choose(key)


class StoryPage(TourPage):
    """A page of the story: an opening, How this works, the monastery, or a part's closing koan."""


class ContentsPage(TourPage):
    """The nine parts, to start any of them; Back returns to where the person was."""

    def can_go_back(self):
        return True

    def hints(self):
        return [("↑↓", "Choose", None), ("⏎", "Start", "enter"), *self.more(), ("esc", "Back", "escape"),
                ("f1", "Help", "f1")]

    def content(self):
        here = self.tour.part["id"]
        rows = [("part:" + part["id"],
                 (f"{self.tour.number(part)}  " if self.tour.number(part) else "   ") + part["title"],
                 "you are here" if part["id"] == here else "")
                for part in self.tour.parts[:-1]]
        rows[0] = (rows[0][0], "   From the beginning", rows[0][2])
        return ("Contents", self.tour.script["name"], [Static(CONTENTS_NOTE, classes="page-quiet")], rows,
                part_place(self.tour))

    def show(self):
        super().show()
        listing = self.query_one("#page-choices", OptionList)
        listing.highlighted = next(i for i, part in enumerate(self.tour.parts) if part is self.tour.part) \
            if self.tour.part is not self.tour.parts[-1] else 0
        for name in ("#page-contents", "#page-leave"):
            self.query_one(name).add_class("hidden")
        self.query_one("#page-back").remove_class("hidden")
        self.query_one("#page-nav").remove_class("hidden")


class TourStrip(Vertical):
    """The tour's narration under the workspace: which part in its frame, what to notice or do, and the way
    on. A beat's own button moves the view only when it is pressed."""

    DEFAULT_CSS = STRIP_CSS
    SCOPED_CSS = False

    def compose(self) -> ComposeResult:
        yield Static(id="tour-text")
        with Horizontal(id="tour-controls"):
            yield Button("◀ Back", id="tour-back")
            yield Button("", id="tour-do", classes="hidden")
            yield Button("Next ▶", id="tour-next")
            yield Button("Contents", id="tour-contents")
            yield Button("Leave tour", id="tour-leave")

    def show(self, tour):
        number = part_place(tour)
        title = Content.assemble(("Tour", "bold"), f" · {number}" if number else "", f" · {tour.part['title']}")
        self.border_title = title
        self.query_one("#tour-text", Static).update(styled(tour.say()))
        button = tour.button()
        do, onward = self.query_one("#tour-do", Button), self.query_one("#tour-next", Button)
        do.set_class(button is None, "hidden")
        labels = ((do, button and button["label"]), (onward, "Continue ▶" if tour.next_is_page() else "Next ▶"))
        for widget, label in labels:
            if label and str(widget.label) != label:
                widget.label = label
                widget.refresh(layout=True)  # a label is not laid out again by itself
