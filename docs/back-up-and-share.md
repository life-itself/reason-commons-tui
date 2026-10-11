# Back up, share and move goals and trees

Each goal is a plain folder. By default they live in `~/ReasonCommons`, one folder
per goal.

## Back up or share a goal

In the workspace, press **Ctrl+P** and choose **Export commons**. Reason Commons
suggests a file next to the goal's folder, such as
`~/ReasonCommons/first-practice-2026-11-09.reasoncase`; press Enter to write it.
Use a new file name each time.

From the command line:

```sh
reason-commons export ~/ReasonCommons/first-practice ~/Desktop/first-practice.reasoncase
```

A `.reasoncase` file is a complete, portable copy: send it, keep it or archive it.

## Look inside a copy without changing it

```sh
reason-commons show ~/Desktop/first-practice.reasoncase
```

## Continue from a copy

Import it into a new folder, then open that folder:

```sh
reason-commons import ~/Desktop/first-practice.reasoncase --store ~/ReasonCommons/first-practice-copy
reason-commons
```

The destination folder must not exist yet. The copy carries the whole history, original source bytes, proposal membership,
acceptance decisions and cursor. Existing `.reasoncase` archives and `case` keys
remain compatible; delivery increment changes do not migrate them.
For the accepted reconstructed development import, see
[the working-import guide](restoration/working-import.md).

## Bring trees in or out

Trees can travel on their own as an `.ltp.yaml` file, the format the
[Reason Commons guide](https://github.com/life-itself/reasoncommons/tree/main/ltp)
uses. In the workspace, press **Ctrl+P** and choose **Import trees** or **Export
trees**. What a file brings in waits in **Backlog** until you accept it, then joins
the trees already in the goal; the file's goal is proposed as your goal, or as a new
version of it. Anything the trees
cannot draw yet, such as a joint cause, is kept as a note.

From the command line:

```sh
reason-commons trees ~/ReasonCommons/first-practice --import analysis.ltp.yaml
reason-commons trees ~/ReasonCommons/first-practice --export ~/Desktop/analysis.ltp.yaml
reason-commons trees ~/ReasonCommons/first-practice --tree current_reality
```

The last command draws one tree in the terminal without opening the workspace.

## Keep goals somewhere else

Set `REASON_COMMONS_HOME` to another folder (for example a synced one) and
`reason-commons` lists the goals there:

```sh
export REASON_COMMONS_HOME=~/Documents/ReasonCommons
```

You can also open any folder directly: `reason-commons tui ~/Projects/my-goal`
creates or opens it, and `reason-commons resume ~/Projects/my-goal` opens it but
never creates one.

## Keep goals in a git repository

To share goals with the people working on a repository, keep them in it. Put each
goal's folder under `commons/` at the repository's root, and add to its
`.gitignore`:

```gitignore
commons/*/writer.lock
commons/*/cursor.yaml
```

`writer.lock` exists only while a goal is open, and `cursor.yaml` holds your own
draft and view. A clone without `cursor.yaml` opens the goal at its current
question.

So that the skill in Claude Code uses the repository's goals, commit
`.claude/settings.json` with:

```json
{"env": {"REASON_COMMONS_HOME": "commons"}}
```

Claude Code then starts the plugin's server on `commons/` whenever it is opened in
this repository; elsewhere it keeps using `~/ReasonCommons`. In the workspace, run
it from the repository's root with the same setting:

```sh
REASON_COMMONS_HOME=commons reason-commons
```

**Take turns.** Pull before you work on a goal and commit and push when you stop.
Git cannot merge two people's additions to the same goal: both would write the
same next revision, and the commit that arrives second conflicts. Different goals
in the same repository never conflict. Everything in the folder, including
consultant receipts, is published with the repository.

## Good to know

- Only one workspace can edit a goal at a time. Quit it in one window before
  opening it in another.
- Remove a goal by deleting its folder. Export it first if you may want it later.
