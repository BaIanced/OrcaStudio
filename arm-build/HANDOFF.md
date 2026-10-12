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
**Test target: WSA while the user is away from home** (user, 2026-10-12 evening: phone off the network). r114 is
installed on WSA too. Back on the phone when the user says so / it shows in `adb devices`. Phone setup (wireless adb, root taps,
`phone-ui.py`, token file): archive "Phone test setup" and memory `test-on-phone`.

1. **Preset re-link (user OK'd 2026-10-12 late): done on WSA, still to do on the phone.** "Bambu Lab A1 0.4 nozzle
   -No cut No vibe" was detached (`machine/base/`, `"inherits": ""`), so only generic process/filaments were compatible.
   WSA: backup in `~\orca-android-tools\preset-backup-2026-10-12\machine`; `inherits` -> "Bambu Lab A1 0.4 nozzle",
   `.info` `base_id` = the sibling linked preset's (system A1 id), both files moved to `machine/`, `base/` removed
   (script: `cat >` over the old file keeps owner/SELinux, then `mv`). Verified WSA: listed, selectable, keeps Bambu
   PLA filaments, process "0.20mm Standard @BBL A1", G-code keys identical after app close. **Phone: same steps when
   it's back** (its own backup first). **Untested:** a Bambu/Orca cloud sync afterwards (cloud copy is still
   detached; same updated_time, so the pull shouldn't replace it); the Chromebook desktop still has it detached.
2. **User reports 2026-10-12** (commits after 5b7ee35, all in r114):
   - Match the installed nozzle (More, default on): `BambuReport.nozzleDiameter` -> `installedNozzles[model]`,
     `UiState.visiblePrinters` hides other nozzles, Prepare hint + "Use <preset>". **Untested:** the printer was
     offline (no report); newer-firmware `device.nozzle.info` path; stale status after switching printer models.
   - Use my filament presets (More, default on): AMS sync (`PresetBundle::sync_ams_list`) only picks base presets,
     so the user's saved filament presets were replaced on every sync. `PresetRef.base` from the engine,
     `AppSettings.myFilaments` (system -> user preset; set by picking / saving, cleared by picking the system one),
     applied after sync and for a new printer's default slot. **Untested** (needs the printer online and the
     preset re-link, else sync only finds generic filaments).
3. Merge: main = r112 (6f8560c, Android PR #6, 2026-10-12). Left on the branch: 46a694e (nozzle match) and
   121765c (my filaments), both untested; on top of them, verified: b7d6de2 (milestone 4, WSA r115) and the
   settings tools (WSA r117/r118); then 8334d43 + 80c8d0f (item 4, verified r120). Next merge
   once item 2's untested parts pass (or, if the user wants milestone 4 sooner, ask before splitting it off).
4. **Shape builder phase 2 gaps fixed + verified on WSA r120** (ungroup exact, rename no render, re-frame;
   archive "Shape builder phase 2 gaps"). **Next:** UI tests on WSA of align, mirror, dims list edit/remove,
   keyboard shortcuts; untested: no size/turn handles under a mirrored group. Editor draft holds test shapes
   (ids 2-4 + 7-9, dim `px`): clear it before UI tests.

Done 2026-10-12 (archive): merges to r112; AI tools milestones 1-4; settings tools; user reports (AMS sync
button, plate types); shape builder phase 2 gaps (r120).

## State
- Both repos work on branch `claude/handoff-continuation-rseql3` (the "test branch"). Autonomy
  (user, 2026-10-11): decide branch handling and next steps yourself. **Main merges / releases need
  the user.** Main = r112 (merged 2026-10-12, PR #6, on the user's `/next-merge`); user agreed to merge more
  often, at verified milestones: offer a merge PR when a batch is verified, merge only on their "merge".
- Installed on WSA: r120 (2026-10-12 evening); AI tools on. Plate 2 (temp) is empty. Shape-builder handles not tested: Y
  handle, Shift = 1° turn, handles on a group / nested child, touch (WSA has none).
- Draft of the open design: `files/openscad/draft.scad|json` (read with `adb exec-out "su -c 'cat ...'"`,
  handy to check builder edits without screenshots; the Code tab text isn't in the ui dump).
- WSA 1080p: the editor panel is short; collapse the preview ("Hide preview") to reach buttons
  below the Customizer notice.

## Modeling roadmap (user agreed 2026-10-11, in this order)
User goal: model **without writing code**; OpenSCAD code is only a backstop.
1. Shape builder: phases 1-2 done (r96-r104, gaps fixed r120; archive). Untested: align, mirror, dims list
   edit/remove, keyboard shortcuts, phone layout. Design data = CSG
   tree JSON in the object's `module` metadata (`ShapeDesign`, `scad/ShapeModel.kt`) -> OpenSCAD -> `ScadService`.
2. AI tool layer (MCP server in the app): milestones 1-4 done (archive).
3. Settings tools: done (archive). Printing from a tool would need the user's OK + on-screen confirm.

## Open items (details: grep the archive)
- Sketch editor: many controls untested (list in the archive, 2026-10-12 trim).
- User to retest: the 325 MB slice that crashed before the r59 OOM fix; pinch zoom on MakerWorld;
  whether a real keyboard's Ctrl+1 works (WSA drops synthetic Ctrl+1..9).
- Auto-save (r94): untested switching it off / changing the interval.
- Orca plugin runtime: kept as a general capability (no plugin in use). **FilamentHub is dropped
  for good; never suggest, test with, or mention it.** Not done: audit prompts, create_window,
  per-preset config overrides, printerAgent capability.
- 3D Filament Profiles (3dfilamentprofiles.com) is built in (Models tab site + "Log print"). Never
  press Subtract in tests.
- AMS mapping verified (user printed from A1). User's AMS lite: A1 yellow, A2 matte black, A3
  white, A4 PETG. **Any test print needs the user's OK.**
- Section view: travels/markers not clipped, picking ignores the cut.
- OpenSCAD untested: Save/Open .scad via picker, phone layout, opening .scad from a download/zip,
  painting through a mesh boolean.
- Models tab untested: MakerWorld sign-in ticket flow, Thingiverse downloads.
- REA MCP (github.com/morluto/rea), looked at 2026-10-12, not installed (needs the user's OK; changes MCP config):
  fits release APK / `liborca_jni.so` inspection and HAR traces of the MakerWorld / Thingiverse flows only.
- Wishlist later: filament colour mixing (upstream `FilamentMixer.cpp`). Not wanted: iOS port.
- Flatpak r9 MakerLab tab, weekly upstream bump, obn follow-ups: see the archive (2026-10-12 trim).

## Gotchas
- The app restores `files/session/session.3mf` on start and saves it in `onStop` (and by auto-save
  every 60 s when changed). `am force-stop` skips the onStop save. Closing the WSA window
  (`CloseMainWindow()` on the "OrcaStudio-Android" window) ran onStop on 2026-10-11/12.
- Test on a temp Plate 2 and delete it after; don't change the user's Plate 1. When deleting
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
- CI (`android-apk.yml`): Kotlin check, deps cache, then `liborca_jni.so` reused from cache when
  `android/core`, `android/obn`, `android/scripts`, the toolchain, src-orca and deps are unchanged
  (key `android-core-*`), else rebuilt with ccache (`android-ccache-*`); old caches pruned. Checks
  **19** `ObnNative` JNI exports (update when adding one). Release-signed since build 32.

## Environment and tools (Windows PC, local session)
- Working dir `C:\Users\Vince\OrcaProjectsGithub` with `OrcaStudio` (Flatpak; holds this file) and
  `OrcaStudio-Android` (`src-orca` submodule = OrcaSlicer). gh CLI logged in.
- WSA adb `127.0.0.1:58526` (root via `su -c '...'`, Android 13 / API 33; `run-as` fails, release build); an Android TV box is also attached, so always
  pass `-s`. WSA stops drawing the app when its window isn't in front (taps are lost, ui dump empty): focus it with
  the Alt + SetForegroundWindow trick from `wheel.ps1:17`.
- `~\orca-android-tools`: `install-build.ps1 -Run <id>` (WSA default), `ui.ps1 [-Shot png]`,
  `step.ps1`, `wheel.ps1` (real mouse wheel / drags), `drag.ps1`, `reinstall-with-data.ps1`.
- Logs: `adb shell setprop log.tag.OrcaInput DEBUG` (mouse events), `log.tag.OrcaWeb DEBUG` then
  restart = Models WebView debuggable: `adb forward tcp:9222 localabstract:webview_devtools_remote_<pid>`;
  helpers `cdp.mjs` / `cdplog.mjs` / `ua.mjs` in the session scratchpad (recreate if gone).
  A CDP UA override only lasts while that CDP connection is open.
- System file picker: close with `adb shell am force-stop com.android.documentsui`.
- WSA lost DNS once: `wsaclient /shutdown` and relaunch fixed it. adb `input` has no Shift/Alt state.
- The user's Chromebook (Crostini, aarch64) runs the Flatpak; A1 printer is cloud-bound
  (Developer Mode off); the app is signed in to their Bambu account with PEMs imported.

## Repos
| Repo | Notes |
|---|---|
| `BaIanced/OrcaStudio-Android` | cl1x/Orca-Android + signed Bambu printing via obn (static in `liborca_jni.so`, `android/obn`). main = PR #3 merge (pre-release `android-v0.1.2-r37`). Bot branch `upstream/orca-main` (never commit). Builds run on dispatch only (`gh workflow run android-apk.yml --ref <branch>`). |
| `BaIanced/OrcaStudio` | Flatpak fork; ours: `arm-build/`, `.github/workflows/arm-*.yml`. Latest release r9 (MakerLab tab). Details in the archive. |
| `ClusterM/open-bamboo-networking` | obn pinned v2.2.0 + local patches 0001 (cloud callbacks), 0002 (start_print try LAN first), 0003 (MQTT CA from `SSL_CERT_FILE`). |
