"""The twelve voices of the Reason Commons web app, carried into the terminal as Textual themes.

A theme changes colour and frame, never behaviour. The palettes come from the web
app's ``styles.css`` (one ``[data-theme]`` block each) and keep its contract: four
colour families with jobs, distinguishable from one another and from the neutrals.

    hand          the human hand: chrome, focus, the Send button (web ``--brand-ink``)
    proposed      reasoning not yet in the record (web ``--accent``)
    stood-behind  reasoning that is accepted and relied upon (web ``--sage``)
    disagreed     reality disagreed, or something going wrong (web ``--rust``)

What changed on the way into a terminal:

* Every voice has a light form, which is the web palette, and a dark form with the
  same hues at mirrored lightness, because most terminals are dark. The web's
  ``--brand-lift`` ("light enough to read on the dark surfaces") is the dark hand.
* Fonts are the terminal's. Corner radius becomes the frame: voices drawn with
  radii of 6px or more get rounded frames, the hard-edged ones square frames.
* Each family's text colour is the first step of its scale that clears WCAG AA
  (4.5:1) on the ground, so a coloured label is always readable; muted text is the
  web's ``--neutral-600``, the lightest step the web guarantees at AA.

Textual's semantic slots are filled from the same families: ``primary`` and
``accent`` are the hand (the web's focus ring follows the brand, not the accent),
``warning`` is proposed, ``success`` and ``secondary`` are stood behind, and
``error`` is disagreed. The families are also exposed by name (``$hand``,
``$proposed``, ``$stood-behind``, ``$disagreed``) along with ``$hand-tint`` and
``$frame``, for CSS and for the coloured trees.

The descriptions are the web picker's. Where a voice reads a tradition rather than
one author, its colour assignments are the product's interpretation and not a
historical claim, and its description says so.
"""

from typing import NamedTuple

from textual.theme import Theme

ENVIRONMENT = "REASON_COMMONS_THEME"
DEFAULT_THEME = "commons-dark"
MODES = ("light", "dark")


class Palette(NamedTuple):
    ground: str
    surface: str
    sunk: str
    boost: str
    ink: str
    muted: str
    rule: str
    hand: str
    hand_tint: str
    proposed: str
    stood_behind: str
    disagreed: str


class Voice(NamedTuple):
    label: str
    attribution: str | None
    description: str


VOICES = {
    "commons": Voice("Commons", None,
                     "The public voice: warm paper, sage-green hand, slate for what is stood behind, brick where "
                     "reality disagreed."),
    "organic": Voice("Organic", None,
                     "Cream and earth: terracotta hand, olive for what is stood behind, wine where reality "
                     "disagreed."),
    "schopenhauer": Voice("Schopenhauer", None,
                          "Restrained and literary: graphite ink, oxblood hand, blue-black slate for what is stood "
                          "behind, brick where reality disagreed."),
    "goethe": Voice("Goethe", None,
                    "The polarity, laid out in planes: yellow for the question that has come near, blue for what "
                    "has withdrawn into the record, violet for a reservation deepening to carmine where a person "
                    "signs, yellow-red where reality pushed back."),
    "steiner": Voice("Steiner", None,
                     "Image and lustre: green for the record, which is the image of a thought that has stopped "
                     "moving; yellow and red for whatever is presently happening; peach-blossom for the human being "
                     "inside the machinery; blue for everything standing further off."),
    "al-haytham": Voice("Optics", "Ibn al-Haytham",
                        "What is given, apart from what has been inferred from it: an instrument plane in cool stone, "
                        "optical blue for the hand, observational green for the record, ochre for a proposal, "
                        "vermilion where reality disagreed. The four never blur, and edges do the work shadow does "
                        "elsewhere."),
    "tanizaki": Voice("Shadows", "Jun'ichirō Tanizaki",
                      "Attention shaped by restraint: smoked parchment with no white anywhere, tarnished bronze for "
                      "the hand, celadon for the record, lacquer red where reality disagreed. Things recede by "
                      "surface and space, never by fading the ink."),
    "suhrawardi": Voice("Illumination", "Suhrawardi",
                        "Presence through degrees of light — how manifest a thing is, never how true. Dusk "
                        "parchment, bronze-gold for the hand and its proposals, lapis for what is stood behind, earth "
                        "red where reality disagreed."),
    "wittgenstein": Voice("Grammar", "Ludwig Wittgenstein",
                          "Meaning through distinction and use: violet for the hand, cobalt for what is stood behind, "
                          "ochre for a proposal, oxide where reality disagreed. No hue means anything on its own — "
                          "the four are picked to exclude one another, and the flat, hard-edged surfaces leave the "
                          "work to boundary and adjacency."),
    "yoruba": Voice("Chromatics", "Yorùbá",
                    "Temperature as character, and mediation in the middle: warm paper, funfun silver for a "
                    "proposal, dudu blue-green for what is stood behind, pupa brick where reality disagreed, and "
                    "violet for the hand — placed outside the three families so authorship never becomes a "
                    "truth-value. The mapping is ours, not the tradition's."),
    "wuxing": Voice("Five Phases", "Wǔsè / Wǔxíng",
                    "Colour as a position in a set rather than a mood: the yellow centre spent on the ground and the "
                    "scaffolding, qīng for a proposal entering the system, metal's defined form for what is stood "
                    "behind, water's counterforce where reality disagreed, fire for the hand. The relational set is "
                    "the tradition's; the four assignments are ours."),
    "khipu": Voice("Channels", "Inka khipu",
                   "Undyed camelid fibre, and four dyes over it: ochre for a proposal, indigo for what is stood "
                   "behind, cochineal where reality disagreed, plant green for the hand. The borrowed idea is that "
                   "meaning is spread across channels — colour, cord, knot, position — so this is the theme that "
                   "leans least on hue and most on the dashed and solid line."),
}

# Per voice: frame, then the light palette (the web's own) and the dark one (same hues, mirrored lightness).
# Palette(ground, surface, sunk, boost, ink, muted, rule, hand, hand_tint, proposed, stood_behind, disagreed)
PALETTES = {
    "commons": ("round",
        Palette("#f0ece3", "#ffffff", "#e6e0d3", "#e6e0d3", "#17150f", "#665e52", "#d5cdbc", "#1c5238", "#bee2c9", "#815b1f", "#216188", "#9c3f28"),
        Palette("#181611", "#211f1b", "#110f0b", "#282622", "#eae8e1", "#b0aea8", "#44423d", "#8ec7a1", "#0c432b", "#e3b573", "#74bae9", "#ec7e62")),
    "organic": ("round",
        Palette("#f5ead8", "#fdf6ea", "#e5dccd", "#e5dccd", "#201e1d", "#6e6559", "#dcd3c4", "#8c491a", "#ffc6a5", "#8c491a", "#49612f", "#94305a"),
        Palette("#1a150c", "#241e15", "#140f06", "#2b261c", "#ede7de", "#b3ada4", "#484137", "#ffc6a5", "#542c12", "#fea570", "#9dbe7d", "#eb74a1")),
    "schopenhauer": ("solid",
        Palette("#e9e6de", "#f4f1e9", "#d8d4cc", "#d8d4cc", "#1c1c1a", "#67645d", "#bbb7ae", "#753b38", "#c59b95", "#753b38", "#485d66", "#9a4729"),
        Palette("#171612", "#211f1b", "#110f0c", "#282622", "#eae8e2", "#b0aea8", "#44423e", "#dca097", "#572826", "#f2a7a1", "#9eb5c0", "#e68360")),
    "goethe": ("solid",
        Palette("#f3efe3", "#fbf9f3", "#e3e1d6", "#e3e1d6", "#252724", "#5f6459", "#cfc9b8", "#7d3545", "#e1bad3", "#836412", "#31536b", "#a0491a"),
        Palette("#181610", "#211f19", "#110f0a", "#282620", "#eae8df", "#b0aea6", "#44423c", "#f0b1da", "#562731", "#deb966", "#8eb7d5", "#e98251")),
    "steiner": ("round",
        Palette("#f4f0e7", "#fcfaf4", "#d2dadf", "#d2dadf", "#252522", "#5a656a", "#c6c8c6", "#823f54", "#ecc1c7", "#83681a", "#3f5a4b", "#9b4933"),
        Palette("#181612", "#211f1b", "#110f0b", "#282622", "#eae8e1", "#b0aea8", "#44423d", "#feb8c3", "#552735", "#daba68", "#99baa7", "#e58369")),
    "al-haytham": ("solid",
        Palette("#eef0ed", "#ffffff", "#dfe5e2", "#dfe5e2", "#101619", "#586568", "#c7cdca", "#204c68", "#9fc3d8", "#785b00", "#3f6345", "#994735"),
        Palette("#151615", "#1f201e", "#0f100e", "#262725", "#e7e8e6", "#adaeac", "#424341", "#97c4df", "#0e3c57", "#dcb966", "#93be99", "#e5836c")),
    "tanizaki": ("solid",
        Palette("#d7cdb9", "#ece2cd", "#c6baa3", "#c6baa3", "#17140f", "#564e41", "#b7aa93", "#55410f", "#c2a960", "#624c15", "#39534d", "#863d2f"),
        Palette("#1a150b", "#241f14", "#130f06", "#2b261b", "#d5d0c7", "#b2ada3", "#474236", "#c8af66", "#483502", "#d6ba7e", "#99b9b1", "#df8673")),
    "suhrawardi": ("round",
        Palette("#eee6d3", "#fff8e7", "#ddd2ba", "#ddd2ba", "#17150f", "#625b4e", "#c9bda5", "#684707", "#d7be75", "#77520c", "#365f75", "#964a32"),
        Palette("#1a160c", "#231f15", "#130f06", "#2a261c", "#ece7de", "#b2aea3", "#464237", "#d7be75", "#4c3201", "#e3b570", "#88b9d4", "#e18669")),
    "wittgenstein": ("solid",
        Palette("#f3f2ed", "#fffefa", "#e6e4dd", "#e6e4dd", "#171717", "#665f59", "#c5c3bd", "#5d3d6d", "#c2a9cc", "#806000", "#385f8a", "#9b4437"),
        Palette("#171614", "#201f1d", "#100f0d", "#272624", "#e9e8e4", "#afaeab", "#434240", "#c7a5d5", "#452c51", "#dfb862", "#86b5ea", "#e8806f")),
    "yoruba": ("round",
        Palette("#efe8d9", "#fbf7ed", "#e4dcc9", "#e4dcc9", "#1d211f", "#565b56", "#d6cfc0", "#56407d", "#d5cced", "#58636e", "#286c67", "#a33e23"),
        Palette("#19160e", "#221f17", "#120f08", "#2a261e", "#ece7de", "#b2ada4", "#464239", "#baa7e5", "#3d2f57", "#b2c0cd", "#76c1ba", "#f17a5b")),
    "wuxing": ("round",
        Palette("#e8dfc5", "#f7f1df", "#ded3b5", "#ded3b5", "#201f1b", "#5d5850", "#d6cbb8", "#9f3220", "#f3b1a3", "#346756", "#575a6f", "#21405e"),
        Palette("#19160b", "#231f14", "#130f06", "#2a261b", "#ebe8de", "#b1aea3", "#464236", "#fa8f7b", "#572920", "#91ccb7", "#abafc9", "#80a6cc")),
    "khipu": ("solid",
        Palette("#d9c5a3", "#eee0c2", "#ccb695", "#ccb695", "#241b13", "#50443b", "#bba47e", "#2d5c3d", "#a4c9ae", "#714a01", "#265377", "#8c2f27"),
        Palette("#1b150b", "#241e14", "#140f06", "#2b261b", "#ede7de", "#b3ada4", "#484136", "#92be9d", "#154226", "#e5b471", "#83b7e4", "#ec7c6e")),
}

# Names the web app once stored, and what they are now.
RENAMED = {"critical-edition": "schopenhauer"}


def theme_name(voice, mode):
    return voice if mode == "light" else f"{voice}-{mode}"


def split_name(name):
    """``"tanizaki-dark"`` -> ``("tanizaki", "dark")``."""
    voice, _, mode = name.rpartition("-")
    return (voice, mode) if mode in MODES and voice in VOICES else (name, "light")


THEME_NAMES = [theme_name(voice, mode) for mode in MODES for voice in VOICES]


def resolve(value):
    """A theme name from what a person might type, or None.

    Accepts an id or its label in any case ("tanizaki", "Shadows"), the web's old
    names, and a light or dark form ("goethe dark", "Optics-dark", "commons-light").
    """
    text = " ".join(str(value or "").strip().lower().replace("_", " ").replace("-", " ").split())
    mode = "light"
    for candidate in MODES:
        if text == candidate or text.endswith(" " + candidate):
            mode, text = candidate, text[:-len(candidate)].strip()
    text = text.replace(" ", "-")
    labels = {v.label.lower().replace(" ", "-"): key for key, v in VOICES.items()}
    voice = text if text in VOICES else RENAMED.get(text) or labels.get(text)
    return theme_name(voice, mode) if voice else None


def title(name):
    """``"Shadows · Jun'ichirō Tanizaki, dark"``: label, attribution and mode, for menus."""
    voice, mode = split_name(name)
    label, attribution, _ = VOICES[voice]
    return (f"{label} · {attribution}" if attribution else label) + (", dark" if mode == "dark" else "")


def textual_theme(name):
    voice, mode = split_name(name)
    frame, *palettes = PALETTES[voice]
    p = palettes[MODES.index(mode)]
    return Theme(
        name=name, dark=mode == "dark",
        primary=p.hand, accent=p.hand, secondary=p.stood_behind,
        warning=p.proposed, success=p.stood_behind, error=p.disagreed,
        foreground=p.ink, background=p.ground, surface=p.surface, panel=p.sunk, boost=p.boost,
        variables={
            "hand": p.hand, "hand-tint": p.hand_tint, "proposed": p.proposed,
            "stood-behind": p.stood_behind, "disagreed": p.disagreed, "frame": frame,
            "text-muted": p.muted, "border": p.hand, "border-blurred": p.rule,
            "footer-background": p.sunk, "footer-key-foreground": p.hand,
            "block-cursor-background": p.hand_tint, "block-cursor-foreground": p.ink,
            "input-selection-background": f"{p.hand_tint} 70%",
        },
    )


THEMES = {name: textual_theme(name) for name in THEME_NAMES}
