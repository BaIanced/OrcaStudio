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
- Android main = r194 (541c5c4, PR #22, 2026-10-14; r192-r194 selection colour + design mode dialog samples, verified
  phone + Chromebook; archive "r192-r194"). Work branch = main (nothing unmerged, nothing unverified).
- Installed: Chromebook r193 (2026-10-14; landscape now; restored to Dark + Prusa default, no
  custom colours, wallpaper off; session = 1 cube on 1 plate). Phone r194 (Dark + Prusa default restored; fullscreen portrait
  lab on (user's setting); session =
  test downloads; old 8-plate session in `/data/local/tmp/phone-session-backup.{3mf,json}`). WSA r194 (2026-10-14; AI tools
  on; auto-save 60 s; Dark + Prusa default; current session empty, the user's is in `/data/local/tmp/session-backup.{3mf,json}`;
  slots Basic/Matte/Matte/PETG from sync, `tray_picks` {}, ad-block rules {}).
- A TV box shows up in `adb devices` (USB serial, 2026-10-14): not a test device, leave it alone.
- Test zip `scadzip-test.zip` stays in `/sdcard/Download` on phone + Chromebook.

## Next task
**Design mode is done, verified on all three devices and merged (r180-r194, main r194).** r179/r178 landscape verified on the Chromebook (archive "r179 delete popup + r178 design view in landscape"). Item 5's 16 KB sniff verified 2026-10-14 (Chromebook). WSA r194 2026-10-14: item 0 mouse right-click and item 2 tray
picks verified (archive "WSA r194 element blocker right-click + tray picks"). **User away from the PC (2026-10-14), standing orders:** (1) numpad camera views: **verified WSA r196** (Num Lock on: 1 = top,
3 = front, 7 = frame plate; Num Lock off: no change). (2) Blind bug hunt, in progress on the work branch (no main merge): random-input
fuzz (`scratchpad/fuzz.sh`, ~470 steps, no crash), then targeted edge cases. **Fixed, on the work branch, UNMERGED** (r197-r200,
67098ce): Shape dialog Add off outside 0.1-1000 mm + chips wrap (Cone was a sliver); typed scale clamped 0.1 %-100x; NumberField rejects
NaN/Infinity/|x|>1e6 (they ended in a raw NPE error dialog; **cause of that NPE not found**, stack traces now logged under tag
`OrcaStore`); "(s)" strings -> plurals (objects outside, files imported; **others still "(s)"**: cloud/preset sync toasts, ai_confirm_save);
failed OpenSCAD run clears the old log. Verified on WSA r197-r199: dialog validation, scale clamp, NaN rejected. **Untested:** plurals +
stale-log fix (r200 build 38579919475). Not bugs: OpenSCAD recursion bomb / 420k-triangle loop handled; lab sliders 50-130 %, filmstrip digits
bottom-aligned on purpose. WSA quirk: the app window jumps position; get offsets from the `Prepare` label in `ui.ps1`. (3) Then design polish:
centering, sizing, consistency. 
Sign-ins + cloud syncs done by the user 2026-10-14 (archive "sign-ins + cloud sync"). User-only: retests, plate switcher pick, launcher icon colour (still teal; user
2026-10-14: "decide later"). Background:
**Colour presets + design mode (user, 2026-10-14: "code all three as presets, in addition to the customizer; you
categorize everything").** **Verified on WSA r182** (presets, live design mode, per-part overrides, resets, restart; details: archive
"2026-10-14: design mode r182-r187").
- Panel: drag by header, fold, close; preset chips, "Part of the app" dropdown (14 parts), a row of colour chips (• = custom)
  with the slot's hint, HSV sliders + hex + swatches, Reset this part / Reset all. Colours per light/dark mode; sliders save
  on release. Design mode itself isn't kept over a restart (by design).
- Code: `ui/theme/AppColors.kt` (schemes moved from MainActivity; Role/Slot/Region/ThemePreset; `withRoles` derives Material
  slots; `Themed(region)` = nested MaterialTheme; `OrcaTheme`), `ui/theme/DesignPanel.kt`, `core/ThemeSpec.kt` (prefs
  `theme_spec` JSON). Regions wired in `AppScaffold.kt`; 3D view `Viewport.kt` + badges `PlateBadgeAtlas.kt` read slots.
- **Verified on the Chromebook (portrait) 2026-10-14:** Industrial/Minimal light by eye, floating panel fits above the tab bar,
  tab bar slots, Device + Settings editor regions (dark background in light mode, r184+), wallpaper colours + overrides,
  panel Reset all (no confirm in the panel; More's "Reset custom colors" confirms). Also on r185 (light, Background
  #1E293B per region): More, Models (toolbar/chips), OpenSCAD editor read fine; Preview sheet came out slate grey (fixed r187).
- r187 fd4361d (dark-Background sheets, contrast warning, drag strip): verified + merged (archive "2026-10-14: r187"); its
  snackbar shading verified with r189.
- Phone r189 checks, dialogs (sample + real error dialog; busy/AI-confirm share `GlobalDialogs`), 3D selection colour:
  all verified (archive "r189 + r190", "r192-r194"). Nothing open in design mode except the known limits below.
- Known limits: hard-coded colours (delete popup #2B2C32, red bin, preview legend) don't follow; the Models web page keeps
  its own colours. A dark 3D background under a light theme hides the floating tool icons (user's choice; "Prepare: floating
  buttons" can be changed to match).

**r179 de39e04** delete popup + r178 design view: verified r189 (portrait) and Chromebook r193 (landscape).
Slice button = primaryContainer; the user can set "Soft accent" in design mode. Launcher icon still teal (asked the user).

Then: the plate switcher pick (lab stays until they say), the user-only items below.

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
0. Element blocker + ad-block menu (e4d75ab, a7e63d2): verified phone; mouse right-click verified WSA r194. **Untested:**
   rules in other WebViews (Device page etc.; needs a printer with a web UI). User 2026-10-13: MakerWorld, Printables and Orca sign-ins work; a Google-account Orca
   sign-in goes through Brave (not the WebView). Bambu sign-out is Device tab > Connection > Sign out (told the user).
1. Preset re-link + cloud syncs afterwards: verified (syncs by the user 2026-10-14). Nothing open.
2. Nozzle match + filament picks per AMS tray: verified. **Untested:** newer-firmware `device.nozzle.info` path; stale status
   after switching printer models; spool change -> printer's preset wins and the pick is dropped (only when the user swaps a
   spool). Tray picks on WSA r194: verified. Phone plate: 1 slot "Bambu PLA Basic @BBL A1".
3. Section view (r170/r172/r173): all verified (archive). Nothing open.
4. Shape builder: verified by touch + phone layout on the phone r134 (archive). Handles by touch on WSA: n/a (no touch).
5. .scad zips, Thingiverse downloads, the 16 KB content sniff (Chromebook r193): all verified (archive). Nothing open.
6. Ad blocking (f138655, ec86442, 08bdf0b = `AdBlock.Client` in all app WebViews): verified; MakerWorld sign-in / downloads with
   it on, Bambu sign-in WebView, Orca Cloud login verified by the user 2026-10-14. **Untested:** plugin pages, Device page on
   the phone (needs a printer with a web UI; the phone only has the A1).
7. OpenSCAD: phone layout r166/r168, real .scad download r142/r143, painting through a mesh boolean r175: all verified (archive).
8. Models tab MakerWorld sign-in ticket flow: verified by the user 2026-10-14. Nothing open.
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
