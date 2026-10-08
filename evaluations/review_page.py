"""A review package: each case's screens as its operator saw them, beside a form for the rubric.

``build_review_package`` replays every run of a completed report through the workspace (``evaluations.screens``)
and writes a folder holding ``index.html`` and the screens. The page shows, for one case at a time, the setup,
each turn's literal words and how they were sent, and the workspace's screens after each reply; the rubric is
judged on a form beside the screens, never on them. The page writes a ``review.json`` in the format
``scripts/review_evaluation.py`` checks against the unchanged report.

The page is blind: it carries no machine check, no earlier review and no score. The records behind each screen
are there, folded, for criteria a screen cannot settle.
"""

import json
from pathlib import Path
import tempfile

from evaluations.review import review_template
from evaluations.screens import replay_run

STATUS_LABELS = {"pending": "Undecided", "pass": "Pass", "fail": "Fail", "unjudgeable": "Can't judge"}


def package_data(report_path, output, provider=None):
    """Replay each run and describe what the page shows; the screens are written under ``output``/screens."""
    report_path = Path(report_path)
    report = json.loads(report_path.read_text())
    if report.get("status") != "completed":
        raise ValueError("Only a completed evaluation can be reviewed")
    template = review_template(report_path)
    if not template["decisions"]:
        raise ValueError("This report contains no semantic criteria to review")
    provider = provider or report.get("configuration", {}).get("provider") or "anthropic"
    cases = []
    with tempfile.TemporaryDirectory() as work:
        for run in report["runs"]:
            if not run.get("rubric"):
                continue
            directory = Path(output) / "screens" / run["id"]
            replayed = {entry["number"]: entry for entry in replay_run(report_path.parent, run, provider, work,
                                                                      directory)}
            turns = []
            for turn, entry in zip((t for t in run["turns"] if t["result"].get("request_id")), replayed.values()):
                result = turn["result"]
                screens = ([entry["before"]] if "before" in entry else []) + entry["screens"]
                turns.append({
                    "number": turn["number"], "speaker": turn["speaker"], "text": turn["text"],
                    "sent_with": entry["sent_with"], "notes": entry["notes"],
                    "saved": result["status"] == "saved",
                    "outcome": "" if result["status"] == "saved" else
                               result.get("message") or result["status"].replace("_", " "),
                    "screens": [dict(s, file=f"screens/{run['id']}/{s['file']}") for s in screens],
                    "records": turn.get("new_records", [])})
            cases.append({"id": run["id"], "scenarios": run.get("scenarios", []),
                          "setup": run.get("setup", ""), "setup_text": run.get("setup_text"),
                          "setup_records": run.get("setup_records", []), "turns": turns,
                          "stopped": len(turns) < len(run["turns"]) or any(not t["saved"] for t in turns)})
    return {"template": template, "cases": cases, "labels": STATUS_LABELS,
            "configuration": {"provider": provider, "started": report.get("started")}}


def build_review_package(report_path, output, provider=None):
    """Write ``output``/index.html and its screens; refuse an existing output folder."""
    output = Path(output)
    if output.exists():
        raise FileExistsError("Use a new review package folder")
    output.mkdir(parents=True)
    data = package_data(report_path, output, provider)
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    (output / "index.html").write_text(PAGE.replace("/*DATA*/", payload), encoding="utf-8")
    return output / "index.html"


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Semantic review</title>
<style>
:root { --bg: #fbfaf7; --panel: #ffffff; --ink: #1d1b16; --muted: #6b665c; --line: #dedad0; --accent: #5b3fb5;
  --pass: #1f7a3f; --fail: #b3261e; --unjudgeable: #8a6100; --pending: #6b665c; --shade: #f2efe7; }
@media (prefers-color-scheme: dark) { :root { --bg: #16140f; --panel: #1f1c16; --ink: #ece8de; --muted: #a39d90;
  --line: #3a362d; --accent: #b39dff; --pass: #6fd08f; --fail: #ff8a80; --unjudgeable: #e8c15a; --pending: #a39d90;
  --shade: #29251d; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.5 system-ui, sans-serif; }
header { padding: 12px 16px; border-bottom: 1px solid var(--line); display: flex; flex-wrap: wrap; gap: 8px 16px;
  align-items: center; background: var(--panel); }
header h1 { font-size: 17px; margin: 0 8px 0 0; }
header label { color: var(--muted); font-size: 13px; }
header input { font: inherit; padding: 3px 6px; border: 1px solid var(--line); border-radius: 4px; background: var(--bg);
  color: var(--ink); width: 11em; }
button, select { font: inherit; padding: 4px 10px; border: 1px solid var(--line); border-radius: 4px;
  background: var(--shade); color: var(--ink); cursor: pointer; }
button.primary { background: var(--accent); color: var(--bg); border-color: var(--accent); }
.progress { color: var(--muted); font-size: 13px; }
main { display: grid; grid-template-columns: minmax(0, 1fr) minmax(320px, 440px); gap: 16px; padding: 16px; }
@media (max-width: 900px) { main { grid-template-columns: minmax(0, 1fr); } }
.case-head { margin-bottom: 12px; }
.case-head h2 { margin: 0; font-size: 18px; }
.muted { color: var(--muted); }
.turn { background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 12px; margin-bottom: 16px; }
.turn h3 { margin: 0 0 6px; font-size: 15px; }
blockquote { margin: 6px 0; padding: 6px 10px; border-left: 3px solid var(--accent); background: var(--shade);
  white-space: pre-wrap; }
.tabs { display: flex; flex-wrap: wrap; gap: 4px; margin: 8px 0; }
.tabs button[aria-selected="true"] { background: var(--accent); color: var(--bg); border-color: var(--accent); }
.screen img { width: 100%; height: auto; display: block; border-radius: 4px; }
.note { background: var(--shade); padding: 6px 10px; border-radius: 4px; margin: 6px 0; font-size: 14px; }
.outcome { color: var(--fail); font-weight: 600; }
details { margin-top: 8px; font-size: 13px; }
details pre { overflow-x: auto; background: var(--shade); padding: 8px; border-radius: 4px; }
aside { position: sticky; top: 16px; align-self: start; max-height: calc(100vh - 32px); overflow-y: auto; }
@media (max-width: 900px) { aside { position: static; max-height: none; } }
.criterion { background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 10px; margin-bottom: 10px; }
.criterion p { margin: 0 0 8px; }
.choices { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 6px; }
.choices label { border: 1px solid var(--line); border-radius: 4px; padding: 2px 8px; cursor: pointer; font-size: 14px; }
.choices input { margin: 0 4px 0 0; }
.choices label.on.pass { border-color: var(--pass); color: var(--pass); }
.choices label.on.fail { border-color: var(--fail); color: var(--fail); }
.choices label.on.unjudgeable { border-color: var(--unjudgeable); color: var(--unjudgeable); }
textarea { width: 100%; min-height: 4.5em; font: inherit; font-size: 14px; padding: 6px; border: 1px solid var(--line);
  border-radius: 4px; background: var(--bg); color: var(--ink); }
.missing { border-color: var(--fail); }
.nav { display: flex; gap: 8px; margin-top: 8px; }
</style>
</head>
<body>
<header>
  <h1>Semantic review</h1>
  <label>Reviewer <input id="reviewer" autocomplete="name"></label>
  <label>Role <input id="reviewer_role"></label>
  <label>Date <input id="reviewed_at" type="date"></label>
  <select id="case" aria-label="Case"></select>
  <span class="progress" id="progress"></span>
  <button id="save" class="primary">Save review.json</button>
  <button id="load">Load a review</button>
  <input id="file" type="file" accept="application/json,.json" hidden>
</header>
<main>
  <section id="screens" aria-label="What the operator saw"></section>
  <aside id="form" aria-label="Rubric"></aside>
</main>
<script type="application/json" id="data">/*DATA*/</script>
<script>
const data = JSON.parse(document.getElementById("data").textContent);
const review = JSON.parse(JSON.stringify(data.template));
const key = "reason-commons-review-" + review.report_sha256;
const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "text") node.textContent = v; else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const child of children) if (child) node.append(child);
  return node;
};
function restore(saved) {
  if (!saved || saved.report_sha256 !== review.report_sha256) return false;
  for (const field of ["reviewer", "reviewer_role", "reviewed_at"]) review[field] = saved[field] || "";
  const byId = new Map((saved.decisions || []).map(d => [d.run_id + "#" + d.criterion, d]));
  for (const d of review.decisions) {
    const old = byId.get(d.run_id + "#" + d.criterion);
    if (old && old.rubric === d.rubric && old.status in data.labels) { d.status = old.status; d.evidence = old.evidence || ""; }
  }
  return true;
}
try { restore(JSON.parse(localStorage.getItem(key) || "null")); } catch (e) { /* storage unavailable */ }
function keep() { try { localStorage.setItem(key, JSON.stringify(review)); } catch (e) { /* storage unavailable */ } }
for (const field of ["reviewer", "reviewer_role", "reviewed_at"]) {
  const input = document.getElementById(field);
  input.value = review[field];
  input.addEventListener("input", () => { review[field] = input.value; keep(); });
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
function screens(turn) {
  const box = el("div", {class: "screen"});
  const tabs = el("div", {class: "tabs", role: "tablist"});
  const pick = (index) => {
    const s = turn.screens[index];
    [...tabs.children].forEach((b, j) => b.setAttribute("aria-selected", j === index));
    box.replaceChildren(el("a", {href: s.file, target: "_blank", rel: "noopener", title: "Open full size"},
      el("img", {src: s.file, loading: "lazy", alt: `${s.view} at ${s.size}, as the workspace showed it`})));
  };
  turn.screens.forEach((s, i) => tabs.append(el("button", {role: "tab", type: "button", text: `${s.view} · ${s.size}`,
    onclick: () => pick(i)})));
  const wrap = el("div", {}, tabs, box);
  pick(turn.screens.findIndex(s => s.view === "Next step"));
  return wrap;
}
function records(label, value) {
  if (!value || !value.length) return null;
  return el("details", {}, el("summary", {text: label}), el("pre", {text: JSON.stringify(value, null, 2)}));
}
function show(index) {
  select.value = index;
  const c = data.cases[index];
  const left = document.getElementById("screens");
  left.replaceChildren(el("div", {class: "case-head"}, el("h2", {text: c.id}),
    el("div", {class: "muted", text: `Scenarios ${c.scenarios.join(", ")} · ${c.setup}`}),
    c.setup_text ? el("blockquote", {text: c.setup_text}) : null,
    records("Records the setup put in the case", c.setup_records)));
  for (const t of c.turns) {
    left.append(el("article", {class: "turn"},
      el("h3", {text: `Turn ${t.number}: ${t.speaker} · ${t.sent_with}`}),
      el("blockquote", {text: t.text}),
      ...t.notes.map(n => el("div", {class: "note", text: n})),
      t.saved ? null : el("div", {class: "outcome", text: `The application did not save this reply: ${t.outcome}.`}),
      screens(t), records("Records this reply added", t.records)));
  }
  if (c.stopped) left.append(el("div", {class: "note",
    text: "The run stopped here: a reply was not saved, so later turns were never sent."}));
  const right = document.getElementById("form");
  right.replaceChildren(el("p", {class: "muted",
    text: "Judge each criterion from what the screens and the turn's words show. Cite the turn and screen in the evidence."}));
  for (const d of review.decisions.filter(d => d.run_id === c.id)) {
    const evidence = el("textarea", {"aria-label": `Evidence for criterion ${d.criterion}`,
      placeholder: "Cite the turn and screen, then what you saw there that decides it"});
    evidence.value = d.evidence;
    const choices = el("div", {class: "choices", role: "radiogroup"});
    const mark = () => {
      [...choices.children].forEach(l => l.className = (l.dataset.status === d.status ? "on " : "") + l.dataset.status);
      evidence.classList.toggle("missing", d.status !== "pending" && !d.evidence.trim());
    };
    for (const [status, label] of Object.entries(data.labels)) {
      const input = el("input", {type: "radio", name: `${d.run_id}-${d.criterion}`, value: status});
      input.checked = d.status === status;
      input.addEventListener("change", () => { d.status = status; keep(); mark(); progress(); });
      const option = el("label", {}, input, label);
      option.dataset.status = status;
      choices.append(option);
    }
    evidence.addEventListener("input", () => { d.evidence = evidence.value; keep(); mark(); });
    right.append(el("div", {class: "criterion"}, el("p", {text: `${d.criterion}. ${d.rubric}`}), choices, evidence));
    mark();
  }
  right.append(el("div", {class: "nav"},
    el("button", {type: "button", class: "primary", text: "Save review.json", onclick: save}),
    index > 0 ? el("button", {type: "button", text: "Previous case", onclick: () => show(index - 1)}) : null,
    index < data.cases.length - 1 ? el("button", {type: "button", text: "Next case", onclick: () => show(index + 1)}) : null));
  window.scrollTo(0, 0);
  try { sessionStorage.setItem(key + "-case", index); } catch (e) { /* storage unavailable */ }
}
function save() {
  const blob = new Blob([JSON.stringify(review, null, 2) + "\\n"], {type: "application/json"});
  const link = el("a", {href: URL.createObjectURL(blob), download: "review.json"});
  document.body.append(link); link.click(); link.remove();
}
document.getElementById("save").addEventListener("click", save);
document.getElementById("load").addEventListener("click", () => document.getElementById("file").click());
document.getElementById("file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  let saved = null;
  try { saved = JSON.parse(await file.text()); } catch (e) { /* reported below */ }
  if (!restore(saved)) { alert("That file is not a review of this report."); return; }
  keep();
  for (const field of ["reviewer", "reviewer_role", "reviewed_at"]) document.getElementById(field).value = review[field];
  show(+select.value); progress();
});
let start = 0;
try { start = Math.min(+(sessionStorage.getItem(key + "-case") || 0), data.cases.length - 1); } catch (e) { /* none */ }
show(start); progress();
</script>
</body>
</html>
"""
