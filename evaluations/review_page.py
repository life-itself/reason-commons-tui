"""A review package a reviewer with no background can use: each conversation in plain words, with questions.

``build_review_package`` replays every run of a completed report through the workspace (``evaluations.screens``)
and writes a folder holding ``index.html``, one ``cases/case-NN.js`` per case with that case's screens,
``publish.json`` (the publish call) and ``questions.json`` (what ``collect_reviews`` needs).

The page is read once, top to bottom, by someone who knows nothing of the method, the fixtures or the app, so it
introduces each thing before using it and gives each thing one name: the assistant is always "the system", and a
reviewer's case is a "conversation". The brief says what the system does, what a turn is, what the reviewer judges,
what the system keeps a record of, and what each answer means, with a worked example of its own; the reviewer's
name comes after it. Each conversation then gives who is talking and what was set up before it, and each turn gives
what the person wrote, the facts that message brings (with the sums done) right under it, the system's reply in
plain words (``evaluations.plain_reply``; codes in the system's own wording are explained where they first appear),
and the yes/no questions about that reply (``evaluations.review_questions``), or a line saying there are none. The
person's own screens are there, folded, under each reply. A question about a reply the system could not produce is
answered for the reviewer.

Each rubric criterion's decision comes from its questions' answers (``combine``), so the ``review.json`` the page
saves, and ``collect_reviews`` builds, is the template ``scripts/review_evaluation.py`` checks against the unchanged
report. Published as a claude.ai page, each reviewer's answers save as they go under their own account, readable only
by them and the page's owner; opened as a local file, the page keeps answers in the browser. The page carries no
machine check, earlier review or score.
"""

import json
from pathlib import Path
import re
import tempfile

from evaluations.fixtures import SCENARIOS
from evaluations.plain_reply import CODE, Names, plain_reply
from evaluations.review import review_template
from evaluations.review_questions import ANSWERS, REVIEW, Ask, combine
from evaluations.screens import replay_run

# The page names the assistant "the system", whichever model a run used.
CONSULTANT = "the system"
# Each reviewer writes reviews/<their id>; nobody else reads it but the page's owner.
CAPABILITIES = {"db": {"rules": [{"path": "reviews", "read": "owner", "write": "owner"},
                                 {"path": "reviews/{self}", "read": "interact", "write": "interact"}]},
                "user": {}, "downloads": True}
SCREEN_LABELS = {"Next step, answer typed": "Before sending", "Case context": "Everything the system has recorded",
                 "Trees": "The diagrams", "Backlog": "Waiting for approval"}
HOW = {"answer": "{speaker} typed this and sent it.",
       "direct_advice": "{speaker} typed this and sent it with the button that asks for direct advice.",
       "explain_observation": "{speaker} typed this and sent it with the button labelled “Ask for help planning an "
                              "observation”, which asks the system for help with results.",
       "another_question": "{speaker} pressed the button that asks the system for a different question."}
DECLARED = ("With this message, {speaker} also formally stated being the person in charge of the work. (The system "
            "only records someone as in charge when they state it this way.)")


def fixture_of(run_id):
    """The fixture a run comes from: semantic-<fixture>-<repetition>."""
    match = re.fullmatch(r"semantic-(.+)-(\d+)", run_id)
    return (match.group(1), int(match.group(2))) if match else (run_id, 1)


def screen_label(shot):
    if shot["view"] == "Next step":
        return "After the reply" + (", on a small screen" if shot["size"] == "80×24" else "")
    return SCREEN_LABELS.get(shot["view"], shot["view"])


def case_questions(run, authored, consultant, turns):
    """The case's questions, criterion by criterion, with an answer given for a turn that has no reply to judge."""
    replied = {t["number"] for t in turns if t["saved"]}
    sent = {t["number"] for t in turns}
    questions = []
    for criterion, rubric in enumerate(run.get("rubric", []), 1):
        asks = None
        if authored and criterion <= len(authored.criteria) and authored.criteria[criterion - 1][0] == rubric:
            asks = authored.criteria[criterion - 1][1]
        if asks is None:  # the rubric changed since these questions were written: ask the criterion itself
            asks = [Ask(None, "Is this true of {consultant}'s replies? " + rubric)]
        for index, ask in enumerate(asks, 1):
            question = {"id": f"{criterion}.{index}", "criterion": criterion, "turn": ask.turn,
                        "text": ask.text.format(consultant=consultant)}
            if ask.turn is not None and ask.turn not in replied:
                why = (f"The system couldn't produce a reply in Turn {ask.turn}, so there is nothing to judge."
                       if ask.turn in sent else
                       f"Turn {ask.turn} never happened: the conversation stopped after the error in an earlier turn.")
                question["given"] = {"answer": "cant", "why": why}
            questions.append(question)
    return questions


def package_data(report_path, provider=None, only=None):
    """Replay each run; return what the page shows and each case's screens (SVG text by key)."""
    report_path = Path(report_path)
    report = json.loads(report_path.read_text())
    if report.get("status") != "completed":
        raise ValueError("Only a completed evaluation can be reviewed")
    template = review_template(report_path)
    if not template["decisions"]:
        raise ValueError("This report contains no semantic criteria to review")
    provider = provider or report.get("configuration", {}).get("provider") or "anthropic"
    consultant = CONSULTANT
    planned = {s.name: len(s.turns) for s in SCENARIOS}
    runs = [run for run in report["runs"] if run.get("rubric")
            and (not only or run["id"] in only or fixture_of(run["id"])[0] in only)]
    if not runs:
        raise ValueError("No run with rubric criteria matches")
    cases, screens = [], {}
    with tempfile.TemporaryDirectory() as work:
        for run in runs:
            name, repetition = fixture_of(run["id"])
            authored = REVIEW.get(name)
            directory = Path(work) / "screens" / run["id"]
            replayed = replay_run(report_path.parent, run, provider, Path(work) / "cases", directory)
            screens[run["id"]] = {path.stem: path.read_text(encoding="utf-8")
                                  for path in sorted(directory.glob("*.svg"))}
            sent = [t for t in run["turns"] if t["result"].get("request_id")]
            speakers = {t["result"]["request_id"]: (t["number"], t["speaker"]) for t in sent}

            def source_of(refs):
                for ref in refs:
                    if ref in speakers:
                        number, speaker = speakers[ref]
                        return f"From {speaker}'s message in Turn {number}"
                return "From what was set up before this conversation" if refs else "Source not given"
            names = Names(run.get("setup_records", []))
            turns = []
            for turn, entry in zip(sent, replayed):
                saved = turn["result"]["status"] == "saved"
                records = turn.get("new_records", [])
                names.add(records)
                shots = ([entry["before"]] if "before" in entry else []) + entry["screens"]
                reply = plain_reply(records, names, source_of, capital(consultant)) if saved else None
                fill = {"speaker": turn["speaker"], "consultant": consultant}
                turns.append({
                    "number": turn["number"], "speaker": turn["speaker"], "text": turn["text"],
                    "how": HOW.get(entry["intent"], HOW["answer"]).format(**fill),
                    "declared": DECLARED.format(**fill) if entry["notes"] else "",
                    "saved": saved,
                    "reply": reply,
                    "codes": (CODE.search(json.dumps(reply, ensure_ascii=False)) or [""])[0] if reply else "",
                    "screens": [{"key": Path(s["file"]).stem, "label": screen_label(s)} for s in shots]})
            title = authored.title if authored else name.replace("_", " ")
            planned_turns = planned.get(name, len(run["turns"]))
            cases.append({
                "id": run["id"], "title": title + (f" (run {repetition})" if repetition > 1 else ""),
                "situation": authored.situation if authored else "No description of this conversation was written.",
                "facts": [list(row) for row in authored.facts] if authored else [], "turns": turns,
                "unsent": list(range(len(turns) + 1, planned_turns + 1)),
                "questions": case_questions(run, authored, consultant, turns)})
    for index, case in enumerate(cases, 1):
        case["file"] = f"cases/case-{index:02d}.js"
    return {"template": template, "cases": cases, "consultant": consultant, "answers": ANSWERS}, screens


def capital(text):
    return text[:1].upper() + text[1:]


def safe_json(value):
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")


def build_review_package(report_path, output=None, provider=None, only=None):
    """Write the package (default: ``review-package`` beside the report); refuse an existing folder."""
    report_path = Path(report_path)
    output = Path(output) if output else report_path.parent / "review-package"
    if output.exists():
        raise FileExistsError(f"{output} already exists; remove it or choose another --output")
    data, screens = package_data(report_path, provider, only)
    (output / "cases").mkdir(parents=True)
    for case in data["cases"]:
        (output / case["file"]).write_text(
            f"(window.reviewScreens = window.reviewScreens || {{}})[{safe_json(case['id'])}] = "
            f"{safe_json(screens[case['id']])};\n", encoding="utf-8")
    page = PAGE.replace("{consultant}", data["consultant"]).replace("/*DATA*/", safe_json(data))
    (output / "index.html").write_text(page, encoding="utf-8")
    (output / "questions.json").write_text(json.dumps(
        {"template": data["template"], "answers": ANSWERS,
         "cases": [{"id": c["id"], "questions": c["questions"]} for c in data["cases"]]},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    count = sum(len(c["questions"]) for c in data["cases"])
    (output / "publish.json").write_text(json.dumps({
        "file_path": "index.html", "files": {case["file"]: case["file"] for case in data["cases"]},
        "capabilities": CAPABILITIES, "icon": "checklist",
        "description": f"Answer {count} yes/no questions about an AI assistant's replies across "
                       f"{len(data['cases'])} short cases; answers save as you go.",
        "report_sha256": data["template"]["report_sha256"]}, indent=2) + "\n", encoding="utf-8")
    return output / "index.html"


def review_from_answers(questions, stored):
    """A reviewer's review.json, from the package's questions.json and their saved answers (one stored row)."""
    review = json.loads(json.dumps(questions["template"]))
    for field in ("reviewer", "reviewer_role", "reviewed_at"):
        review[field] = stored.get(field) or ""
    answers = stored.get("answers") or {}
    by_case = {case["id"]: case["questions"] for case in questions["cases"]}
    for decision in review["decisions"]:
        asked = [q for q in by_case.get(decision["run_id"], []) if q["criterion"] == decision["criterion"]]
        given = [q.get("given") or answers.get(f"{decision['run_id']}__{q['id']}") for q in asked]
        decision["status"] = combine([g["answer"] if g and g.get("answer") in ANSWERS else None for g in given])
        decision["evidence"] = " | ".join(evidence(q, g, questions["answers"]) for q, g in zip(asked, given)
                                          if g and g.get("answer") in ANSWERS)
    review["answers"] = answers  # kept so the page can reopen the file
    return review


def evidence(question, given, labels):
    where = f"Turn {question['turn']}" if question["turn"] else "Whole conversation"
    why = (given.get("why") or "").strip()
    return f"{where}: {question['text']} {labels[given['answer']]}" + (f" — {why}" if why else "")


def collect_reviews(package, rows, output):
    """Write review-<name>.json in ``output`` for each stored reviewer row (JSON files, as ArtifactData saves them)."""
    questions = json.loads((Path(package) / "questions.json").read_text())
    Path(output).mkdir(parents=True, exist_ok=True)
    written = []
    for path in sorted(Path(rows).rglob("*.json")):
        row = json.loads(path.read_text())
        stored = row["data"] if isinstance(row.get("data"), dict) else row
        if stored.get("report_sha256") != questions["template"]["report_sha256"]:
            continue
        review = review_from_answers(questions, stored)
        slug = re.sub(r"[^A-Za-z0-9]+", "-", stored.get("reviewer") or path.stem).strip("-") or path.stem
        target = Path(output) / f"review-{slug}.json"
        target.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(target)
    return written


PAGE = """<title>Reason Commons reply review</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:ital,wght@0,400;0,600;1,400&display=swap">
<style>
/* Layout: one reading column, in the order a newcomer needs it: the brief, the conversation, then each turn's words,
   facts, reply and questions; the person's screens stay folded under each reply. */
:root {
  --bg: #f6f5f9; --panel: #ffffff; --ink: #1c1a24; --muted: #5f5a6e; --line: #dcd9e5; --shade: #eeecf3;
  --accent: #5a3fc0; --on-accent: #ffffff; --sam: #ece9f7; --reply: #f1f6f3;
  --yes: #1d7a42; --no: #b3261e; --cant: #8a5d00;
  --sans: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #15131b; --panel: #1e1b26; --ink: #ebe8f2; --muted: #a39db4; --line: #362f44; --shade: #27232f;
  --accent: #b7a3ff; --on-accent: #15131b; --sam: #2a2540; --reply: #1d2a24;
  --yes: #6fd08f; --no: #ff8a80; --cant: #e8c15a; color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #15131b; --panel: #1e1b26; --ink: #ebe8f2; --muted: #a39db4; --line: #362f44; --shade: #27232f;
  --accent: #b7a3ff; --on-accent: #15131b; --sam: #2a2540; --reply: #1d2a24;
  --yes: #6fd08f; --no: #ff8a80; --cant: #e8c15a; color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.55 var(--sans); padding: 0 16px 48px; }
.page { max-width: 860px; margin: 0 auto; }
h1, h2, h3 { text-wrap: balance; margin: 0; line-height: 1.25; }
h1 { font-size: 24px; }
h2 { font-size: 21px; }
h3 { font-size: 17px; }
p { margin: 0; }
button, select, input, textarea { font: inherit; color: var(--ink); }
button, select { padding: 6px 14px; border: 1px solid var(--line); border-radius: 6px; background: var(--shade); cursor: pointer; }
button.primary { background: var(--accent); color: var(--on-accent); border-color: var(--accent); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.label { font: 600 12px/1.4 var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
.muted { color: var(--muted); }
.small { font-size: 14px; }
.stack { display: grid; gap: 12px; }
.top { display: grid; gap: 14px; padding-block: 20px 12px; }
.who { display: flex; flex-wrap: wrap; gap: 12px 18px; align-items: end; }
.who label { display: grid; gap: 4px; }
.who input, .who select { padding: 6px 10px; border: 1px solid var(--line); border-radius: 6px; background: var(--panel); width: 18em; max-width: 100%; }
.status { font-size: 14px; color: var(--muted); }
.status.bad { color: var(--no); }
.brief { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px 18px; }
.brief summary { cursor: pointer; font-weight: 600; font-size: 17px; }
.brief .stack { margin-top: 12px; max-width: 68ch; }
.brief ul { margin: 0; padding-left: 20px; display: grid; gap: 4px; }
.example { border-left: 3px solid var(--accent); padding: 8px 12px; background: var(--shade); border-radius: 0 6px 6px 0; display: grid; gap: 6px; }
.reviewers { border: 1px solid var(--line); border-radius: 8px; background: var(--panel); padding: 12px 16px; }
.reviewers table { border-collapse: collapse; width: 100%; font-size: 15px; }
.reviewers td, .reviewers th { text-align: left; padding: 6px 8px; border-top: 1px solid var(--line); }
.reviewers th { border-top: 0; }
.num { font-variant-numeric: tabular-nums; }
.scroll { overflow-x: auto; }
.nav { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; padding-block: 12px; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.nav select { max-width: 100%; min-width: 0; flex: 1 1 100%; }
.case { display: grid; gap: 22px; padding-block: 20px; }
.facts { border-collapse: collapse; width: 100%; font-size: 15px; }
.facts th, .facts td { text-align: left; vertical-align: top; padding: 7px 10px; border-top: 1px solid var(--line); }
.facts th { width: 32%; font-weight: 600; }
.turn { display: grid; gap: 12px; padding-top: 18px; border-top: 2px solid var(--line); min-width: 0; }
.said { background: var(--sam); border-radius: 8px; padding: 10px 14px; display: grid; gap: 4px; }
.said blockquote { margin: 0; white-space: pre-wrap; font-size: 17px; }
.reply { background: var(--reply); border-radius: 8px; padding: 10px 14px; display: grid; gap: 10px; }
.reply .move { font-size: 17px; }
.reply .why { font-size: 15px; }
.reply ul { margin: 0; padding-left: 20px; display: grid; gap: 8px; }
.reply li .lines { color: var(--muted); font-size: 14px; }
.reply li .src { font-size: 13px; color: var(--muted); font-style: italic; }
.rejected { color: var(--no); font-weight: 600; }
.reply .note { font-size: 14px; background: var(--panel); border-radius: 6px; padding: 6px 10px; }
details.screens summary { cursor: pointer; color: var(--accent); }
.tabs { display: flex; flex-wrap: wrap; gap: 6px; margin-block: 8px; }
.tabs button { font-size: 14px; padding: 3px 10px; }
.tabs button[aria-selected="true"] { background: var(--accent); color: var(--on-accent); border-color: var(--accent); }
.shot button { all: unset; display: block; cursor: zoom-in; width: 100%; }
.shot img { width: 100%; height: auto; display: block; border-radius: 6px; }
.questions { display: grid; gap: 10px; }
.q { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; display: grid; gap: 8px; }
.q.done { border-color: color-mix(in srgb, var(--accent) 45%, var(--line)); }
.choices { display: flex; flex-wrap: wrap; gap: 6px; }
.choices label { border: 1px solid var(--line); border-radius: 6px; padding: 4px 12px; cursor: pointer; font-size: 15px; }
.choices input { margin: 0 6px 0 0; }
.choices label.on { font-weight: 600; }
.choices label.on.yes { border-color: var(--yes); color: var(--yes); }
.choices label.on.no { border-color: var(--no); color: var(--no); }
.choices label.on.cant, .choices label.on.unclear { border-color: var(--cant); color: var(--cant); }
textarea { width: 100%; min-height: 3em; font-size: 15px; padding: 6px 10px; border: 1px solid var(--line); border-radius: 6px; background: var(--bg); }
textarea.missing { border-color: var(--no); }
.given { font-size: 14px; color: var(--muted); }
.end { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between; padding-top: 16px; border-top: 2px solid var(--line); }
.zoom { position: fixed; inset: 0; background: color-mix(in srgb, var(--bg) 94%, transparent); overflow: auto; padding: 16px; z-index: 5; cursor: zoom-out; }
.zoom img { max-width: none; width: 1400px; display: block; margin: 0 auto; }
@media (prefers-reduced-motion: no-preference) { .choices label, .tabs button { transition: background .12s, border-color .12s; } }
</style>
<div class="page">
<div class="top">
  <h1>Reviewing the system's replies</h1>
  <details class="brief" id="brief" open>
    <summary>Read this first (about two minutes)</summary>
    <div class="stack">
      <p><b>What this is.</b> Reason Commons is a system that helps people think through a problem at work, one step
      at a time. A person types a message about what is going on. The system replies: it keeps a record of what they
      said, and asks one next question or suggests a next step. One message and the system's reply to it make up a
      <b>turn</b>.</p>
      <p><b>What we'd like from you.</b> You'll read a few short conversations between a person and the system, one
      at a time. Under the system's replies are some yes/no questions about those replies. You are judging the
      system's replies only: not the person, and not whether their plan is a good idea.</p>
      <div>
        <p class="label">What the system keeps a record of</p>
        <ul>
          <li><b>Notes</b>: something a person said, kept in their own words.</li>
          <li><b>The goal</b>: what the person wants to achieve, and what must not get worse along the way.</li>
          <li><b>A trial</b>: a small change the person will try, with a prediction of what it will do, written down
          before it starts. People and the system may also call it a <b>pilot</b> or a <b>test</b>.</li>
          <li><b>Results and reviews</b>: what was measured during a trial, and the system's reading of the results
          against the prediction.</li>
          <li><b>Diagrams</b>: simple maps of the problem, made of short statements and links between them (for
          example, what is going wrong and what causes it).</li>
        </ul>
        <p>Each thing the system records says whose message it came from.</p>
      </div>
      <div>
        <p class="label">How to answer each question</p>
        <ul>
          <li><b>Yes</b>: the reply clearly does this.</li>
          <li><b>No</b>: it doesn't, or it does the opposite.</li>
          <li><b>Can't tell</b>: what's shown isn't enough to decide.</li>
          <li><b>I don't understand the question</b>: please say so. That tells us the question needs rewriting; it
          is never a wrong answer.</li>
        </ul>
        <p>Then add a few words saying why. This is needed for every answer except Yes.</p>
      </div>
      <div class="example">
        <p class="label">An example (made up, not one of the conversations)</p>
        <p><b>Anna wrote:</b> “We sold 30 of our 40 tickets.”</p>
        <p><b>The system replied:</b> “That's 75% sold. What share did you hope to sell?”</p>
        <p><b>Question:</b> Does the system work out what share of the tickets was sold?</p>
        <p><b>Answer:</b> Yes. <b>Why:</b> “It says 75%, and 30 of 40 is 75%.”</p>
      </div>
      <div>
        <p class="label">Good to know</p>
        <ul>
          <li>Each conversation takes about five minutes. Your answers save as you go, so you can stop and come
          back.</li>
          <li>Where a message contains numbers, we've done the sums for you, next to that message.</li>
          <li>Under each reply you can open the person's actual screen. You don't need it to answer. On that screen,
          the system's replies are labelled with the name of the AI model it uses (Claude), and the box for typing
          belongs to the person, not to you.</li>
        </ul>
      </div>
    </div>
  </details>
  <div class="stack">
    <p class="label">Before you start</p>
    <div class="who">
      <label><span class="label">Your name</span><input id="reviewer" autocomplete="name" placeholder="So we know whose answers these are"></label>
      <label><span class="label">Your background</span>
        <select id="reviewer_role">
          <option value="">Choose one</option>
          <option>No background in this kind of work</option>
          <option>Some experience running teams or projects</option>
          <option>Familiar with the Theory of Constraints (a management method)</option>
        </select></label>
      <span class="status" id="saved" role="status"></span>
    </div>
  </div>
  <section class="reviewers" id="reviewers" hidden aria-label="Reviewers"></section>
</div>
<div class="nav">
  <select id="case" aria-label="Conversation"></select>
  <span class="status num" id="progress"></span>
  <button id="save" type="button">Save my answers to a file</button>
  <button id="load" type="button">Open saved answers</button>
  <input id="file" type="file" accept="application/json,.json" hidden>
</div>
<main class="case" id="case-body"></main>
</div>
<div class="zoom" id="zoom" hidden></div>
<script type="application/json" id="data">/*DATA*/</script>
<script>
const data = JSON.parse(document.getElementById("data").textContent);
const C = data.consultant;
const local = "reason-commons-review-" + data.template.report_sha256;
const FIELDS = ["reviewer", "reviewer_role", "reviewed_at"];
const answers = {};
const me = {reviewer: "", reviewer_role: "", reviewed_at: ""};
const state = {hosted: false, ref: null, downloads: null, readOnly: false};
const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "text") node.textContent = v; else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const child of children) if (child) node.append(child);
  return node;
};
const Cap = C.charAt(0).toUpperCase() + C.slice(1);
const status = (text, bad = false) => { const s = document.getElementById("saved"); s.textContent = text; s.classList.toggle("bad", bad); };
const keyOf = (c, q) => c.id + "__" + q.id;
const answerOf = (c, q) => q.given || answers[keyOf(c, q)] || null;
const needsWhy = a => a && a.answer !== "yes" && !(a.why || "").trim();
const isDone = (c, q) => { const a = answerOf(c, q); return !!(a && a.answer && !needsWhy(a)); };

// A criterion's decision from its questions' answers (the same rule as review_questions.combine).
function combine(list) {
  if (!list.length || list.some(a => !a) || (list.includes("unclear") && !list.includes("no"))) return "pending";
  if (list.includes("no")) return "fail";
  if (list.includes("cant")) return "unjudgeable";
  return "pass";
}
function reviewFile() {
  const out = JSON.parse(JSON.stringify(data.template));
  for (const f of FIELDS) out[f] = me[f] || "";
  for (const d of out.decisions) {
    const c = data.cases.find(c => c.id === d.run_id);
    const asked = c ? c.questions.filter(q => q.criterion === d.criterion) : [];
    const given = asked.map(q => answerOf(c, q));
    d.status = combine(given.map(g => g && data.answers[g.answer] ? g.answer : null));
    d.evidence = asked.map((q, i) => {
      const g = given[i];
      if (!g || !data.answers[g.answer]) return null;
      const why = (g.why || "").trim();
      return `${q.turn ? "Turn " + q.turn : "Whole conversation"}: ${q.text} ${data.answers[g.answer]}${why ? " — " + why : ""}`;
    }).filter(Boolean).join(" | ");
  }
  out.answers = answers;
  return JSON.stringify(out, null, 2) + "\\n";
}
function stored() {
  const value = {report_sha256: data.template.report_sha256, answers};
  for (const f of FIELDS) value[f] = me[f];
  return value;
}
function restore(value) {
  if (!value || value.report_sha256 !== data.template.report_sha256) return false;
  for (const f of FIELDS) me[f] = value[f] || "";
  for (const [k, v] of Object.entries(value.answers || {})) if (v && (v.answer in data.answers || v.why)) answers[k] = {answer: v.answer || null, why: v.why || ""};
  return true;
}

// Saving: to the reviewer's own record when the page is published, else to this browser.
let pending = {}, timer = null, writing = Promise.resolve();
function merge(into, patch) {
  for (const [k, v] of Object.entries(patch)) {
    if (v && typeof v === "object" && !Array.isArray(v)) merge(into[k] = into[k] || {}, v); else into[k] = v;
  }
}
function changed(patch) {
  me.reviewed_at = new Date().toISOString().slice(0, 10);
  patch = Object.assign({reviewed_at: me.reviewed_at}, patch);
  if (!state.hosted) { try { localStorage.setItem(local, JSON.stringify(stored())); status("Saved in this browser"); } catch (e) { /* storage unavailable */ } return; }
  if (state.readOnly) return;
  merge(pending, patch);
  status("Saving…");
  clearTimeout(timer);
  timer = setTimeout(flush, 700);
}
function flush() {
  const patch = pending; pending = {};
  writing = writing.then(() => state.ref.update(patch)).then(
    () => { if (!Object.keys(pending).length) status("Saved"); },
    e => {
      if (e && e.code === "invalid_argument") readOnly();
      else status("Not saved. Check your connection; your next change will try again.", true);
      merge(pending, patch);
    });
}
function readOnly() {
  state.readOnly = true;
  status("You can read this review but your answers can't be saved. Ask the person who sent it to share it with you as a Contributor.", true);
  show(shown);
}
async function connect() {
  if (!window.claude || typeof window.claude.use !== "function") return;
  const [db, user, downloads] = await Promise.all(["db", "user", "downloads"].map(n => window.claude.use(n)));
  state.downloads = downloads;
  if (!db || !user) return;
  const id = await user.id();
  if (!id) return;
  state.ref = db.doc("reviews/" + id);
  let snap;
  try { snap = await state.ref.get(); } catch (e) { status("Answers can't be saved right now. Reload the page to try again.", true); return; }
  state.hosted = true;
  document.getElementById("save").hidden = document.getElementById("load").hidden = true;
  if (snap.exists) restore(snap.data());
  else { try { await state.ref.set(stored()); } catch (e) { readOnly(); } }
  if (!state.readOnly) status("Your answers save as you go. Other reviewers can't see them.");
  for (const f of ["reviewer", "reviewer_role"]) document.getElementById(f).value = me[f];
  show(shown); progress();
  if (await user.isOwner()) watchReviewers(db);
}

// The owner's view: everyone's progress, and each reviewer's review.json.
function watchReviewers(db) {
  const box = document.getElementById("reviewers");
  box.hidden = false;
  box.replaceChildren(el("p", {class: "muted small", text: "As the owner, you'll see each reviewer's progress here once they start."}));
  const total = data.cases.reduce((n, c) => n + c.questions.filter(q => !q.given).length, 0);
  db.collection("reviews").onSnapshot(snap => {
    if (!snap.docs.length) return;
    const rows = snap.docs.map(doc => {
      const value = doc.data() || {};
      const done = Object.values(value.answers || {}).filter(a => a && a.answer).length;
      return el("tr", {}, el("td", {text: value.reviewer || "Name not given yet"}), el("td", {text: value.reviewer_role || ""}),
        el("td", {class: "num", text: `${done} of ${total}`}),
        el("td", {}, el("button", {type: "button", text: "Save review.json", onclick: () => {
          const keep = {...me}, kept = {...answers};
          Object.keys(answers).forEach(k => delete answers[k]);
          restore(value);
          const text = reviewFile();
          Object.keys(answers).forEach(k => delete answers[k]); Object.assign(answers, kept); Object.assign(me, keep);
          offer(`review-${(value.reviewer || doc.id).replace(/[^A-Za-z0-9]+/g, "-")}.json`, text);
        }})));
    });
    box.replaceChildren(el("p", {class: "label", text: "Reviewers (only you, the owner, see this)"}),
      el("div", {class: "scroll"}, el("table", {}, el("thead", {}, el("tr", {}, el("th", {text: "Reviewer"}),
        el("th", {text: "Background"}), el("th", {text: "Answered"}), el("th", {text: ""}))), el("tbody", {}, ...rows))));
  }, () => box.replaceChildren(el("p", {class: "status bad", text: "Reviewers' progress can't be read right now. Reload to try again."})));
}
async function offer(filename, text) {
  if (state.downloads) {
    try { await state.downloads.save({filename, data: text}); return; }
    catch (e) { if (e && e.code === "declined") return; }
  }
  const link = el("a", {href: URL.createObjectURL(new Blob([text], {type: "application/json"})), download: filename});
  document.body.append(link); link.click(); link.remove();
}

// Sam's screens arrive per case, from cases/case-NN.js.
const loading = {};
function screensOf(c) {
  if (window.reviewScreens && window.reviewScreens[c.id]) return Promise.resolve(window.reviewScreens[c.id]);
  return loading[c.id] = loading[c.id] || new Promise((resolve, reject) => {
    const script = el("script", {src: c.file});
    script.onload = () => resolve((window.reviewScreens || {})[c.id]);
    script.onerror = reject;
    document.head.append(script);
  });
}
const uri = svg => "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
function zoom(src, alt) { const box = document.getElementById("zoom"); box.replaceChildren(el("img", {src, alt})); box.hidden = false; }
document.getElementById("zoom").addEventListener("click", () => { document.getElementById("zoom").hidden = true; });
document.addEventListener("keydown", e => { if (e.key === "Escape") document.getElementById("zoom").hidden = true; });
function screens(c, turn) {
  const box = el("div", {class: "shot"});
  const tabs = el("div", {class: "tabs", role: "tablist"});
  const details = el("details", {class: "screens"}, el("summary", {text: `See ${turn.speaker}'s actual screen for this turn (optional)`}), tabs, box);
  const pick = async index => {
    const s = turn.screens[index];
    [...tabs.children].forEach((b, j) => b.setAttribute("aria-selected", j === index));
    box.replaceChildren(el("p", {class: "muted small", text: "Loading…"}));
    let svgs = null;
    try { svgs = await screensOf(c); } catch (e) { svgs = null; }
    if (!svgs || !svgs[s.key]) { box.replaceChildren(el("p", {class: "status bad", text: "This screen didn't load. Reload the page to try again."})); return; }
    const src = uri(svgs[s.key]), alt = `${turn.speaker}'s screen: ${s.label}`;
    box.replaceChildren(el("button", {type: "button", title: "Show larger", onclick: () => zoom(src, alt)}, el("img", {src, alt})));
  };
  turn.screens.forEach((s, i) => tabs.append(el("button", {role: "tab", type: "button", text: s.label, onclick: () => pick(i)})));
  details.addEventListener("toggle", () => { if (details.open && !box.childNodes.length) pick(Math.max(0, turn.screens.findIndex(s => s.label === "After the reply"))); });
  return details;
}
function facts(rows, label) {
  if (!rows.length) return null;
  return el("div", {class: "stack"}, el("p", {class: "label", text: label}),
    el("div", {class: "scroll"}, el("table", {class: "facts"}, el("tbody", {}, ...rows.map(([, k, v]) => el("tr", {}, el("th", {text: k}), el("td", {text: v})))))));
}
function reply(turn, explainCodes) {
  if (!turn.saved) return el("div", {class: "reply"}, el("p", {class: "label", text: "The system replied"}),
    el("p", {class: "rejected", text: `The system couldn't produce a reply here. ${turn.speaker} saw an error message, and nothing was recorded.`}));
  const move = turn.reply.find(p => p.kind === "move");
  const recorded = turn.reply.filter(p => p.kind === "recorded");
  const colon = move ? move.headline.indexOf(": ") : -1;
  return el("div", {class: "reply"}, el("p", {class: "label", text: "The system replied"}),
    explainCodes ? el("p", {class: "note", text: `Codes like ${turn.codes} below are the system's own labels for things it recorded earlier. We've added in [square brackets] what each one refers to. The person saw only the code.`}) : null,
    move ? el("p", {class: "move"}, el("b", {text: move.headline.slice(0, colon + 1) + " "}), move.headline.slice(colon + 2)) : null,
    ...(move ? move.lines.map(line => el("p", {class: "why", text: line})) : []),
    recorded.length ? el("p", {class: "small", text: `The system recorded ${recorded.length === 1 ? "this" : "these " + recorded.length + " things"}:`}) : el("p", {class: "small muted", text: "The system recorded nothing else."}),
    recorded.length ? el("ul", {}, ...recorded.map(p => el("li", {}, el("div", {text: p.headline}),
      p.lines.length ? el("div", {class: "lines", text: p.lines.join(" · ")}) : null,
      el("div", {class: "src", text: p.source})))) : null);
}
function question(c, q) {
  const card = el("div", {class: "q"});
  card.append(el("p", {text: q.text}));
  if (q.given) {
    card.append(el("p", {class: "given", text: `Answered for you: ${data.answers[q.given.answer]}. ${q.given.why}`}));
    card.classList.add("done");
    return card;
  }
  const key = keyOf(c, q);
  const current = answers[key] || {answer: null, why: ""};
  const why = el("textarea", {id: "why-" + key, "aria-label": "Why?", placeholder: "Why? What in the reply shows this? A few words is enough."});
  why.value = current.why || "";
  why.disabled = state.readOnly;
  const choices = el("div", {class: "choices", role: "radiogroup", "aria-label": "Your answer"});
  const mark = () => {
    const a = answers[key];
    [...choices.children].forEach(l => l.className = (a && l.dataset.answer === a.answer ? "on " : "") + l.dataset.answer);
    why.classList.toggle("missing", !!needsWhy(a));
    card.classList.toggle("done", !!isDone(c, q));
  };
  for (const [value, label] of Object.entries(data.answers)) {
    const input = el("input", {type: "radio", name: "answer-" + key, value});
    input.checked = current.answer === value;
    input.disabled = state.readOnly;
    input.addEventListener("change", () => {
      answers[key] = {answer: value, why: why.value}; mark(); progress();
      changed({answers: {[key]: answers[key]}});
    });
    const option = el("label", {}, input, label);
    option.dataset.answer = value;
    choices.append(option);
  }
  why.addEventListener("input", () => {
    answers[key] = {answer: (answers[key] || {}).answer || null, why: why.value}; mark(); progress();
    changed({answers: {[key]: answers[key]}});
  });
  card.append(choices, why);
  mark();
  return card;
}
const select = document.getElementById("case");
data.cases.forEach((c, i) => select.append(el("option", {value: i, text: c.title})));
select.addEventListener("change", () => { show(+select.value); window.scrollTo(0, document.querySelector(".nav").offsetTop); });
function progress() {
  const all = data.cases.flatMap(c => c.questions.filter(q => !q.given).map(q => [c, q]));
  const done = all.filter(([c, q]) => isDone(c, q)).length;
  const c = data.cases[shown] || data.cases[0];
  const mine = c.questions.filter(q => !q.given);
  document.getElementById("progress").textContent = (mine.length
    ? `This conversation: ${mine.filter(q => isDone(c, q)).length} of ${mine.length} questions answered`
    : "Nothing to answer in this conversation") + ` · All conversations: ${done} of ${all.length}`;
  data.cases.forEach((c, i) => {
    const qs = c.questions.filter(q => !q.given);
    const n = qs.filter(q => isDone(c, q)).length;
    select.options[i].textContent = `${i + 1}. ${c.title} ${n === qs.length ? "(done)" : `(${n} of ${qs.length} answered)`}`;
  });
}
let shown = 0;
function show(index) {
  shown = index;
  select.value = index;
  const c = data.cases[index];
  const body = document.getElementById("case-body");
  const parts = [el("div", {class: "stack"},
    el("p", {class: "label", text: `Conversation ${index + 1} of ${data.cases.length}`}), el("h2", {text: c.title}),
    el("p", {text: c.situation}))];
  parts.push(facts(c.facts.filter(f => f[0] === 0), "Set up before this conversation"));
  let codesExplained = false;
  for (const t of c.turns) {
    const asked = c.questions.filter(q => q.turn === t.number);
    const explain = t.codes && !codesExplained;
    codesExplained = codesExplained || explain;
    parts.push(el("section", {class: "turn"}, el("h3", {text: `Turn ${t.number}`}),
      el("div", {class: "said"}, el("p", {class: "label", text: `${t.speaker} wrote`}), el("blockquote", {text: t.text}),
        el("p", {class: "small muted", text: t.how}), t.declared ? el("p", {class: "small muted", text: t.declared}) : null),
      facts(c.facts.filter(f => f[0] === t.number), "In plain terms, with the sums done"),
      reply(t, explain), screens(c, t),
      asked.length ? el("div", {class: "questions"}, el("p", {class: "label", text: `Questions about the system's reply in Turn ${t.number}`}), ...asked.map(q => question(c, q)))
        : el("p", {class: "small muted", text: "No questions about this reply. It's here so you can follow the conversation."})));
  }
  for (const n of c.unsent) {
    const asked = c.questions.filter(q => q.turn === n);
    parts.push(el("section", {class: "turn"}, el("h3", {text: `Turn ${n}`}),
      el("p", {class: "muted", text: `Turn ${n} never happened: the conversation stopped after the error in an earlier turn.`}),
      ...asked.map(q => question(c, q))));
  }
  const whole = c.questions.filter(q => q.turn === null);
  if (whole.length) parts.push(el("section", {class: "turn"}, el("h3", {text: "The conversation as a whole"}),
    el("p", {class: "small muted", text: "These questions are about all of the system's replies above."}),
    el("div", {class: "questions"}, ...whole.map(q => question(c, q)))));
  const left = c.questions.filter(q => !q.given && !isDone(c, q)).length;
  parts.push(el("div", {class: "end"},
    el("p", {class: "muted", text: left ? `${left} question${left === 1 ? "" : "s"} left in this conversation.`
      : c.questions.every(q => q.given) ? "There is nothing for you to answer in this conversation." : "You've answered every question in this conversation. Thank you."}),
    el("div", {class: "who"},
      index > 0 ? el("button", {type: "button", text: "Previous conversation", onclick: () => { show(index - 1); window.scrollTo(0, 0); }}) : null,
      index < data.cases.length - 1 ? el("button", {type: "button", class: "primary", text: "Next conversation", onclick: () => { show(index + 1); window.scrollTo(0, 0); }}) : null)));
  body.replaceChildren(...parts.filter(Boolean));
  progress();
  try { sessionStorage.setItem(local + "-case", index); } catch (e) { /* storage unavailable */ }
}
for (const f of ["reviewer", "reviewer_role"]) {
  const input = document.getElementById(f);
  input.addEventListener(f === "reviewer" ? "input" : "change", () => { me[f] = input.value; changed({[f]: input.value}); });
}
const brief = document.getElementById("brief");
try { if (localStorage.getItem(local + "-brief") === "closed") brief.open = false; } catch (e) { /* none */ }
brief.addEventListener("toggle", () => { try { localStorage.setItem(local + "-brief", brief.open ? "open" : "closed"); } catch (e) { /* none */ } });
document.getElementById("save").addEventListener("click", () => offer("review.json", reviewFile()));
document.getElementById("load").addEventListener("click", () => document.getElementById("file").click());
document.getElementById("file").addEventListener("change", async event => {
  const file = event.target.files[0];
  if (!file) return;
  let value = null;
  try { value = JSON.parse(await file.text()); } catch (e) { /* reported below */ }
  if (!restore(value)) { status("That file isn't a saved review of these cases.", true); return; }
  changed({});
  for (const f of ["reviewer", "reviewer_role"]) document.getElementById(f).value = me[f];
  show(shown);
  status("Opened " + file.name);
});
try { restore(JSON.parse(localStorage.getItem(local) || "null")); } catch (e) { /* storage unavailable */ }
for (const f of ["reviewer", "reviewer_role"]) document.getElementById(f).value = me[f];
let start = 0;
try { start = Math.min(+(sessionStorage.getItem(local + "-case") || 0), data.cases.length - 1); } catch (e) { /* none */ }
show(start);
connect();
</script>
"""
