# Handoff: OrcaStudio-Android + OrcaStudio aarch64 Flatpak (hot file, 2026-10-13)

Read this first. Don't use any title for the user ("Supreme Master" was a joke; never use it).
- `HANDOFF-REFERENCE.md`: devices, tools, build commands, recipes. **Read its device section before driving a device.**
- `HANDOFF-BACKLOG.md`: pending / untested / ideas / user decisions waiting. Grep it; don't read it up front.
- `HANDOFF-ARCHIVE.md`: history, verified features, file maps, past causes. Don't read it, `README.md` or `NOTES-*.md`
  up front; grep them when a question needs them (e.g. `grep -n "AMS mapping" HANDOFF-ARCHIVE.md`).

## Rolling handoff rules (user, 2026-10-12; full text in the /next skill)
- **Under ~8 KB** (`wc -c` at every update; prune before stopping): state, 1-3 tasks in progress, gotchas, rules. How-to ->
  `HANDOFF-REFERENCE.md`; verified details -> end of `HANDOFF-ARCHIVE.md` (dated), one line here.
- Pending/untested items live in `HANDOFF-BACKLOG.md` (one line each, never deleted; archived once verified).
- Task boundary cue: "`/clear` then `/next`", or "`/clear` then `/next-merge`" when verified work awaits a merge (say what
  merges, what stays unverified). Never mid-task. Merge only on "merge" / `/next-merge`, never untested commits.
- **Log user verdicts first** (archive line with date/build/their words, backlog line, one-liner here) before anything else.
- **User-only items** (feel, look, prints): grep the archive; if the last verdict predates the latest build, ask one line first.

## State
- Both repos work on `claude/handoff-continuation-rseql3`. Autonomy (user, 2026-10-11): decide branches and next steps
  yourself; **main merges / releases need the user**. Offer a merge when a batch is verified.
- Android main = ab790b9 (PR #30, r276, merged 2026-10-16); work branch up to dff57e4 (r281-r285: grip/top bar/fling, lab crash, preview fixes), unmerged.
- Installed: r285 on phone + SHIELD, r280 on WSA; Chromebook offline (lacks r271+). `install-build.ps1 -Run <id> -Device <serial>`.
- Devices: phone = wireless `adb-...` entry; Chromebook ARC `<chromebook-ip>:5555` (reference); WSA `127.0.0.1:58526`; **USB serial = the user's
  SHIELD TV** (rooted; installs only).
- **User gaming (2026-10-17, 1-2 h): test on the phone (user: "Abandon shield", installs only); if the user is on it, wait
  60 s and retry. Don't use WSA (PC busy).** User wants /clear cues often.
- User sessions backed up: phone `/data/local/tmp/phone-session-backup.{3mf,json}` (8 plates), WSA `/data/local/tmp/session-backup.{3mf,json}`.
  Test zip `scadzip-test.zip` stays in `/sdcard/Download` on phone + Chromebook. LAN access code was given in chat: never write it anywhere.
## Next task
**r285 (run 39017596686, dff57e4; phone + SHIELD):** Claude-verified (archive "r285 fixes"): Layout lab opens; Preview is
camera-only; preview crack dots + seam glitch gone. User to judge: preview look while moving the camera.
Answered in chat: shadows are Prepare-only by design (desktop has none; AO removed r27x); zoom: user to try the lab's pinch
speed slider before a zoom-dependent curve. **Next: printer controls on the Device tab like Handy's** (backlog spec, HIGH).
User hasn't seen: bead look, part shadows, light sliders, tool row move/collapse (r276, merged). Haptics verified.
r283/r284 top bar + flick feel, r280 pinch lock feel: user-only. WSA still on r280 (install when the user is off the PC).
Test tools: `mcpao.sh view_state` (3D), `phone-ui.py <serial> layout` (2D); reference "Build and tools". MCP ideas: backlog.
Waiting on the user: plate switcher pick.

## User decisions (2026-10-13)
- (2026-10-14) Each newly imported file gets its own plate (active if empty, else first empty, else new; `FileController.useEmptyPlate`).
- Plate activation must not move the camera when zoomed out (sometimes moving is fine).
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
