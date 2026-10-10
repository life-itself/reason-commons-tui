---
name: publish-review
description: Publish a semantic-evaluation review package (built by scripts/review_screens.py) as a private claude.ai page that reviewers open by link, or pull the reviewers' review.json files from one already published. Use when asked to publish, share or update a review package, or to collect its reviews.
---

# Publish a review package

A review package is a folder made by `python3 scripts/review_screens.py REPORT.json` (by default
`review-package/` beside the report). It holds `index.html`, `cases/case-NN.js` and `publish.json`,
which is the publish call to make.

## Publish

1. If the folder does not exist yet, build it: `python3 scripts/review_screens.py <report.json>`.
2. Read `publish.json` and `index.html` (the Artifact tool requires reading a file before publishing it;
   the conversation files are generated screen data, one per conversation).
3. Call the Artifact tool once with `file_path` = `<package>/index.html`, `root` = the package folder,
   `files` = `publish.json`'s `files`, `capabilities` = `publish.json`'s `capabilities`, `icon`,
   `description`. The page's `<title>` is its name.
4. Do one check: `ArtifactData` `list` of collection `reviews` (empty until someone opens the page).
5. Give the person the link and say: share it from the page's Share menu with each reviewer as a
   **Contributor** (Viewers and Commenters can look but cannot record decisions). Each reviewer's
   decisions save under their own account; only the reviewer and the page's owner can read them.

To publish a new run, build a new package and publish it as a new page; one page reviews one report
(decisions are bound to its `report_sha256`).

## Collect the reviews

The owner can save each reviewer's `review.json` from the Reviewers table on the page. Or collect them
all here: `ArtifactData` `list` of collection `reviews` with `out_dir` set to a new folder (one JSON file
per reviewer, holding their name, background and answers to the plain questions), then run
`python3 scripts/review_screens.py <report.json> --collect <that folder> --output <new folder>`. It
combines each reviewer's answers into the rubric's decisions (every question Yes is a pass, any No a
fail, otherwise can't judge; a question the reviewer did not understand leaves the criterion undecided)
and writes `review-<name>.json`. Check each with
`python3 scripts/review_evaluation.py <report.json> --review <file> --output <new reviewed.json>`.
Report the questions reviewers marked "I don't understand the question": they show which plain
questions in `evaluations/review_questions.py` need rewriting.
