# Handoff: OrcaStudio-Android + OrcaStudio aarch64 Flatpak (hot file, 2026-10-12)

Read this first. Don't use any title for the user ("Supreme Master" was a joke; never use it).
History, verified features, file maps and past causes live in `HANDOFF-ARCHIVE.md` (latest dump:
"Moved from HANDOFF.md on 2026-10-12"). **Don't read the archive, `README.md` or `NOTES-*.md` up
front**; grep them when a question needs them (e.g. `grep -n "AMS mapping" HANDOFF-ARCHIVE.md`).

## Rolling handoff rules (user, 2026-10-12)
- Keep this file **under ~12 KB**: only the next task, open/untested items, gotchas and the rules.
- When a task is verified, move its details (runs, files, causes) to the end of
  `HANDOFF-ARCHIVE.md` under a dated heading and leave at most a one-line summary here.
- **Never move pending, open or untested information out of this file** (user, 2026-10-12), even to
  meet the size target; only verified, finished work goes to the archive.
- **Merge cue** (user, 2026-10-12): like the /clear cue, tell the user when it's a good time to merge to
  main (a batch is verified), with what it contains and what's still unverified. Merge only on "merge"
  or `/next-merge` (= merge the verified, unmerged work, then carry on like /next; never untested commits).
  The cue is one line: "`/clear` then `/next`", or "`/clear` then `/next-merge`" when verified work awaits a merge.
- Update "Next task" before stopping any task. At each task boundary, **tell the user it is a good
  time to `/clear` then `/next`** (and why: task done + handoff updated). Don't suggest it mid-task.

## Next task
**Test devices (user, 2026-10-13):** **phone** = main (root); **Chromebook's Android (ARC)** = big-screen layout
checks (user wants the app there). Chromebook: `<chromebook-ip>:5555` (memory `test-on-phone`), Android 13, arm64,
1920x1080 (app area ~1813x948, shelf below), **no root**. Launch: `am start -n io.github.baianced.orcastudio_android/app.orcaandroid.ui.MainActivity`
(ARC draws only while unlocked: focus = MainActivity, not ARC's PlaceholderActivity). `ui.ps1 -Device <ip>:5555` works.
The system file picker is a ChromeOS dialog (adb can't drive it); open files with a VIEW intent on the MediaStore URI
(`content query --uri content://media/external/file --where "_display_name='x'"` -> `-d content://media/external/file/<id>
-t application/zip --grant-read-uri-permission`), which works without root.
Big-screen pass verified + merged (r140, PR #10). UI batch builds r144-r152 details: archive "UI batch builds r144-r152".
Verified: r148 filmstrip row (WSA), r149 Models infinite scroll (WSA; **untested on the phone**), phone pass r150 (portrait
tooltips / tool column / tabs / filmstrip / chips / fullscreen; landscape immersive), r151 number tabs + whole-row switches,
r152 rail 80 dp, **r153 rail skips the camera cutout (4dac2f4, verified by the user on the phone 2026-10-13)**.
Plate label default is off (`plateLabel = false`). Phone has plates 1-8 (user's), lab Tabs. The user drives sessions
from the phone: don't take the phone over without asking. WSA phone view (`phone-view.sh`) was back-burnered by the user.
Import/arrange fix eac2d13 **verified on WSA r154** (import onto a filled plate, Duplicate, Arrange; archive "Import/arrange
fix verified on WSA r154"). WSA session backup stays in `/data/local/tmp/session-backup.{3mf,json}` (restored).
**Next:** the rest of the batch list below (mostly phone checks: ask the user before taking the phone over). WSA r144/r146 checks passed (archive "UI batch WSA
checks"). fd71b33's keep_layout path verified WSA r154 (2026-10-13); a2d3148 (user 2026-10-13): lab sliders for text size,
interface size (root `LocalDensity` override in `AppScaffold`) and floating controls (overlay density, Prepare + Preview),
applied on release; wide settings panel edge drags to resize (`lab.panelWidth`, min 300 dp; let go < 200 dp = tuck; tap
toggles; keep this when removing the lab); tool column up/down arrows (`ScrollCue`, 28x18 dp, tap scrolls). User said some
text and the floating icons look huge.
Ghost on plate overlaps what is already there and is small at plate zoom: mention to the user. **Still untested:** everything on the phone (portrait,
tool column/fullscreen in portrait, landscape immersive), Chromebook, chips switcher, opacity slider, 20 plates,
tooltip look (vanished before the screenshot), default-plate-type pinning, native fixes. Lab now = filmstrip + label
+ ghost on WSA. Editor width resets after leaving Prepare (minor). **6e45548 verified WSA r158**: + pinned after the
plates (tabs + filmstrip); builder Customizer slider thumb, number and preview follow a slow drag (screencaps mid-drag
66 -> 48 -> 16; uiautomator can't dump during a drag, use `adb exec-out screencap` + crop).
Batch items:
- User couldn't pick between mockups (https://claude.ai/artifact/E3MtY8rQ1dMGHhibY2oNCX), so variants are switchable in
  **More > Layout lab (temporary)** (`core/LayoutLab.kt`, prefs `layout_lab`): plate switcher tabs (default) /
  filmstrip / chips, "Plate n of m" label, control opacity slider (`LocalOverlayAlpha`), portrait tool column (default
  on: undo/redo/view at its top), fullscreen in portrait, OpenSCAD view canvas (default) / ghost. Once the user picks,
  delete the losers and the lab. Wide panel tuck state is in the lab struct too (keep it when removing the lab).
- More order: Layout lab, Recent files (desktop rows, open), Calibration, Printers & presets (open), then collapsed AI
  tools, Orca Cloud, Backup, Appearance, Misc, About. Profile updates: auto check once a day (`lastProfileCheck`) ->
  `UpdatesChip` in the Prepare top bar (tap installs).
- "High Temp Plate" -> "Smooth PEI Plate" (`Translator.plate`, English only); picking a plate type makes it the default
  (`PresetController.rememberBedType`; other plates that followed the old default get it pinned).
- Tooltips (`Tip`, M3 TooltipBox: long press / hover) on tool + top-bar icons; auto-orient icon = arrow + tilted square;
  filaments collapsible (`CollapsibleTitle`); File button top right; landscape always immersive (`Immersive` in MainActivity).
- Double tap on an inactive plate (empty spot) focuses it (`PlateRenderer.plateAt`, `PlateListener.onPlateDoubleTap`).
- OpenSCAD: preview on the main canvas (shape designs always) or ghost (type 98 mesh, translucent pass) on the active
  plate's centre; editor resizable (`DragHandle`, portrait = split with the canvas above); slider drag = previews after
  40 ms with `$fn = 16` appended (draft, "Draft while dragging" chip), full render on release (`ScadController.endDrag`).
- Native: `add_plate` moves the object nearest to the new plate from outside every plate onto it (user's bug: 9-object
  import, floaters stayed beside the grid). **fd71b33** (in r153): add_plate skips that when a floater
  already lies in the new spot (**untested**); its `keep_layout` import part verified WSA r154 (archive "keep_layout import verified").
**Test on the phone first** (portrait + landscape), then Chromebook. Things to check: tooltips don't block taps; tool
column scrolls in portrait; filmstrip vs Slice button with many plates; 20 plates in tabs/filmstrip; slider follows the finger.
**Plate organisation (c315432 + 8d70911, r157): verified on WSA filmstrip** (archive "Plate organisation verified on WSA
r156/r157"). Undo of a group delete and tabs-layout group delete: verified WSA r158. **Untested:** phone/Chromebook.
**User picks 2026-10-13:** plate delete -> upstream (objects stay): **2db1d53, verified WSA r158** (`delete_plates` moves
a deleted plate's objects to free grid spots after the last plate, one per plate, skipping spots with floaters; no
confirm dialogs; delete plate 1 -> object floats off-grid, Objects (1); Add plate picked it up; group delete 1+2 + undo
restored it). **Untested:** a group delete where 2+ plates hold objects (separate spots). Minor: undo of a delete
makes plate 1 active (was 3). **b4a0789 (not built yet, untested):** tabs layout's "Delete n plates" sat over Undo
(below the row); now right of the stop button, vertically centred. Build it with the next batch.
Switcher (tabs/filmstrip/chips) and SCAD view (canvas/ghost): user **not decided yet**, keep the lab; ask again later.
Chips layout has no picking. User wants phone checks later (phone not on adb now; WSA meanwhile). Minor, seen on WSA:
the filmstrip's first plate is clipped a little at the left edge (pre-existing?).
**Next after the user's picks (G2b, user 2026-10-13):** plate number labels and per-plate icons drawn in the 3D view
around each plate (like Orca/Bambu: they turn with the camera), useful with many plates; then remove the lab.
**Older leftovers:** items 0 and 6 mostly need the user (sign-ins) or a web-UI printer.
**Phone:** serial = the `adb-...._adb-tls-connect._tcp` entry in `adb devices` (`adb disconnect` a stale `ip:port`).
Has r143. Setup: archive "Phone test setup", memory `test-on-phone`; `phone-ui.py` needs `PYTHONIOENCODING=utf-8`;
pull binaries with `adb exec-out "su -c '...'"`; Delete key = `su -c 'input keyevent 112'`. **Never
`cat missing > target`** (the redirect empties the target first). Don't drive WSA while the user uses the PC.
Test zip `scadzip-test.zip` stays in `/sdcard/Download` on phone + Chromebook.

0. Element blocker + ad-block menu (e4d75ab, a7e63d2): verified phone. **Untested:** mouse right-click (WSA), rules in
   other WebViews (Device page etc.); Orca Cloud login WebView (08bdf0b) needs a sign-out: leave to the user.
1. Preset re-link: verified. **Untested:** a Bambu/Orca cloud sync afterwards (cloud copy still detached; same
   updated_time, so the pull shouldn't replace it); the Chromebook desktop still has it detached.
2. Nozzle match: verified phone r114. **Untested:** newer-firmware `device.nozzle.info` path; stale status after
   switching printer models. Filament picks per AMS tray: verified phone r134. **Untested:** spool change -> printer's
   preset wins and the pick is dropped (only when the user swaps a spool); WSA. Phone plate: 1 slot "Bambu PLA Basic @BBL A1".
3. Merge: main = r143 (cc7abe4, PR #11 from `claude/merge-r143` at 4d55156, 2026-10-13, user's `/next-merge`). No merge offer pending.
   Unmerged, untested (all after 4d55156): f7f4d57 (UI batch), fd71b33 (plates; import part verified WSA r154, add_plate floater skip untested), 6e45548 (plate row, sliders; verified WSA r158), a2d3148 (sizes, panel drag), 6e645cb + 9f9978a (filmstrip row), 31f6b58 (chips, verified phone), 49e4cdf (tabs numbers + switch rows verified phone; cutout), 0afd458 (rail insets), 4dac2f4 (rail cutout, verified phone), eac2d13 (arrange fix, verified WSA r154), c315432 + 8d70911 (plate organisation, verified WSA r157), 2db1d53 (delete keeps objects, verified WSA r158), b4a0789 (tabs delete button, not built). 0d2bb7b (r149,
   infinite scroll) is verified on WSA but sits after the untested commits (cherry-pick it if merged early).
   Untested parts already in main stay listed in items 0, 2, 5, 6.
4. Shape builder by touch: verified phone r134. Raw multi-touch: `~/orca-android-tools/pinch.sh` / `drag1.sh`
   (push with `MSYS_NO_PATHCONV=1` and a `C:/` source path).
5. .scad zips + Thingiverse downloads: verified (WSA r126, phone r138/r142/r143, Chromebook r138; archive "Thingiverse
   downloads on the phone"). **Untested:** the 16 KB content sniff itself (r143 now gets the real name first).
6. Ad blocking (f138655, Models tab): verified WSA r127 + phone r134; Thingiverse download fix ec86442 verified phone
   r142 (archive "Thingiverse downloads on the phone"). 08bdf0b, all app WebViews use `AdBlock.Client`: verified WSA
   r128 (Device page, Models tab). **Untested:** MakerWorld sign-in / downloads with it on; Bambu sign-in WebView
   (needs Sign out + the user's password: leave to the user), Orca Cloud login, plugin pages, Device page on the phone
   (needs a printer with a web UI; the phone only has the A1).

## State
- Both repos work on branch `claude/handoff-continuation-rseql3` (the "test branch"). Autonomy
  (user, 2026-10-11): decide branch handling and next steps yourself. **Main merges / releases need
  the user.** Main = r143 (merged 2026-10-13, PR #11, on the user's `/next-merge`); user agreed to merge more
  often, at verified milestones: offer a merge PR when a batch is verified, merge only on their "merge".
- Installed on WSA: r158 (2026-10-13); AI tools on; auto-save 60 s. Session = the backup above (3 plates, plate 3 active). Shape-builder
  handles by touch untested (WSA has none). Real mouse drags (+Shift): `mdrag.ps1 x1 y1 x2 y2 [-Shift]`
  (Android coords = Windows pixels on WSA); the builder's shape list scrolls only with a real mouse wheel.
- Draft of the open design: `files/openscad/draft.scad|json` (read with `adb exec-out "su -c 'cat ...'"`,
  handy to check builder edits without screenshots; the Code tab text isn't in the ui dump).
- WSA 1080p: the editor panel is short; collapse the preview ("Hide preview") to reach buttons below the Customizer notice.

## Modeling roadmap (user agreed 2026-10-11, in this order)
User goal: model **without writing code**; OpenSCAD code is only a backstop.
1-3 done (archive): shape builder (untested: phone layout; data = CSG JSON in the object's `module` metadata,
`scad/ShapeModel.kt`), AI tool layer (MCP), settings tools (printing from a tool needs the user's OK + on-screen confirm).

## Open items (details: grep the archive)
- User to retest: the 325 MB slice that crashed before the r59 OOM fix; pinch zoom on MakerWorld;
  whether a real keyboard's Ctrl+1 works (WSA drops synthetic Ctrl+1..9).
- Orca plugin runtime: kept as a general capability (no plugin in use). **FilamentHub is dropped
  for good; never suggest, test with, or mention it.** Not done: audit prompts, create_window,
  per-preset config overrides, printerAgent capability.
- 3D Filament Profiles (3dfilamentprofiles.com) is built in (Models tab site + "Log print"). Never
  press Subtract in tests.
- AMS mapping verified (user printed from A1). User's AMS lite: A1 yellow, A2 matte black, A3
  white, A4 PETG. **Any test print needs the user's OK.**
- Section view: travels/markers not clipped, picking ignores the cut.
- OpenSCAD untested: phone layout, a real .scad download (Next task 5),
  painting through a mesh boolean.
- Models tab untested: MakerWorld sign-in ticket flow. (Thingiverse download verified r126.)
- REA MCP (github.com/morluto/rea), looked at 2026-10-12, not installed (needs the user's OK; changes MCP config):
  fits release APK / `liborca_jni.so` inspection and HAR traces of the MakerWorld / Thingiverse flows only.
- Wishlist later: filament colour mixing (upstream `FilamentMixer.cpp`). Not wanted: iOS port.
- Wishlist WebView element blocker + ad-block menu: built and verified (Next task 0).
- Flatpak r9 MakerLab tab, weekly upstream bump, obn follow-ups: see the archive (2026-10-12 trim).

## Gotchas
- The app restores `files/session/session.3mf` on start and saves it in `onStop` (and by auto-save
  every 60 s when changed). `am force-stop` skips the onStop save. Closing the WSA window
  (`CloseMainWindow()` on the "OrcaStudio-Android" window) ran onStop on 2026-10-11/12.
- Test on a temp Plate 2 and delete it after; don't change the user's Plate 1. Exception (user, 2026-10-12): the
  phone's Plate 1 objects and its shape-builder draft were only test objects, so they can be changed. When deleting
  objects by list position, verify the selection first.
- WSA stops drawing when its window isn't in front (taps lost, empty ui dump): focus it first
  (`wheel.ps1:17` trick / `tapf.sh`). WSA wedged (no window): stop WsaClient,
  `Start-Service WsaService`, `Start-Process wsa://<package>`. Lost DNS: `wsaclient /shutdown`.
- **MCP on WSA:** never `adb forward tcp:X tcp:Y` (WSA routes Android loopback to Windows; the
  forward loops and wedges adb: kill adb.exe). Use `adb forward tcp:8765 localabstract:orcastudio_mcp`.
  Token: `su -c 'cat .../shared_prefs/app_settings.xml'` into a variable, never print it. Run adb
  calls in PowerShell jobs with timeouts while testing sockets.
- **MCP on a real phone:** the `localabstract` forward works over wireless adb; the socket binds only after an
  app restart with AI tools on (archive "MCP on a real phone").
- WSA -> LAN printer: run `wsa-lan.ps1 <printer-ip>` after each WSA start. Safe print-dialog test:
  `iptables -I OUTPUT -d <ip> -p tcp --dport 990 -j REJECT` (root), Print, Cancel, `iptables -D ...`.
- Local native build in WSL: `MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /mnt/c/Users/Vince/orca-android-tools/wsl/corebuild.sh`
  (25 min cold, seconds incremental; details in the archive).


## Working rules (the user asked for these)

1. **Verify against source before recommending any change**; cite file:line.
2. Label anything untested as untested, inline.
3. Before any shell command the **user** must run, print a pre-flight block: 1. BLIND SPOTS,
   2. EXTRAPOLATED RISKS (2), 3. CAPABILITY VALIDATION (YES/NO). Direct verdicts, brief.
4. Keep check-ins cheap: one background `gh run watch`, not polling loops.
5. Approved: pushes and `android-apk.yml` dispatches on the work branches without asking. **Merging
   to main or publishing releases needs the user's go-ahead.**
6. **Never print, sign out or delete presets without asking.** Standing permission for an
   autonomous test-and-fix loop on WSA otherwise. Don't change the user's plate (their project is
   on it); close the app when done:
   `adb -s 127.0.0.1:58526 shell am force-stop io.github.baianced.orcastudio_android`.
7. **Secrets:** the user's `slicer_cert.pem` / `slicer_key.pem` / `slicer_crl.pem` never go in a
   repo or bundle; never explain how to obtain them. `obn.auth.json`, trace logs and session files
   contain tokens: ask only for filtered output.
8. **Both repos are public: no identifying details** (serials, IPs, e-mail, account / display names,
   MakerWorld handle, device models, tokens) in files, commits or PR text. Use placeholders. Run the
   privacy scan before every push (python is `python` on this PC):
   - Android: `python .claude/hooks/privacy_scan.py range "HEAD --not --remotes" . ':(exclude)src-orca'`
   - OrcaStudio: `python .claude/hooks/privacy_scan.py range "HEAD --not --remotes" arm-build '.github/workflows/arm-*' .claude`
9. Commit trailer: `Co-Authored-By` + `Claude-Session` lines as given in the session.

## Efficiency (user, 2026-10-10)
- Compile Kotlin locally before every push (12 s warm):
  `cd OrcaStudio-Android/android && JAVA_HOME="/c/Program Files/Java/jdk-22" ANDROID_HOME='C:\android_sdk' ./gradlew --console=plain -q :app:compileReleaseKotlin`
- Add `:app:mergeReleaseResources` to that check when strings change, and read the exit code (a
  grep on the output hid a resource failure once). Bash heredocs with python break in this tool:
  write the script with Write, then run it.
- Write code with Edit or python raw strings, never plain python heredocs (they ate backslashes 5x).
- Test with `ui.ps1` text dumps; screenshots only when the look matters. After launching the app,
  wait until `ui.ps1` lists the tabs before tapping (the first tap after start is often lost).
- Batch 2-4 changes per build; don't dispatch builds that will be superseded.
- CI (`android-apk.yml`, cache details in the archive): checks **19** `ObnNative` JNI exports (update
  when adding one). Release-signed since build 32.

## Environment and tools (Windows PC, local session)
- Working dir `C:\Users\Vince\OrcaProjectsGithub` with `OrcaStudio` (Flatpak; holds this file) and
  `OrcaStudio-Android` (`src-orca` submodule = OrcaSlicer). gh CLI logged in.
- WSA adb `127.0.0.1:58526` (root via `su -c '...'`, Android 13 / API 33; `run-as` fails, release build); an Android TV box is also attached, so always
  pass `-s`. WSA stops drawing the app when its window isn't in front (taps are lost, ui dump empty): focus it with
  the Alt + SetForegroundWindow trick from `wheel.ps1:17`.
- **Phone view on WSA: back-burnered** (user, 2026-10-13: "didn't look right on my end"; test phone layouts on the
  phone, WSA in its normal window as before). Kept for reference: `sh ~/orca-android-tools/phone-view.sh`
  (launches + `am task resize` to 412x720 dp portrait, sw412 "nrml port"); `... land` = 720x412. WSA display is
  1280x720 px at 160 dpi, so 720 dp is the max height (a real phone is ~900 dp). Task ID changes per launch (script finds it).
- `~\orca-android-tools`: `install-build.ps1 -Run <id>` (WSA default), `ui.ps1 [-Shot png]`,
  `step.ps1`, `wheel.ps1` (real mouse wheel / drags), `drag.ps1`, `reinstall-with-data.ps1`.
- Debug logs / Models WebView CDP: archive "Logs and CDP (moved 2026-10-12)".
- System file picker: plain `adb input tap` (focus.ps1 finds no app window while it is up), scroll with
  `input swipe`, avoid its Search (list broke); delete test files from `/sdcard/Download` after. Close with `adb shell am force-stop com.android.documentsui`. adb `input` has no
  Shift/Alt state: use `keys.ps1 -Keys <vk codes>` (real key presses; tap a row first for focus).
- The user's Chromebook (Crostini, aarch64) runs the Flatpak; A1 printer is cloud-bound
  (Developer Mode off); the app is signed in to their Bambu account with PEMs imported.

## Repos
| Repo | Notes |
|---|---|
| `BaIanced/OrcaStudio-Android` | cl1x/Orca-Android + signed Bambu printing via obn (static in `liborca_jni.so`, `android/obn`). main = r143 (PR #11). Bot branch `upstream/orca-main` (never commit). Builds run on dispatch only (`gh workflow run android-apk.yml --ref <branch>`). |
| `BaIanced/OrcaStudio` | Flatpak fork; ours: `arm-build/`, `.github/workflows/arm-*.yml`. Latest release r9 (MakerLab tab). Details in the archive. |
| `ClusterM/open-bamboo-networking` | obn pinned v2.2.0 + local patches 0001 (cloud callbacks), 0002 (start_print try LAN first), 0003 (MQTT CA from `SSL_CERT_FILE`). |
