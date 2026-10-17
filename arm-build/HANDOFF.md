# Handoff: OrcaStudio-Android + OrcaStudio aarch64 Flatpak (hot file, 2026-10-13)

Read this first. Don't use any title for the user ("Supreme Master" was a joke; never use it).
- `HANDOFF-REFERENCE.md`: devices, tools, build commands, recipes. **Read its device section before driving a device.**
- `HANDOFF-BACKLOG.md`: pending / untested / ideas / user decisions waiting. Grep it; don't read it up front.
- `HANDOFF-ARCHIVE.md`: history, verified features, file maps, past causes. Don't read it, `README.md` or `NOTES-*.md`
  up front; grep them when a question needs them (e.g. `grep -n "AMS mapping" HANDOFF-ARCHIVE.md`).

## Rolling handoff rules (user, 2026-10-12)
- Keep this file **under ~8 KB**: only state, the 1-3 tasks in progress, safety gotchas and the rules.
  How-to material goes to `HANDOFF-REFERENCE.md`; verified work's details (runs, files, causes) go to the end of
  `HANDOFF-ARCHIVE.md` under a dated heading, leaving at most a one-line summary here.
- **Pending, open and untested items live in `HANDOFF-BACKLOG.md`** (one line each; never delete them there, only move them to the archive once verified). Pull an item into "Next task" when you start it.
- At each task boundary (task done + handoff updated), give a one-line cue: "`/clear` then `/next`", or "`/clear` then
  `/next-merge`" when verified work awaits a merge (say what it merges and what stays unverified). Never mid-task.
  Merge only on "merge" / `/next-merge` (= merge the verified, unmerged work, then carry on like /next; never untested commits).
- Update "Next task" before stopping any task.
- **Log user verdicts first (2026-10-16; lost ones caused re-test loops):** when the user says an item works / is fixed /
  is still broken, before any other step: archive line (date, build, their words), fix/remove its backlog line, one-liner here.
- **User-only items:** before working on an item only the user can check (feel, look, real print), grep the archive; if its
  last verdict predates the latest build, ask the user one line ("still broken on rNNN?") instead of fixing or testing it.
- Over ~8 KB (`wc -c` at every update) means prune before stopping. Pending/untested text goes to the backlog, never deleted.

## State
- Both repos work on `claude/handoff-continuation-rseql3`. Autonomy (user, 2026-10-11): decide branches and next steps
  yourself; **main merges / releases need the user**. Offer a merge when a batch is verified.
- Android main = ab790b9 (PR #30, r276, merged 2026-10-16); work branch +94bb1e6 (MCP `view_state`, unmerged).
- Installed: r278 on phone, SHIELD, WSA; Chromebook offline (lacks r271+). `install-build.ps1 -Run <id> -Device <serial>`.
- Devices: phone = wireless `adb-...` entry; Chromebook ARC `<chromebook-ip>:5555` (reference); WSA `127.0.0.1:58526`; **USB serial = the user's
  SHIELD TV** (rooted; installs only).
- **User is at work (2026-10-16): free rein, WSA usable** (needs window focus). User wants /clear cues often.
- User sessions backed up: phone `/data/local/tmp/phone-session-backup.{3mf,json}` (8 plates), WSA `/data/local/tmp/session-backup.{3mf,json}`.
  Test zip `scadzip-test.zip` stays in `/sdcard/Download` on phone + Chromebook. LAN access code was given in chat: never write it anywhere.
## Next task
**Grep the archive before re-testing anything.** User hasn't seen: bead look, part shadows, light sliders. Haptics verified (archive 2026-10-16).
**Tool row move/collapse** r276 merged (PR #30, archive). User hasn't tried it (portrait, Layout lab "tools in a column" off).
**NEXT 1 (user, 2026-10-17): rotating portrait -> landscape crashes the app (phone, r278).** Trace saved:
`~/orca-android-tools/crash-2026-10-17-rotate.txt`: `IllegalArgumentException: performMeasureAndLayout called during
measure layout` (Compose re-entrant measure), but R8-obfuscated, and CI keeps no `mapping.txt`. First upload
`app/build/outputs/mapping/release/mapping.txt` as an artifact in `android-apk.yml` (makes every crash dump readable).
Suspects: r276's movable tool row (kept-on-screen clamp on resize, 16e1960/24fe798) and anything that measures or lays out
synchronously from a size or layout callback (the PlateView AndroidView). Repro on the phone (`content rotation` via
`settings put system user_rotation`) or WSA, then check with `phone-ui.py layout` / `view_state`.
**NEXT 2 (user, 2026-10-17): pinch zoom too sensitive in the plate 3D view; fingers close together also register a drag
(pan/move) during the pinch.** Look at the pinch handling in `render/PlateView.kt` (scale factor per event, drag vs
pinch switch on pointer count / finger gap). Tune or "calibrate" it, but **keep the very deep zoom-in** (user wants it).
If the sensitivity can't be separated from the deep zoom, the user accepts it as is: say so.
**Token-saving test tools (2026-10-17):** MCP `view_state` (94bb1e6, r278, run 39010234734; Claude-verified on WSA:
tapping a copy's box centre selected it) = 3D view as text: camera, mode/tool, selection, screen-px boxes of
plates/copies/towers. Use `mcpao.sh 'view_state:{}'` instead of screenshots. Other UI: `phone-ui.py <serial> layout [regex]`.
Next candidates (asked by the user): `slice` + `slice_result` (all users), then debug-only `app_state`, `log_tail`, `perf`.
Phone tools: `~/orca-android-tools/mcpao.sh 'tool:{json}'` (phone MCP, token never printed). `adb pair` needs the code on the command line.
Waiting on the user: plate switcher pick.

## User decisions (2026-10-13)
- (2026-10-14) Each newly imported file gets its own plate (active if empty, else first empty, else new; `FileController.useEmptyPlate`).
- Plate activation must not move the camera when zoomed out (sometimes moving is fine).
- OpenSCAD eye-button decision (2026-10-13): built + verified r166, details in the archive.
- Plate switcher: **keep the lab until the user says otherwise; don't ask again** (mockups https://claude.ai/artifact/E3MtY8rQ1dMGHhibY2oNCX).
  Once picked: delete the losers and the lab (keep the wide panel tuck/width).
- Modeling goal: model **without writing code**; OpenSCAD code is only a backstop. Roadmap 1-3 done (archive).

## Safety gotchas
- **Any test print needs the user's OK.** User's AMS lite: A1 yellow, A2 matte black, A3 white, A4 PETG.
- 3D Filament Profiles (3dfilamentprofiles.com) is built in (Models tab site + "Log print"): **never press Subtract** in tests.
- **User 2026-10-15: all build plates/objects on the devices are currently throwaway test objects with no real-life significance (until the user says otherwise). Standing permission to move, reassign, delete or rearrange anything; no need to avoid or restore them.** Still verify the selection before deleting by list position. (Prints still need the user's OK.)
- **Never `cat missing > target`** (the redirect empties the target first).
- **Never `adb forward tcp:X tcp:Y` on WSA** (wedges adb); use `localabstract:orcastudio_mcp` (reference "WSA").

## Working rules (the user asked for these)
1. **Verify against source before recommending any change**; cite file:line.
2. Label anything untested as untested, inline.
3. Before any shell command the **user** must run, print a pre-flight block: 1. BLIND SPOTS,
   2. EXTRAPOLATED RISKS (2), 3. CAPABILITY VALIDATION (YES/NO). Direct verdicts, brief.
4. Keep check-ins cheap: one background `gh run watch`, not polling loops.
5. Approved: pushes and `android-apk.yml` dispatches on the work branches without asking. **Merging
   to main or publishing releases needs the user's go-ahead.**
6. **Never print, sign out or delete presets without asking.** Standing permission for an autonomous test-and-fix loop on
   WSA otherwise. Don't change the user's plate (their project is on it); close the app when done.
7. **Secrets:** the user's `slicer_cert.pem` / `slicer_key.pem` / `slicer_crl.pem` never go in a
   repo or bundle; never explain how to obtain them. `obn.auth.json`, trace logs and session files
   contain tokens: ask only for filtered output.
8. **Both repos are public: no identifying details** (serials, IPs, e-mail, account / display names,
   MakerWorld handle, device models, tokens) in files, commits or PR text. Use placeholders. Run the
   privacy scan before every push (python is `python` on this PC):
   - Android: `python .claude/hooks/privacy_scan.py range "HEAD --not --remotes" . ':(exclude)src-orca'`
   - OrcaStudio: `python .claude/hooks/privacy_scan.py range "HEAD --not --remotes" arm-build '.github/workflows/arm-*' .claude`
9. Commit trailer: `Co-Authored-By` + `Claude-Session` lines as given in the session.
11. **Model fit (user, 2026-10-16):** when a task would be better suited to Opus (hard rendering/shader/math debugging, subtle multi-file design, after 2 failed attempts), say so before starting or as soon as it shows, and tell the user to `/model` swap and `/next`. Otherwise stay on the current model.
10. Efficiency (user, 2026-10-10): compile Kotlin locally before every push (command in the reference); batch 2-4 changes per
    build, don't dispatch builds that will be superseded; write code with Edit or python raw strings, never plain python
    heredocs (they ate backslashes 5x); write python scripts with Write, then run them.
