# Handoff: OrcaStudio-Android + OrcaStudio aarch64 Flatpak (state as of 2026-10-10 20:45 UTC)

Read this first. Address the user as Supreme Master. Older history (builds 14-50, past causes,
Flatpak details) is in `HANDOFF-ARCHIVE.md`. **Don't read the archive or `README.md` / `NOTES-*.md`
up front**; open them only when a question needs them (grep first).

## Now

Both repos work on branch `claude/handoff-continuation-rseql3` (the "test branch").
**Two streams (user, 2026-10-10):** implement on a feature branch while the test branch builds;
merge the feature branch into the test branch once both build clean and pass on WSA.

- Run 38072645925 (test branch, Orca Cloud sync merge + CI cache) green, ~20 min; not installed.
- **r59 = run 38074555972 (test branch) installed on WSA:** OOM fix (user crash: a big slice's 325 MB
  `extrusions.bin` was copied into a direct ByteBuffer twice, `Viewport.kt:161` and
  `PreviewPanel.kt:268`, over the 512 MB heap). Now `Buffers.kt` memory-maps, and `Preview.cpp`
  FloatWriter writes `.tmp` + rename like the scene/paint meshes. WSA: the user's plate (97 MB
  extrusions.bin) slices and previews, Java heap 5 MB. The 325 MB slice itself: user to retest.
- **Feature branch `claude/orca-plugins`: plugin runtime.** r62 = run 38082690102 installed on WSA (untested:
  first try crashed because R8 renamed the JNI listener methods, fixed with keep rules in r62; then WSA
  stopped creating the app window, `WsaClient /shutdown` hung; user asked to restart WSA).
  Embedded CPython 3.12.12 (Chaquopy build, `android/scripts/stage_python.py`) + upstream plugin
  host compiled unchanged (`android/core/plugins.cmake`); Android replacements in
  `android/core/plugin/` (PluginManager, PluginAuditManager = no sandbox hook yet, orca.host app/ui);
  `PluginConfig.cpp` extracted by `android/scripts/extract_plugin_config.py`. JNI
  `jni/OrcaPlugins.cpp` <-> `plugins/PluginNative.kt` / `Plugins.kt`; page UI `ui/settings/PluginPage.kt`.
  Test on WSA: More > Orca Cloud > Subscribed plugins > FilamentHub > Install (re-downloads, installs
  to `files/data/orca_plugins/_subscribed/<user>/<uuid>`), then the "FilamentHub" page button under
  the section; logcat tag OrcaPlugins + python log. Post-process step runs on save/share/send.
  Not done: plugin settings UI (getContext/saveConfig/onConfig, `resources/web/dialog`), audit
  prompts, create_window, picking `slicing_pipeline_plugin` in the process settings.
- **Local native build in WSL** (25 min cold, seconds incremental): `~/orca-android-tools/wsl/corebuild.sh`
  (`MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /mnt/c/Users/Vince/orca-android-tools/wsl/corebuild.sh`) syncs `android/` from the
  Windows checkout (`syncsrc.py`, CRLF->LF, only changed files) into `~/src/OrcaStudio-Android`
  (branch clone, src-orca pinned) and builds in `~/orca-build` (deps from the CI artifact of run
  38078498928, `deps_artifact=true` dispatch input; NDK r28c, cmake 3.31 + pkgconf + ccache in
  `~/.local/bin`; `~/build` is root-owned, don't use). `undef.sh` lists undefined symbols / NEEDED.
- CI: ccache never hit (fresh NDK mtime) -> `CCACHE_COMPILERCHECK=string:$NDK_VERSION`; caches are
  per branch (a feature branch's first build is cold); prune is per branch now.
- Verified on WSA 2026-10-10:
  - Orca Cloud sign-in (user: Google round trip works, 4 subscribed plugins listed, sign-in
    survives a restart; the account has no password, GitHub not tried).
  - Mouse back (adb `input mouse keyevent 4`): More -> Prepare; on Prepare it is eaten instead
    of backgrounding the app (user report: "acts like minimise"). Real mouse button (user).
  - MakerWorld: dark web pages, native links row, blank strip trimmed, Collections opens the
    user's collections.
- Built, not tested yet:
  - More > "Sync presets from Orca Cloud" (pull) and "Upload presets to Orca Cloud" (user).
  - Pinch zoom and Ctrl+wheel zoom in Models (user / wheel.ps1).
  - MakerWorld "Full site" chip; theme switch recreates the Models browser.
  - CI native-core cache + ccache: check the 2nd build after 38072645925 takes ~5-8 min.
- **Next: Orca plugins.** The user only uses the **4th subscribed plugin (Script + SlicingPipeline)**;
  the others (incl. "Orca Cloud dev") are not needed (user, 2026-10-10).
- Order (user): Orca Cloud login (done), preset sync (done, testing), Orca plugins (Script +
  SlicingPipeline first, then printerAgent, then pages). OpenSCAD skipped for now.

### Orca Cloud (Kotlin port of upstream `OrcaCloudServiceAgent.cpp`)
- `net/OrcaCloud.kt`, `net/OrcaCloudLoopback.kt`, `ui/settings/OrcaCloudSection.kt`.
- Sign-in page `https://cloud.orcaslicer.com/orcaslicer-login`, JS bridge registered as `wx`;
  `get_login_cmd` -> `window.postMessage(login_config)` (PKCE S256, loopback
  `http://localhost:41172..41174/callback`). Code exchange `POST auth.orcaslicer.com/auth/v1/token
  ?grant_type=pkce`. Refresh with 15 min skew; 400/401/403 signs out. Session: AES-GCM with an
  AndroidKeyStore key in `noBackupFilesDir/orca_cloud/session.sec` (**not in the backup yet**).
- API `https://api.orcaslicer.com`: plugins `GET /api/v1/plugins/subscriptions`; pull
  `GET /api/v1/sync/pull` (full, no cursor) -> engine `loadCloudPresets` (shared with the Bambu
  sync; cannot delete presets: `remove_users_preset` only touches presets whose user_id equals the
  engine's empty `preset_folder`).
- Upload (user approved 2026-10-10): engine `cloudUploads(userId)` (get_user_presets +
  get_differed_values_to_update) / `markUploaded` (set_sync_info_and_save); `POST /api/v1/sync/push`
  {id, name, content, original_updated_time}. New ids = UUIDv5(ns `f47ac10b-58cc-4372-a567-
  0e02b2c3d479`, "<user_id>/<name>"). 409 reported, never forced; 413 -> will_not_sync; deletes never
  uploaded; presets with another account's user_id (Bambu-synced) skipped.

### Models tab (`ui/models/ModelsScreen.kt`, `net/ModelDownloads.kt`)
- MakerWorld uses a desktop Chrome UA + `BBL-Slicer/v<ver> BBL-Language/en` ("slicer mode"):
  needed for "Open in Bambu Studio" (`bambustudio://open?file=` -> download -> import). In slicer
  mode MakerWorld renders no header; the app adds a links row (handle = `name` from
  `/api/v1/user-service/my/profile`, fetched by the page) and MW_TRIM_JS moves the fixed
  `.global_new` bar from top:60px to 0 (home only; model pages have no strip, don't overlay).
  "Full site" chip = no BBL suffix (header, sidebar, Collections; no slicer import).
- `?modelid=` changes load `<lang>/models/<id>`; downloads go to `cache/downloads`; names from
  page / header / URL, else sniffed (3MF/zip/STL/OBJ). All WebViews need MATCH_PARENT layout params
  (WRAP_CONTENT makes CSS 100vh = 0) and are made by `themedWebView` (app light/dark).
- Untested: MakerWorld sign-in ticket flow, Thingiverse downloads.

### FilamentHub (the user's plugin; read from the wheel, source stays out of repos)
- Installed on WSA via run 38076568561 (`claude/orca-plugins`, r60): `files/plugins/<id>/plugin.whl`,
  one 805 KB `filamenthub_plugin.py` (14k lines; line 545 is a 232 KB embedded React page). Pull
  binaries with `adb exec-out "su -c 'cat ...'"` (plain `adb shell` mangles them).
- **Stdlib only** (ssl, socket, ftplib, urllib, threading, zipfile, ...) + `orca`: fine on Android.
- Registers `FilamentHubPage` (orca.pages.PagesPluginCapabilityBase) when the host has Pages, else
  `FilamentHubCatalog` (Script: `orca.host.ui.create_window(html, ...)`), plus
  `FilamentHubSliceReporter` (SlicingPipelineCapabilityBase) when orca.slicing exists.
- Slice reporter acts **only at `Step.psGCodePostProcess`**: uses ctx.step, ctx.gcode_path (edits
  the exported G-code in place: identity comments), ctx.output_name, ctx.host,
  ctx.config_value("filament_settings_id") etc.; enabled per process preset via the
  `slicing_pipeline_plugin` option.
- Host surface: orca.base, @orca.plugin, orca.register_capability, orca.ExecutionResult.{success,
  skipped}, capability get_name/get_icon/has_config_ui/get_config_ui/get_default_config/on_load/
  on_unload/on_message/post_message/get_ui, orca.host.preset_bundle() (filaments/printers/prints:
  size(), preset(i).name/.file/.is_user(), current_process_preset().config_value()),
  orca.host.plugin.storage(), orca.host.app_language(), optional orca.host.reload_local_bundle
  (not upstream). JS side: injected `window.orca` bridge (postMessage/onMessage/getContext/
  saveConfig/onConfig) from `src-orca/src/slic3r/GUI/Widgets/WebHosting.cpp` ORCA_BRIDGE_JS.
- It writes imported filament presets to `{data_dir}/user/<folder>/_local/filamenthub/filament/*.json`
  (the app must then reload user presets) and opens OAuth in the real browser (`webbrowser`).
- Android plan: Pages capability -> a Kotlin WebView screen with the bridge JS; post-process step
  -> run on the G-code the app exports/sends; no wx needed.

### Orca plugins: research (2026-10-10)
- Upstream `src-orca/src/slic3r/plugin` (~14k lines): CPython 3.12 embedded via pybind11
  (`PythonInterpreter.cpp`); capability types PrinterConnection, Pages, Analysis, Importer,
  Exporter, Visualization, Script, SlicingPipeline. SlicingPipeline hooks libslic3r
  (`Print::set_slicing_pipeline_hook_fn`; the engine already has the seam). Host APIs in
  `plugin/host/*`: geometry, model, presets, slicing are GUI-free; ui / app / pages use wx. wx also
  in PluginManager, PluginConfig, PluginResolver, PluginAuditManager, PythonInterpreter.
- Plan: CPython for Android linked into the engine with the NDK + pybind11 (vendored in
  `src-orca/deps_src/pybind11`); Script + SlicingPipeline first. Plugins with native-code wheels
  can't run on Android (pure Python only); upstream installs PEP 723 deps with `uv` (none on Android).
- python.org ships Android tarballs only from **3.14** (latest 3.14.8; upstream bundles 3.12.13):
  `python-3.14.x-aarch64-linux-android.tar.gz` = `prefix/lib/libpython3.14.so` + stdlib (lib-dynload
  .so) + headers + a `testbed` app showing the embedding (stdlib in assets, extracted to files/,
  `PyConfig.home`; libpython*.so in jniLibs). 3.12 for Android only via Chaquopy builds.
- wx-free as-is: CloudPluginService, PluginFsUtils, PluginLoader, PluginHooks, PythonPluginBridge,
  host/{PluginHost,Geometry,Mesh,Model,Presets,Slicing}, pluginTypes/*. wx/GUI to replace in
  `android/core` (submodule stays unpatched): PluginManager (21 refs), PluginConfig (14),
  PluginResolver (9), PluginAuditManager (43, I18N), host/PluginHostUi (84), PluginHostApp (10),
  PluginPages (40), PythonInterpreter (1).

### Other open items
- Orca Cloud session not in the encrypted backup.
- WSA: 127.0.0.1 refused a shell connection to the loopback while ::1 worked (browser sign-in
  worked anyway).
- Flatpak r9 MakerLab tab: user hasn't reported (ticket sign-in, 3MF/STL round trip).
- Weekly upstream bump `upstream/orca-main`: merging into main is the user's call.
- Optional: obn patch 0001 upstream report (prepare it, give the user a link; needs OK); the cloud
  `POST /v1/user-service/my/task` 403 cause; obn deferred-teardown latch (`agent.cpp:117-129`
  vs `:330`).
- Wishlist later: filament colour mixing (upstream `FilamentMixer.cpp` exists; see archive).
  Not wanted: iOS port.

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
- WSA lost DNS once: `wsaclient /shutdown` and relaunch fixed it. WSA can't reach the printer on
  the LAN (bridged network); adb `input` has no Shift/Alt state.
- The user's Chromebook (Crostini, aarch64) runs the Flatpak; A1 printer is cloud-bound
  (Developer Mode off); the app is signed in to their Bambu account with PEMs imported.

## Repos
| Repo | Notes |
|---|---|
| `BaIanced/OrcaStudio-Android` | cl1x/Orca-Android + signed Bambu printing via obn (static in `liborca_jni.so`, `android/obn`). main = PR #3 merge (pre-release `android-v0.1.2-r37`). Bot branch `upstream/orca-main` (never commit). Builds run on dispatch only (`gh workflow run android-apk.yml --ref <branch>`). |
| `BaIanced/OrcaStudio` | Flatpak fork; ours: `arm-build/`, `.github/workflows/arm-*.yml`. Latest release r9 (MakerLab tab). Details in the archive. |
| `ClusterM/open-bamboo-networking` | obn pinned v2.2.0 + local patches 0001 (cloud callbacks), 0002 (start_print try LAN first), 0003 (MQTT CA from `SSL_CERT_FILE`). |
