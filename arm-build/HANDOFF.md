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
- **Auto-prune (user, 2026-10-15; the old rule kept lapsing):** the moment the user or a test verifies an item, in the same edit move its details to the archive (dated heading) and leave a one-liner. Check the file size at every handoff update; over ~8 KB means prune before stopping. Pending/untested text goes to the backlog, never deleted.

## State
- Both repos work on `claude/handoff-continuation-rseql3`. Autonomy (user, 2026-10-11): decide branches and next steps
  yourself; **main merges / releases need the user**. Offer a merge when a batch is verified.
- Android main = 3048a5d (PR #25, r243, merged 2026-10-15). Work branch = main (nothing unmerged). Verified details of r204-r243 are in the archive.
- **Built 2026-10-15: r245 (run 38844142457, head 8506c3c), installed on all 4 devices (phone done 2026-10-15 after wireless adb returned).** Carries the German strings, L2 and L4 (all UNTESTED). Earlier install history: archive.
  Install with `install-build.ps1 -Run <id> -Device <serial>` on all 4 (memory: install on all devices). Chromebook is now `.33:5555`.
- Devices: phone = wireless `adb-...` entry; Chromebook ARC `<chromebook-ip>:5555` (reference); WSA `127.0.0.1:58526`; **USB serial = the user's
  SHIELD TV** (rooted; installs only; r210 settings/logins copied from the phone, sign-ins untested).
- **User is gaming on the PC: phone only, not WSA** (WSA needs window focus). User wants /clear cues often.
- User sessions backed up: phone `/data/local/tmp/phone-session-backup.{3mf,json}` (8 plates), WSA `/data/local/tmp/session-backup.{3mf,json}`.
  Test zip `scadzip-test.zip` stays in `/sdcard/Download` on phone + Chromebook. LAN access code was given in chat: never write it anywhere.
## Next task
User verified 2026-10-15 (r249): opacity readout card works (but overlapped the tool bar: fixed in a853161, centred; build run 38857868372, UNTESTED), L1 fold jump fixed, L3 status error card good, all sliders good. Haptics: only Back/forward gestures vibrate (settings tabs, Models edge swipes don't; unfixed, can't test over adb). Details to archive when pruning.
Built run 38858438386 (head ca2a96d: readout card centred a853161, Sign out own row b74e8ea, preview top/bottom bead shading ca2a96d) installed on the 3 reachable devices 2026-10-16, Chromebook autopilot 2026-10-16: X2D 0.4 slice OK, no crash (r215/r217 fixes VERIFIED); top-surface bead shading visible when zoomed in (flat zoomed out, by design); printer reset to A1. Still UNTESTED on device: Sign out row, readout card position, model-mismatch guard (user asked for the preview look and the horizontal Sign out). Todo: (2) autopilot on the phone (user OK'd, 2026-10-15): slice with the X2D selected (r215/r217 crash fixes) and the model-mismatch guard; phone was NOT on wireless adb at the time (only SHIELD USB + WSA + Chromebook), so wait for it; (3) merge: user-verified commits dca0db0, 9bca6b7, 9fe3f66, 54b4ca6 (L1/L3 now verified), ca874e4 + a853161 after test; German strings stub; ask for "merge".
Waiting on the user: plate switcher pick (still undecided). Launcher icon colour removed from the list.

## User decisions (2026-10-13)
- **Changed 2026-10-14:** objects already in the project stay on their plate; each newly imported file gets a plate of its own
  (active plate if empty, else first empty, else a new one; `FileController.useEmptyPlate`). Replaces the 2026-10-13 rule that a file lands on the active plate.
- Plate activation must not move the camera when zoomed out (sometimes moving is fine).
- OpenSCAD: design view (main canvas) is the default; an **eye button** shows the design on the build plate and back, with
  the camera the user had on the plates, the project's objects hidden, and new designs on an empty plate.
- Plate switcher (tabs/filmstrip/chips): **keep the lab until the user says otherwise** (user, 2026-10-13, 3rd ask: don't ask
  again; mockups https://claude.ai/artifact/E3MtY8rQ1dMGHhibY2oNCX; More > Layout lab). Once picked: delete the losers and
  the lab (keep the wide panel tuck/width). Chips layout has no picking.
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
10. Efficiency (user, 2026-10-10): compile Kotlin locally before every push (command in the reference); batch 2-4 changes per
    build, don't dispatch builds that will be superseded; write code with Edit or python raw strings, never plain python
    heredocs (they ate backslashes 5x); write python scripts with Write, then run them.
