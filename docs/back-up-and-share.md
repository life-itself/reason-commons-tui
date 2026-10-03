# Back up, share and move goals

Each goal is a plain folder. By default they live in `~/ReasonCommons`, one folder
per goal.

## Back up or share a goal

In the workspace, press **Ctrl+P** and choose **Export case**. Reason Commons
suggests a file next to the goal's folder, such as
`~/ReasonCommons/in-bed-by-23-00-2026-10-12.reasoncase`; press Enter to write it.
Use a new file name each time.

From the command line:

```sh
reason-commons export ~/ReasonCommons/in-bed-by-23-00 ~/Desktop/in-bed.reasoncase
```

A `.reasoncase` file is a complete, portable copy: send it, keep it or archive it.

## Look inside a copy without changing it

```sh
reason-commons show ~/Desktop/in-bed.reasoncase
```

## Continue from a copy

Import it into a new folder, then open that folder:

```sh
reason-commons import ~/Desktop/in-bed.reasoncase --store ~/ReasonCommons/in-bed-copy
reason-commons
```

The destination folder must not exist yet. The copy carries the whole history.

## Keep goals somewhere else

Set `REASON_COMMONS_HOME` to another folder (for example a synced one) and
`reason-commons` lists the goals there:

```sh
export REASON_COMMONS_HOME=~/Documents/ReasonCommons
```

You can also open any folder directly: `reason-commons tui ~/Projects/my-goal`
creates or opens it, and `reason-commons resume ~/Projects/my-goal` opens it but
never creates one.

## Good to know

- Only one workspace can edit a goal at a time. Quit it in one window before
  opening it in another.
- Remove a goal by deleting its folder. Export it first if you may want it later.
