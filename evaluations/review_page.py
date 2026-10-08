"""A review package: each case's screens as its operator saw them, beside a form for the rubric.

``build_review_package`` replays every run of a completed report through the workspace (``evaluations.screens``)
and writes a folder holding ``index.html``, one ``cases/case-NN.js`` per case with that case's screens, and
``publish.json``. The page shows one case at a time: the setup, each turn's literal words and how they were sent,
and the workspace's screens after each reply. The rubric is judged on a form beside the screens, never on them.

Published as a claude.ai page (``publish.json`` holds the publish call; ``.claude/skills/publish-review`` makes
it), each reviewer's decisions are saved as they go, under their own account, where only they and the page's
owner can read them. The owner sees every reviewer's progress and saves each reviewer's ``review.json``. Opened
as a local file, the page keeps decisions in the browser and saves ``review.json`` itself. Either way the file
is in the format ``scripts/review_evaluation.py`` checks against the unchanged report.

The page is blind: it carries no machine check, no earlier review and no score. The records behind each screen
are there, folded, for criteria a screen cannot settle.
"""

import json
from pathlib import Path
import tempfile

from evaluations.review import review_template
from evaluations.screens import replay_run

STATUS_LABELS = {"pending": "Undecided", "pass": "Pass", "fail": "Fail", "unjudgeable": "Can't judge"}
# Each reviewer writes reviews/<their id>; nobody else reads it but the page's owner.
CAPABILITIES = {"db": {"rules": [{"path": "reviews", "read": "owner", "write": "owner"},
                                 {"path": "reviews/{self}", "read": "interact", "write": "interact"}]},
                "user": {}, "downloads": True}


def package_data(report_path, provider=None):
    """Replay each run; return what the page shows and each case's screens (SVG text by key)."""
    report_path = Path(report_path)
    report = json.loads(report_path.read_text())
    if report.get("status") != "completed":
        raise ValueError("Only a completed evaluation can be reviewed")
    template = review_template(report_path)
    if not template["decisions"]:
        raise ValueError("This report contains no semantic criteria to review")
    provider = provider or report.get("configuration", {}).get("provider") or "anthropic"
    cases, screens = [], {}
    with tempfile.TemporaryDirectory() as work:
        for run in report["runs"]:
            if not run.get("rubric"):
                continue
            directory = Path(work) / "screens" / run["id"]
            replayed = replay_run(report_path.parent, run, provider, Path(work) / "cases", directory)
            screens[run["id"]] = {path.stem: path.read_text(encoding="utf-8")
                                  for path in sorted(directory.glob("*.svg"))}
            turns = []
            for turn, entry in zip((t for t in run["turns"] if t["result"].get("request_id")), replayed):
                result = turn["result"]
                shots = ([entry["before"]] if "before" in entry else []) + entry["screens"]
                turns.append({
                    "number": turn["number"], "speaker": turn["speaker"], "text": turn["text"],
                    "sent_with": entry["sent_with"], "notes": entry["notes"],
                    "saved": result["status"] == "saved",
                    "outcome": "" if result["status"] == "saved" else
                               result.get("message") or result["status"].replace("_", " "),
                    "screens": [{"key": Path(s["file"]).stem, "view": s["view"], "size": s["size"]} for s in shots],
                    "records": turn.get("new_records", [])})
            cases.append({"id": run["id"], "scenarios": run.get("scenarios", []),
                          "setup": run.get("setup", ""), "setup_text": run.get("setup_text"),
                          "setup_records": run.get("setup_records", []), "turns": turns,
                          "stopped": len(turns) < len(run["turns"]) or any(not t["saved"] for t in turns)})
    for index, case in enumerate(cases, 1):
        case["file"] = f"cases/case-{index:02d}.js"
    return {"template": template, "cases": cases, "labels": STATUS_LABELS}, screens


def safe_json(value):
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")


def build_review_package(report_path, output=None, provider=None):
    """Write the package (default: ``review-package`` beside the report); refuse an existing folder."""
    report_path = Path(report_path)
    output = Path(output) if output else report_path.parent / "review-package"
    if output.exists():
        raise FileExistsError(f"{output} already exists; remove it or choose another --output")
    data, screens = package_data(report_path, provider)
    (output / "cases").mkdir(parents=True)
    for case in data["cases"]:
        (output / case["file"]).write_text(
            f"(window.reviewScreens = window.reviewScreens || {{}})[{safe_json(case['id'])}] = "
            f"{safe_json(screens[case['id']])};\n", encoding="utf-8")
    (output / "index.html").write_text(PAGE.replace("/*DATA*/", safe_json(data)), encoding="utf-8")
    write_publish(output, data)
    return output / "index.html"


def write_publish(output, data):
    """The Artifact publish call for this package, so any Claude session publishes it the same way."""
    count = len(data["template"]["decisions"])
    (output / "publish.json").write_text(json.dumps({
        "file_path": "index.html", "files": {case["file"]: case["file"] for case in data["cases"]},
        "capabilities": CAPABILITIES, "icon": "checklist", "title": "Semantic review",
        "description": f"Judge {count} rubric criteria across {len(data['cases'])} cases from the screens the "
                       f"operator saw; decisions save as you go.",
        "report_sha256": data["template"]["report_sha256"]}, indent=2) + "\n", encoding="utf-8")


PAGE = """<title>Semantic review</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
/* Layout: the case's screens in a wide reading column; the rubric in a narrower column that stays in view. */
:root {
  --bg: #f6f5f9; --panel: #ffffff; --ink: #1c1a24; --muted: #5f5a6e; --line: #dcd9e5; --shade: #eeecf3;
  --accent: #5a3fc0; --on-accent: #ffffff; --pass: #1d7a42; --fail: #b3261e; --unjudgeable: #8a5d00;
  --sans: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #15131b; --panel: #1e1b26; --ink: #ebe8f2; --muted: #a39db4; --line: #362f44; --shade: #27232f;
  --accent: #b7a3ff; --on-accent: #15131b; --pass: #6fd08f; --fail: #ff8a80; --unjudgeable: #e8c15a;
  color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #15131b; --panel: #1e1b26; --ink: #ebe8f2; --muted: #a39db4; --line: #362f44; --shade: #27232f;
  --accent: #b7a3ff; --on-accent: #15131b; --pass: #6fd08f; --fail: #ff8a80; --unjudgeable: #e8c15a;
  color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.5 var(--sans); padding: 0 16px 32px; }
h1, h2, h3 { text-wrap: balance; margin: 0; }
button, select, input, textarea { font: inherit; color: var(--ink); }
button, select { padding: 5px 12px; border: 1px solid var(--line); border-radius: 4px; background: var(--shade); cursor: pointer; }
button.primary { background: var(--accent); color: var(--on-accent); border-color: var(--accent); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.bar { display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: center; padding-block: 14px; border-bottom: 1px solid var(--line); }
.bar h1 { font-size: 18px; }
.bar .grow { flex: 1 1 auto; }
.label { font: 600 11px/1.4 var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
.status { font-size: 13px; color: var(--muted); }
.status.bad { color: var(--fail); }
.who { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: end; padding-block: 12px; }
.who label { display: grid; gap: 2px; }
.who input { padding: 4px 8px; border: 1px solid var(--line); border-radius: 4px; background: var(--panel); width: 14em; max-width: 100%; }
.intro { color: var(--muted); font-size: 14px; max-width: 70ch; margin: 0; }
.reviewers { border: 1px solid var(--line); border-radius: 6px; background: var(--panel); padding: 12px; margin-block: 8px; }
.reviewers table { border-collapse: collapse; width: 100%; font-size: 14px; }
.reviewers td, .reviewers th { text-align: left; padding: 6px 8px; border-top: 1px solid var(--line); }
.reviewers th { border-top: 0; }
.num { font-variant-numeric: tabular-nums; }
.scroll { overflow-x: auto; }
main { display: grid; grid-template-columns: minmax(0, 1fr) minmax(300px, 420px); gap: 20px; padding-block: 16px; }
@media (max-width: 900px) { main { grid-template-columns: minmax(0, 1fr); } }
.case-head { display: grid; gap: 6px; margin-bottom: 14px; }
.case-head h2 { font: 600 17px/1.3 var(--mono); }
.muted { color: var(--muted); }
.turn { display: grid; gap: 8px; padding-block: 14px; border-top: 1px solid var(--line); min-width: 0; }
.turn h3 { font-size: 15px; }
blockquote { margin: 0; padding: 8px 12px; border-left: 3px solid var(--accent); background: var(--shade); white-space: pre-wrap; }
.tabs { display: flex; flex-wrap: wrap; gap: 4px; }
.tabs button { font-size: 13px; padding: 3px 10px; }
.tabs button[aria-selected="true"] { background: var(--accent); color: var(--on-accent); border-color: var(--accent); }
.screen button { all: unset; display: block; cursor: zoom-in; width: 100%; }
.screen img { width: 100%; height: auto; display: block; border-radius: 6px; }
.note { background: var(--shade); padding: 6px 10px; border-radius: 4px; font-size: 14px; }
.outcome { color: var(--fail); font-weight: 600; }
details { font-size: 13px; }
details pre { overflow-x: auto; background: var(--shade); padding: 8px; border-radius: 4px; font: 12px/1.45 var(--mono); }
aside { position: sticky; top: 16px; align-self: start; max-height: calc(100vh - 32px); overflow-y: auto; display: grid; gap: 10px; min-width: 0; }
@media (max-width: 900px) { aside { position: static; max-height: none; } }
.criterion { background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 12px; display: grid; gap: 8px; }
.criterion p { margin: 0; }
.criterion .n { font: 600 13px var(--mono); color: var(--muted); margin-right: 4px; }
.choices { display: flex; flex-wrap: wrap; gap: 4px; }
.choices label { border: 1px solid var(--line); border-radius: 4px; padding: 2px 9px; cursor: pointer; font-size: 14px; }
.choices input { margin: 0 4px 0 0; }
.choices label.on { font-weight: 600; }
.choices label.on.pass { border-color: var(--pass); color: var(--pass); }
.choices label.on.fail { border-color: var(--fail); color: var(--fail); }
.choices label.on.unjudgeable { border-color: var(--unjudgeable); color: var(--unjudgeable); }
textarea { width: 100%; min-height: 4.5em; font-size: 14px; padding: 6px 8px; border: 1px solid var(--line); border-radius: 4px; background: var(--bg); }
textarea.missing { border-color: var(--fail); }
.nav { display: flex; flex-wrap: wrap; gap: 8px; }
.message { color: var(--fail); font-size: 14px; }
.zoom { position: fixed; inset: 0; background: color-mix(in srgb, var(--bg) 92%, transparent); overflow: auto; padding: 16px; z-index: 5; cursor: zoom-out; }
.zoom img { max-width: none; width: 1400px; display: block; margin: 0 auto; }
@media (prefers-reduced-motion: no-preference) { .tabs button, .choices label { transition: background .12s, border-color .12s; } }
</style>
<div class="bar">
  <h1>Semantic review</h1>
  <select id="case" aria-label="Case"></select>
  <span class="status num" id="progress"></span>
  <span class="grow"></span>
  <span class="status" id="saved" role="status"></span>
  <button id="save" type="button">Save review.json</button>
  <button id="load" type="button">Load a review</button>
  <input id="file" type="file" accept="application/json,.json" hidden>
</div>
<div class="who">
  <label><span class="label">Your name</span><input id="reviewer" autocomplete="name"></label>
  <label><span class="label">Your role</span><input id="reviewer_role" placeholder="e.g. TOC practitioner"></label>
  <label><span class="label">Date</span><input id="reviewed_at" type="date"></label>
  <p class="intro" id="intro">Each case shows what the operator saw after each reply. Judge each criterion from the screens and the
  turn's words, and cite the turn and screen in your evidence.</p>
</div>
<section class="reviewers" id="reviewers" hidden aria-label="Reviewers"></section>
<main>
  <section id="screens" aria-label="What the operator saw"></section>
  <aside id="form" aria-label="Rubric"></aside>
</main>
<div class="zoom" id="zoom" hidden></div>
<script type="application/json" id="data">/*DATA*/</script>
<script>
const data = JSON.parse(document.getElementById("data").textContent);
const review = JSON.parse(JSON.stringify(data.template));
const local = "reason-commons-review-" + review.report_sha256;
const FIELDS = ["reviewer", "reviewer_role", "reviewed_at"];
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
const keyOf = d => d.run_id + "__" + d.criterion;
const status = (text, bad = false) => { const s = document.getElementById("saved"); s.textContent = text; s.classList.toggle("bad", bad); };

// One reviewer's saved form: names they typed and a decision per criterion.
function stored() {
  const decisions = {};
  for (const d of review.decisions) if (d.status !== "pending" || d.evidence) decisions[keyOf(d)] = {status: d.status, evidence: d.evidence};
  const value = {report_sha256: review.report_sha256, decisions};
  for (const f of FIELDS) value[f] = review[f];
  return value;
}
function restore(value) {
  if (!value || value.report_sha256 !== review.report_sha256) return false;
  for (const f of FIELDS) review[f] = value[f] || "";
  const decisions = value.decisions || {};
  for (const d of review.decisions) {
    const old = Array.isArray(decisions) ? decisions.find(o => o.run_id === d.run_id && o.criterion === d.criterion && o.rubric === d.rubric)
                                         : decisions[keyOf(d)];
    if (old && old.status in data.labels) { d.status = old.status; d.evidence = old.evidence || ""; }
  }
  return true;
}
// A review.json for one reviewer, exactly the template with their decisions filled in.
function reviewFile(value) {
  const out = JSON.parse(JSON.stringify(data.template));
  for (const f of FIELDS) out[f] = value[f] || "";
  for (const d of out.decisions) { const old = (value.decisions || {})[keyOf(d)]; if (old) { d.status = old.status; d.evidence = old.evidence || ""; } }
  return JSON.stringify(out, null, 2) + "\\n";
}

// Saving: decisions go to the reviewer's own record when the page is published, else to this browser.
let pending = {}, timer = null, writing = Promise.resolve();
function merge(into, patch) {
  for (const [k, v] of Object.entries(patch)) {
    if (v && typeof v === "object" && !Array.isArray(v)) merge(into[k] = into[k] || {}, v); else into[k] = v;
  }
}
function changed(patch) {
  if (!state.hosted) { try { localStorage.setItem(local, JSON.stringify(stored())); } catch (e) { /* storage unavailable */ } return; }
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
  status("You can read this review but not record decisions. Ask the owner to share it with you as a Contributor.", true);
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
  try { snap = await state.ref.get(); } catch (e) { status("Decisions can't be saved right now. Reload the page to try again.", true); return; }
  state.hosted = true;
  document.getElementById("save").hidden = document.getElementById("load").hidden = true;
  document.getElementById("intro").textContent = "Each case shows what the operator saw after each reply. Judge each " +
    "criterion from the screens and the turn's words, and cite the turn and screen in your evidence. Your decisions " +
    "save as you go; other reviewers can't see them.";
  if (snap.exists) restore(snap.data());
  else { try { await state.ref.set(stored()); } catch (e) { readOnly(); } }
  if (!state.readOnly) status("Saved");
  for (const f of FIELDS) document.getElementById(f).value = review[f];
  show(+select.value); progress();
  if (await user.isOwner()) watchReviewers(db);
}

// The owner's view: everyone's progress, and each reviewer's review.json.
function watchReviewers(db) {
  const box = document.getElementById("reviewers");
  box.hidden = false;
  box.replaceChildren(el("p", {class: "muted", text: "Reviewers appear here once they open the page."}));
  db.collection("reviews").onSnapshot(snap => {
    const total = review.decisions.length;
    const rows = snap.docs.map(doc => {
      const value = doc.data() || {};
      const decided = Object.values(value.decisions || {}).filter(d => d.status && d.status !== "pending").length;
      const name = value.reviewer || "Name not given yet";
      return el("tr", {}, el("td", {text: name}), el("td", {text: value.reviewer_role || ""}),
        el("td", {class: "num", text: `${decided} of ${total}`}),
        el("td", {}, el("button", {type: "button", text: "Save review.json",
          onclick: event => offer(`review-${(value.reviewer || doc.id).replace(/[^A-Za-z0-9]+/g, "-")}.json`,
                                  reviewFile(value), event.target)})));
    });
    if (!rows.length) return;
    box.replaceChildren(el("div", {class: "label", text: "Reviewers (visible to you as owner)"}),
      el("div", {class: "scroll"}, el("table", {}, el("thead", {}, el("tr", {}, el("th", {text: "Reviewer"}),
        el("th", {text: "Role"}), el("th", {text: "Decided"}), el("th", {text: ""}))), el("tbody", {}, ...rows))));
  }, () => box.replaceChildren(el("p", {class: "message", text: "The reviewers' progress can't be read right now. Reload to try again."})));
}
async function offer(filename, text, button) {
  if (state.downloads) {
    try { await state.downloads.save({filename, data: text}); return; }
    catch (e) { if (e && e.code === "declined") return; }
  }
  const link = el("a", {href: URL.createObjectURL(new Blob([text], {type: "application/json"})), download: filename});
  document.body.append(link); link.click(); link.remove();
}

// Screens arrive per case, from cases/case-NN.js.
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
function zoom(src, alt) {
  const box = document.getElementById("zoom");
  box.replaceChildren(el("img", {src, alt}));
  box.hidden = false;
}
document.getElementById("zoom").addEventListener("click", () => { document.getElementById("zoom").hidden = true; });
document.addEventListener("keydown", e => { if (e.key === "Escape") document.getElementById("zoom").hidden = true; });

function screens(turn, svgs) {
  const box = el("div", {class: "screen"});
  const tabs = el("div", {class: "tabs", role: "tablist"});
  const pick = index => {
    const s = turn.screens[index];
    [...tabs.children].forEach((b, j) => b.setAttribute("aria-selected", j === index));
    const alt = `${s.view} at ${s.size}, as the workspace showed it`;
    if (!svgs) { box.replaceChildren(el("p", {class: "message", text: "This screen didn't load. Reload the page to try again."})); return; }
    const src = uri(svgs[s.key]);
    box.replaceChildren(el("button", {type: "button", title: "Show larger", onclick: () => zoom(src, alt)},
      el("img", {src, alt})));
  };
  turn.screens.forEach((s, i) => tabs.append(el("button", {role: "tab", type: "button", text: `${s.view} · ${s.size}`,
    onclick: () => pick(i)})));
  pick(Math.max(0, turn.screens.findIndex(s => s.view === "Next step")));
  return el("div", {}, tabs, box);
}
function records(label, value) {
  if (!value || !value.length) return null;
  return el("details", {}, el("summary", {text: label}), el("pre", {text: JSON.stringify(value, null, 2)}));
}
const select = document.getElementById("case");
data.cases.forEach((c, i) => select.append(el("option", {value: i, text: c.id})));
select.addEventListener("change", () => show(+select.value));
function progress() {
  const done = review.decisions.filter(d => d.status !== "pending").length;
  document.getElementById("progress").textContent = `${done} of ${review.decisions.length} criteria decided`;
  data.cases.forEach((c, i) => {
    const mine = review.decisions.filter(d => d.run_id === c.id);
    select.options[i].textContent = `${c.id} (${mine.filter(d => d.status !== "pending").length}/${mine.length})`;
  });
}
let shown = -1;
async function show(index) {
  shown = index;
  select.value = index;
  const c = data.cases[index];
  form(c, index);
  const left = document.getElementById("screens");
  const head = el("div", {class: "case-head"}, el("h2", {text: c.id}),
    el("div", {class: "muted", text: `Scenarios ${c.scenarios.join(", ")} · ${c.setup}`}),
    c.setup_text ? el("blockquote", {text: c.setup_text}) : null,
    records("Records the setup put in the case", c.setup_records));
  left.replaceChildren(head, el("p", {class: "muted", text: "Loading the screens…"}));
  let svgs = null;
  try { svgs = await screensOf(c); } catch (e) { svgs = null; }
  if (shown !== index) return;
  left.replaceChildren(head);
  for (const t of c.turns) {
    left.append(el("article", {class: "turn"},
      el("h3", {text: `Turn ${t.number}: ${t.speaker} · ${t.sent_with}`}),
      el("blockquote", {text: t.text}),
      ...t.notes.map(n => el("div", {class: "note", text: n})),
      t.saved ? null : el("div", {class: "outcome", text: `The application did not save this reply: ${t.outcome}.`}),
      screens(t, svgs), records("Records this reply added", t.records)));
  }
  if (c.stopped) left.append(el("div", {class: "note",
    text: "The run stopped here: a reply was not saved, so later turns were never sent."}));
  try { sessionStorage.setItem(local + "-case", index); } catch (e) { /* storage unavailable */ }
}
function form(c, index) {
  const right = document.getElementById("form");
  right.replaceChildren();
  for (const d of review.decisions.filter(d => d.run_id === c.id)) {
    const evidence = el("textarea", {id: `evidence-${keyOf(d)}`, "aria-label": `Evidence for criterion ${d.criterion}`,
      placeholder: "Cite the turn and screen, then what you saw there that decides it"});
    evidence.value = d.evidence;
    evidence.disabled = state.readOnly;
    const choices = el("div", {class: "choices", role: "radiogroup", "aria-label": `Decision on criterion ${d.criterion}`});
    const mark = () => {
      [...choices.children].forEach(l => l.className = (l.dataset.status === d.status ? "on " : "") + l.dataset.status);
      evidence.classList.toggle("missing", d.status !== "pending" && !d.evidence.trim());
    };
    for (const [value, label] of Object.entries(data.labels)) {
      const input = el("input", {type: "radio", name: `decision-${keyOf(d)}`, value});
      input.checked = d.status === value;
      input.disabled = state.readOnly;
      input.addEventListener("change", () => {
        d.status = value; mark(); progress();
        changed({decisions: {[keyOf(d)]: {status: d.status, evidence: d.evidence}}});
      });
      const option = el("label", {}, input, label);
      option.dataset.status = value;
      choices.append(option);
    }
    evidence.addEventListener("input", () => {
      d.evidence = evidence.value; mark();
      changed({decisions: {[keyOf(d)]: {status: d.status, evidence: d.evidence}}});
    });
    const text = el("p", {}, el("span", {class: "n", text: `${d.criterion}.`}), d.rubric);
    right.append(el("div", {class: "criterion"}, text, choices, evidence));
    mark();
  }
  right.append(el("div", {class: "nav"},
    index > 0 ? el("button", {type: "button", text: "Previous case", onclick: () => show(index - 1)}) : null,
    index < data.cases.length - 1 ? el("button", {type: "button", class: "primary", text: "Next case",
      onclick: () => { show(index + 1); window.scrollTo(0, 0); }}) : null));
}
for (const f of FIELDS) {
  const input = document.getElementById(f);
  input.addEventListener("input", () => { review[f] = input.value; changed({[f]: input.value}); });
}
document.getElementById("save").addEventListener("click", () => offer("review.json", reviewFile(stored())));
document.getElementById("load").addEventListener("click", () => document.getElementById("file").click());
document.getElementById("file").addEventListener("change", async event => {
  const file = event.target.files[0];
  if (!file) return;
  let value = null;
  try { value = JSON.parse(await file.text()); } catch (e) { /* reported below */ }
  if (!restore(value)) { status("That file is not a review of this report.", true); return; }
  changed({});
  for (const f of FIELDS) document.getElementById(f).value = review[f];
  show(shown); progress();
  status("Loaded " + file.name);
});

try { restore(JSON.parse(localStorage.getItem(local) || "null")); } catch (e) { /* storage unavailable */ }
for (const f of FIELDS) document.getElementById(f).value = review[f];
let start = 0;
try { start = Math.min(+(sessionStorage.getItem(local + "-case") || 0), data.cases.length - 1); } catch (e) { /* none */ }
show(start); progress();
connect();
</script>
"""
