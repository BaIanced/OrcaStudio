# Handoff: OrcaStudio-Android + OrcaStudio aarch64 Flatpak (hot file, 2026-10-13)

Read this first. Don't use any title for the user ("Supreme Master" was a joke; never use it).
- `HANDOFF-REFERENCE.md`: devices, tools, build commands, recipes. **Read its device section before driving a device.**
- `HANDOFF-ARCHIVE.md`: history, verified features, file maps, past causes. Don't read it, `README.md` or `NOTES-*.md`
  up front; grep them when a question needs them (e.g. `grep -n "AMS mapping" HANDOFF-ARCHIVE.md`).

## Rolling handoff rules (user, 2026-10-12)
- Keep this file **under ~12 KB**: only state, the next task, open/untested items, safety gotchas and the rules.
  How-to material goes to `HANDOFF-REFERENCE.md`; verified work's details (runs, files, causes) go to the end of
  `HANDOFF-ARCHIVE.md` under a dated heading, leaving at most a one-line summary here.
- **Never move pending, open or untested information out of this file**, even to meet the size target.
- At each task boundary (task done + handoff updated), give a one-line cue: "`/clear` then `/next`", or "`/clear` then
  `/next-merge`" when verified work awaits a merge (say what it merges and what stays unverified). Never mid-task.
  Merge only on "merge" / `/next-merge` (= merge the verified, unmerged work, then carry on like /next; never untested commits).
- Update "Next task" before stopping any task.

## State
- Both repos work on `claude/handoff-continuation-rseql3`. Autonomy (user, 2026-10-11): decide branches and next steps
  yourself; **main merges / releases need the user**. Offer a merge when a batch is verified.
- Android main = r175 (b7986b0, PR #17, 2026-10-13: high refresh rate during input). Branch = main; nothing unmerged or
  unverified.
- Installed: Chromebook r173 (session = 1 cube on 1 plate, Tabs switcher, cut off). Phone r175 (session = test downloads, contents
  don't matter; old 8-plate session in `/data/local/tmp/phone-session-backup.{3mf,json}`). WSA r161 (AI tools on; auto-save
  60 s; session = backup `/data/local/tmp/session-backup.{3mf,json}`, 3 plates, plate 3 active).
- Test zip `scadzip-test.zip` stays in `/sdcard/Download` on phone + Chromebook.

## Next task
Nothing open can be done alone; nothing awaits a merge. Needs the user: the plate switcher pick (lab stays until they say), the user-only items below.

## User decisions (2026-10-13)
- A 3mf landing on the active plate over existing objects stays as is (arranging could move precisely placed objects).
- Plate activation must not move the camera when zoomed out (sometimes moving is fine).
- OpenSCAD: design view (main canvas) is the default; an **eye button** shows the design on the build plate and back, with
  the camera the user had on the plates, the project's objects hidden, and new designs on an empty plate.
- Plate switcher (tabs/filmstrip/chips): **keep the lab until the user says otherwise** (user, 2026-10-13, 3rd ask: don't ask
  again; mockups https://claude.ai/artifact/E3MtY8rQ1dMGHhibY2oNCX; More > Layout lab). Once picked: delete the losers and
  the lab (keep the wide panel tuck/width). Chips layout has no picking.
- Modeling goal: model **without writing code**; OpenSCAD code is only a backstop. Roadmap 1-3 done (archive).

## Open and untested items
0. Element blocker + ad-block menu (e4d75ab, a7e63d2): verified phone. **Untested:** mouse right-click (WSA), rules in other
   WebViews (Device page etc.); Orca Cloud login WebView (08bdf0b) needs a sign-out: leave to the user.
1. Preset re-link: verified. **Untested:** a Bambu/Orca cloud sync afterwards (cloud copy still detached; same updated_time,
   so the pull shouldn't replace it); the Chromebook desktop still has it detached.
2. Nozzle match + filament picks per AMS tray: verified. **Untested:** newer-firmware `device.nozzle.info` path; stale status
   after switching printer models; spool change -> printer's preset wins and the pick is dropped (only when the user swaps a
   spool); tray picks on WSA. Phone plate: 1 slot "Bambu PLA Basic @BBL A1".
3. Section view (r170/r172/r173): all verified (archive). Nothing open.
4. Shape builder: verified by touch + phone layout on the phone r134 (archive). Handles by touch on WSA: n/a (no touch).
5. .scad zips + Thingiverse downloads: verified. **Untested:** the 16 KB content sniff itself (r143 gets the real name first).
6. Ad blocking (f138655, ec86442, 08bdf0b = `AdBlock.Client` in all app WebViews): verified. **Untested:** MakerWorld sign-in /
   downloads with it on; Bambu sign-in WebView (needs Sign out + the user's password: leave to the user), Orca Cloud login,
   plugin pages, Device page on the phone (needs a printer with a web UI; the phone only has the A1).
7. OpenSCAD: phone layout r166/r168, real .scad download r142/r143, painting through a mesh boolean r175: all verified (archive).
8. Models tab **untested:** MakerWorld sign-in ticket flow.
9. **Untested:** a true EGL context loss (no repro). Badges are ~23 dp at plate zoom on the phone (under 48 dp; told the user).
10. User to retest: the 325 MB slice that crashed before the r59 OOM fix; pinch zoom on MakerWorld; whether a real keyboard's
    Ctrl+1 works (WSA drops synthetic Ctrl+1..9).
11. Orca plugin runtime: kept as a general capability (no plugin in use). Not done: audit prompts, create_window, per-preset
    config overrides, printerAgent capability. **FilamentHub is dropped for good; never suggest, test with, or mention it.**
12. REA MCP (github.com/morluto/rea), looked at 2026-10-12, not installed (needs the user's OK; changes MCP config): fits release
    APK / `liborca_jni.so` inspection and HAR traces of the MakerWorld / Thingiverse flows only.
13. Wishlist later: filament colour mixing (upstream `FilamentMixer.cpp`). Not wanted: iOS port. Flatpak r9 MakerLab tab,
    weekly upstream bump, obn follow-ups: archive (2026-10-12 trim).

## Safety gotchas
- **Any test print needs the user's OK.** User's AMS lite: A1 yellow, A2 matte black, A3 white, A4 PETG.
- 3D Filament Profiles (3dfilamentprofiles.com) is built in (Models tab site + "Log print"): **never press Subtract** in tests.
- Test on a temp Plate 2 and delete it after; don't change the user's Plate 1 (exception, user 2026-10-12: the phone's Plate 1
  objects and shape-builder draft are test objects). When deleting objects by list position, verify the selection first.
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
