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
- Android main = d231870 (PR #24, r203). Work branch = main + many commits since r204 (**not merged**; head 382eb15 = r221).
  Verified details of r204-r220 are in the archive ("2026-10-15: handoff trim"). Mergeable once the phone checks below pass.
- Installed: **r220 on phone + WSA + Chromebook + Shield** (2026-10-15). **r221 = run 38705941780 building** (started 2026-10-15).
  Install with `install-build.ps1 -Run <id> -Device <serial>` on all 4 (memory: install on all devices).
- Devices: phone = wireless `adb-...` entry; Chromebook ARC `<chromebook-ip>:5555` (reference); WSA `127.0.0.1:58526`; **USB serial = the user's
  SHIELD TV** (rooted; installs only; r210 settings/logins copied from the phone, sign-ins untested).
- **User is gaming on the PC: phone only, not WSA** (WSA needs window focus). User wants /clear cues often.
- User sessions backed up: phone `/data/local/tmp/phone-session-backup.{3mf,json}` (8 plates), WSA `/data/local/tmp/session-backup.{3mf,json}`.
  Test zip `scadzip-test.zip` stays in `/sdcard/Download` on phone + Chromebook. LAN access code was given in chat: never write it anywhere.
- **Plan (user, 2026-10-14):** camera LAN (done) -> off-LAN camera (cloud P2P path; REA on Handy is the tool; VPN-home the
  fallback) -> print history (capture Handy's history call, own client, Device tab) -> REA on MakerWorld. Own printer/account,
  personal use, own code only; rule 7 holds.

## Next task
1. **When r221 is green: install on all 4 devices, then test on the phone** (all r221 UNTESTED): zoom toward the fingers / wheel
   cursor (`Camera.zoomAt`); stage 2 contact shadow (`render/SceneEffects.kt`: top-down R8 map, max blend, MESH_FS pass 3 fades
   over 12 mm, 2 blur rounds, quad under the grid, Prepare only, strength 0.55) - look + follows a drag; stage 3 SSAO (half-res
   depth pre-pass, `SSAO_FS` 12 samples radius 3/6 mm, bilateral blur, multiplied after opaque geometry incl. toolpaths) Soft/Full
   on Prepare + Preview; FPS (counter top left). Settings: More > Appearance "3D view: ambient occlusion" Off/Soft/Full (default
   Off) + "shadows under objects" (default on). Also recheck close up on a box wall in Preview (zoom limit ~2.5 px per layer).
2. **Phone checks waiting on the user** (ask; all UNTESTED on the phone):
   - r214 object-drag jump-back fix (`PlateView.kt` release branch, `Viewport.kt` `dragPending`, `SceneController.moveSelected` -> Job): drag an object.
   - r215 single-filament slice crash fix (`OrcaEngine.cpp` ~507: rebuild `flush_volumes_matrix` for `>= 1` filaments) and r217
     dual-nozzle fix (one n*n block per nozzle: `heads = max(1, multiplier, nozzle_diameter count)`): slice with the X2D selected.
   - r216 projects keep the current printer (`FileController.openProjectFile`, toast `project_printer_kept`; session restore still restores its printer).
   - r218 Preview colour-scheme pill opens from its text too (`Surface(onClick)`).
   - r213: settings tabs swipe repeatedly (stale `current` fix, `SettingsEditor.kt`), haptics (settings tabs TextHandleMove, Models
     edge swipes CLOCK_TICK), import 2 files onto a plate with objects (own-plate rule), site-tab line visible (pinned to tab bottom).
   - r211: object settings editor on the phone.
   - Camera card: wrong access code, unreachable printer, on the phone.
   - 165 Hz: added the app (`7-0-0-7`) to `/data/system/refresh_rate_config_user_override.xml` (backup
     `/data/local/tmp/refresh_override.bak`); ask whether the refresh-rate setting now lists it.
3. **Not done / ideas:** auto-select the A1 on the MakerWorld/MakerLab page at load (look at how the site stores its printer pick;
   CDP on the Models WebView); a slice/print-time guard comparing the sliced printer with the connected one; a line under inactive
   settings tabs (user's idea). 3D stage 4 wishlist: real shadow map. Preview colours stay flat on purpose.
4. **Nav proposal (awaiting user OK; analysis 2026-10-14, nothing changed):** Back = AppScaffold.kt:148; Models back + edge swipes
   ModelsScreen.kt:464/:182; settings tab swipe SettingsEditor.kt:303. Gap: no BackHandler for the OpenSCAD editor (`state.scad`,
   AppScaffold.kt:281 -> Back opens the quit prompt), the eye "design on plate" mode, the section panel, the design panel.
   Proposal: Back in OpenSCAD = on-plate view -> design view -> `scad.close()`; optional horizontal swipe between main tabs (not on Prepare).
5. Then: the plate switcher pick (lab stays until they say), the user-only items below.

Still open from earlier batches: **root cause of the r197 NumberField NPE not found** (stack traces now logged under `OrcaStore`);
"failed OpenSCAD run clears the old log" **untested** (no repro); **unexplained:** once a freshly resized portrait window on WSA drew
the Prepare 3D background ~30 % lighter for ~15 s. Design mode known limits: hard-coded colours (delete popup #2B2C32, red bin,
preview legend) don't follow; the Models page keeps its own colours; a dark 3D background under a light theme hides the floating
tool icons ("Prepare: floating buttons" can be changed). User-only: retests, plate switcher pick, launcher icon colour (still teal, "decide later").

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

## Open and untested items
0. Element blocker + ad-block menu (e4d75ab, a7e63d2): verified phone; mouse right-click verified WSA r194. **Untested:**
   rules in other WebViews (Device page etc.; needs a printer with a web UI). User 2026-10-13: MakerWorld, Printables and Orca sign-ins work; a Google-account Orca
   sign-in goes through Brave (not the WebView). Bambu sign-out is Device tab > Connection > Sign out (told the user).
1. Verified, nothing open (archive): preset re-link + syncs, section view, shape builder, .scad zips / 16 KB sniff, OpenSCAD
   phone layout / downloads / painting, MakerWorld sign-in ticket flow.
2. Nozzle match + filament picks per AMS tray: verified. **Untested:** newer-firmware `device.nozzle.info` path; stale status
   after switching printer models; spool change -> printer's preset wins and the pick is dropped (only when the user swaps a
   spool). Tray picks on WSA r194: verified. Phone plate: 1 slot "Bambu PLA Basic @BBL A1".
6. Ad blocking (f138655, ec86442, 08bdf0b = `AdBlock.Client` in all app WebViews): verified; MakerWorld sign-in / downloads with
   it on, Bambu sign-in WebView, Orca Cloud login verified by the user 2026-10-14. **Untested:** plugin pages, Device page on
   the phone (needs a printer with a web UI; the phone only has the A1).
9. **Untested:** a true EGL context loss (no repro). Badges are ~23 dp at plate zoom on the phone (under 48 dp; told the user).
10. User to retest: the 325 MB slice that crashed before the r59 OOM fix. MakerWorld pinch zoom works (user 2026-10-14).
    Real keyboard Ctrl+1 (camera top view, MainActivity.kt:190) does nothing: the system takes it as a hotkey (user
    2026-10-14). Offered: numpad 0-7 as an extra view binding (not done, untested).
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
