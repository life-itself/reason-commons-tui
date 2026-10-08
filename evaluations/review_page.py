"""A review package a reviewer with no background can use: each case's conversation in plain words, with questions.

``build_review_package`` replays every run of a completed report through the workspace (``evaluations.screens``)
and writes a folder holding ``index.html``, one ``cases/case-NN.js`` per case with that case's screens,
``publish.json`` (the publish call) and ``questions.json`` (what ``collect_reviews`` needs).

The page starts with a short brief: what the app is, who Sam and the assistant are, that the reviewer judges the
assistant's replies, and what each answer means, with a worked example. Each case then gives what was going on, the
facts with the arithmetic done, and each turn as what the person wrote and what the assistant replied, in plain
words (``evaluations.plain_reply``), followed by yes/no questions about that reply (``evaluations.review_questions``).
The workspace's own screens are there, folded, under each reply. A question about a reply the application rejected
is answered for the reviewer: there is no reply to judge.

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
from evaluations.plain_reply import Names, plain_reply
from evaluations.review import review_template
from evaluations.review_questions import ANSWERS, REVIEW, Ask, combine
from evaluations.screens import replay_run

CONSULTANTS = {"anthropic": "Claude", "lm-studio": "the assistant"}
# Each reviewer writes reviews/<their id>; nobody else reads it but the page's owner.
CAPABILITIES = {"db": {"rules": [{"path": "reviews", "read": "owner", "write": "owner"},
                                 {"path": "reviews/{self}", "read": "interact", "write": "interact"}]},
                "user": {}, "downloads": True}
SCREEN_LABELS = {"Next step, answer typed": "Before sending", "Case context": "Everything the app has saved",
                 "Trees": "The diagrams", "Backlog": "Waiting for approval"}
HOW = {"answer": "{speaker} typed this and pressed Send.",
       "direct_advice": "{speaker} typed this and chose “Ask for direct advice”.",
       "explain_observation": "{speaker} typed this and chose “Ask for help planning an observation”, which asks "
                              "{consultant} to help make sense of results.",
       "another_question": "{speaker} chose “Ask another question”."}
DECLARED = ("Along with this message, {speaker} formally stated being the person in charge of the work. The app only "
            "records someone as in charge when they state it this way.")


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
                why = (f"The app rejected {consultant}'s reply to Turn {ask.turn}, so there is no reply to judge."
                       if ask.turn in sent else
                       f"Turn {ask.turn} was never sent: the conversation stopped after a reply was rejected.")
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
    consultant = CONSULTANTS.get(provider, "the assistant")
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
                return "From the setup" if refs else "No source given"
            names = Names(run.get("setup_records", []))
            turns = []
            for turn, entry in zip(sent, replayed):
                saved = turn["result"]["status"] == "saved"
                records = turn.get("new_records", [])
                names.add(records)
                shots = ([entry["before"]] if "before" in entry else []) + entry["screens"]
                fill = {"speaker": turn["speaker"], "consultant": consultant}
                turns.append({
                    "number": turn["number"], "speaker": turn["speaker"], "text": turn["text"],
                    "how": HOW.get(entry["intent"], HOW["answer"]).format(**fill),
                    "declared": DECLARED.format(**fill) if entry["notes"] else "",
                    "saved": saved,
                    "reply": plain_reply(records, names, source_of, capital(consultant)) if saved else None,
                    "screens": [{"key": Path(s["file"]).stem, "label": screen_label(s)} for s in shots]})
            title = authored.title if authored else name.replace("_", " ")
            planned_turns = planned.get(name, len(run["turns"]))
            cases.append({
                "id": run["id"], "title": title + (f" (run {repetition})" if repetition > 1 else ""),
                "situation": authored.situation if authored else run.get("setup", ""),
                "facts": [list(row) for row in authored.facts] if authored else [],
                "setup_text": run.get("setup_text"), "turns": turns,
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
/* Layout: one reading column, in the order a newcomer needs it: the brief, the case, then each turn's words, reply
   and questions; the app's screens stay folded under each reply. */
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
.reply .move { font-size: 17px; font-weight: 600; }
.reply ul { margin: 0; padding-left: 20px; display: grid; gap: 8px; }
.reply li .lines { color: var(--muted); font-size: 14px; }
.reply li .src { font-size: 13px; color: var(--muted); font-style: italic; }
.rejected { color: var(--no); font-weight: 600; }
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
  <h1>Is the AI assistant's reply any good?</h1>
  <div class="who">
    <label><span class="label">Your name</span><input id="reviewer" autocomplete="name" placeholder="So we know whose answers these are"></label>
    <label><span class="label">Your background</span>
      <select id="reviewer_role">
        <option value="">Choose one</option>
        <option>No background in this kind of work</option>
        <option>Some experience running teams or projects</option>
        <option>Familiar with the Theory of Constraints</option>
      </select></label>
    <span class="status" id="saved" role="status"></span>
  </div>
  <details class="brief" id="brief" open>
    <summary>Read this first: what you're being asked to do (2 minutes)</summary>
    <div class="stack">
      <p><b>Reason Commons</b> is an app that helps someone think through a problem at work, step by step, with an AI
      assistant (here, <b>{consultant}</b>). In these cases the person is usually <b>Sam</b>, a manager in a company's
      Payments area (sometimes a colleague, Priya, or a community organiser, David). They type what's going on, and
      {consultant} replies: it saves what they said, as notes and other items, and asks one next question or gives a
      recommendation.</p>
      <p><b>Your job is to judge {consultant}'s replies.</b> You are not judging Sam, or whether Sam's plan is a good
      business idea. Each case shows what was going on, the facts (with the sums already done), what Sam wrote, and
      what {consultant} replied. Under each reply are a few yes/no questions about it.</p>
      <div>
        <p class="label">How to answer each question</p>
        <ul>
          <li><b>Yes</b>: the reply clearly does this.</li>
          <li><b>No</b>: it doesn't, or it says the opposite.</li>
          <li><b>Can't tell</b>: what's shown isn't enough to decide.</li>
          <li><b>I don't understand the question</b>: please say so. That tells us the question needs rewriting; it
          is never a wrong answer.</li>
        </ul>
      </div>
      <p>Then add a few words on why, pointing at what you saw: “The reply says 18 of 20 is below 95%.” This is
      needed for No, Can't tell and I don't understand; for Yes it helps but is optional.</p>
      <div class="example">
        <p class="label">An example (a made-up case)</p>
        <p><b>Sam wrote:</b> “We sold 30 of the 40 tickets.”</p>
        <p><b>The reply:</b> “That's 75% sold. What share did you hope to sell?”</p>
        <p><b>Question:</b> Does {consultant} work out what share of the tickets was sold?</p>
        <p><b>Answer:</b> Yes. <b>Why:</b> “It says 75%, and 30 of 40 is 75%.”</p>
      </div>
      <p>Under each reply you can also open <b>Sam's actual screen</b>, exactly as the app showed it. You don't need
      it to answer, and the answer box on that screen is Sam's, not yours. Each case takes about five minutes. Your
      answers save as you go, so you can stop and come back.</p>
    </div>
  </details>
  <section class="reviewers" id="reviewers" hidden aria-label="Reviewers"></section>
</div>
<div class="nav">
  <select id="case" aria-label="Case"></select>
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
  const details = el("details", {class: "screens"}, el("summary", {text: `See ${turn.speaker}'s actual screen for this turn`}), tabs, box);
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
function reply(turn) {
  if (!turn.saved) return el("div", {class: "reply"}, el("p", {class: "label", text: `${Cap} replied`}),
    el("p", {class: "rejected", text: `${Cap}'s reply wasn't in a form the app could use, so the app rejected it: ${turn.speaker} saw an error message, and nothing from the reply was saved.`}));
  const move = turn.reply.find(p => p.kind === "move");
  const saved = turn.reply.filter(p => p.kind === "saved");
  return el("div", {class: "reply"}, el("p", {class: "label", text: `${Cap} replied`}),
    move ? el("p", {class: "move", text: move.headline}) : null,
    move && move.lines.length ? el("p", {class: "small muted", text: move.lines.join(" · ")}) : null,
    saved.length ? el("p", {class: "small", text: `${Cap} saved ${saved.length === 1 ? "this" : "these " + saved.length + " items"}:`}) : el("p", {class: "small muted", text: `${Cap} saved nothing else.`}),
    saved.length ? el("ul", {}, ...saved.map(p => el("li", {}, el("div", {text: p.headline}),
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
  const why = el("textarea", {id: "why-" + key, "aria-label": "Why?", placeholder: `Why? What in ${C}'s reply shows this? A few words is enough.`});
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
    ? `This case: ${mine.filter(q => isDone(c, q)).length} of ${mine.length} answered` : "Nothing to answer in this case")
    + ` · All cases: ${done} of ${all.length}`;
  data.cases.forEach((c, i) => {
    const qs = c.questions.filter(q => !q.given);
    const n = qs.filter(q => isDone(c, q)).length;
    select.options[i].textContent = `${i + 1}. ${c.title} ${n === qs.length ? "(done)" : `(${n} of ${qs.length})`}`;
  });
}
let shown = 0;
function show(index) {
  shown = index;
  select.value = index;
  const c = data.cases[index];
  const body = document.getElementById("case-body");
  const parts = [el("div", {class: "stack"},
    el("p", {class: "label", text: `Case ${index + 1} of ${data.cases.length}`}), el("h2", {text: c.title}),
    el("p", {text: c.situation}))];
  if (c.facts.length) parts.push(el("div", {class: "stack"}, el("p", {class: "label", text: "The facts (sums worked out for you)"}),
    el("div", {class: "scroll"}, el("table", {class: "facts"}, el("tbody", {}, ...c.facts.map(([k, v]) => el("tr", {}, el("th", {text: k}), el("td", {text: v}))))))));
  if (c.setup_text) parts.push(el("details", {}, el("summary", {class: "small", text: "Sam's exact setup message (we wrote it to create the situation; it isn't being judged)"}),
    el("p", {class: "small muted", text: c.setup_text})));
  for (const t of c.turns) {
    const asked = c.questions.filter(q => q.turn === t.number);
    parts.push(el("section", {class: "turn"}, el("h3", {text: `Turn ${t.number}`}),
      el("div", {class: "said"}, el("p", {class: "label", text: `${t.speaker} wrote`}), el("blockquote", {text: t.text}),
        el("p", {class: "small muted", text: t.how}), t.declared ? el("p", {class: "small muted", text: t.declared}) : null),
      reply(t), screens(c, t),
      asked.length ? el("div", {class: "questions"}, el("p", {class: "label", text: `Questions about ${C}'s reply to Turn ${t.number}`}), ...asked.map(q => question(c, q))) : null));
  }
  for (const n of c.unsent) {
    const asked = c.questions.filter(q => q.turn === n);
    parts.push(el("section", {class: "turn"}, el("h3", {text: `Turn ${n}`}),
      el("p", {class: "muted", text: "This turn was never sent: the conversation stopped after the app rejected a reply."}),
      ...asked.map(q => question(c, q))));
  }
  const whole = c.questions.filter(q => q.turn === null);
  if (whole.length) parts.push(el("section", {class: "turn"}, el("h3", {text: "The conversation as a whole"}),
    el("div", {class: "questions"}, ...whole.map(q => question(c, q)))));
  const left = c.questions.filter(q => !q.given && !isDone(c, q)).length;
  parts.push(el("div", {class: "end"},
    el("p", {class: "muted", text: left ? `${left} question${left === 1 ? "" : "s"} left in this case.`
      : c.questions.every(q => q.given) ? "There is nothing for you to answer in this case." : "You've answered every question in this case. Thank you."}),
    el("div", {class: "who"},
      index > 0 ? el("button", {type: "button", text: "Previous case", onclick: () => { show(index - 1); window.scrollTo(0, 0); }}) : null,
      index < data.cases.length - 1 ? el("button", {type: "button", class: "primary", text: "Next case", onclick: () => { show(index + 1); window.scrollTo(0, 0); }}) : null)));
  body.replaceChildren(...parts);
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
