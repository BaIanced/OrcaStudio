# Handoff: OrcaStudio aarch64 Flatpak + OrcaStudio-Android (state as of 2026-10-10 10:30 UTC)

Read this first, then `arm-build/README.md` and the `NOTES-*.md` files next to it. The user is
to be addressed as Supreme Master.

## Start here: open items, in order

**Two streams (user, 2026-10-10):** implement on a feature branch while the test branch builds;
merge the feature branch into the test branch once both build clean and pass on WSA.
- `claude/orca-cloud-login` was merged into `claude/handoff-continuation-rseql3` (`842977d`);
  run 38044939151 builds the merge (Models fixes + Orca Cloud). Next feature branch: start a new
  one from the test branch.
- **The user skipped OpenSCAD for now (2026-10-10).** Order: Orca Cloud login (done, needs the
  user's sign-in test), preset sync, then Orca plugins.
**Close the app when done** (`adb -s 127.0.0.1:58526 shell am force-stop io.github.baianced.orcastudio_android`):
the test scripts keep its window in front of the user's desktop. Python on this PC is `python`, not `python3`.

**WebView debugging (use it, it found every Models bug):** `adb shell setprop log.tag.OrcaWeb DEBUG`,
restart the app, then `adb forward tcp:9222 localabstract:webview_devtools_remote_$(adb shell pidof
io.github.baianced.orcastudio_android)`. Helpers (session scratchpad, recreate if gone): `cdp.mjs`
(node, Runtime.evaluate with awaitPromise) and `cdplog.mjs` (console, exceptions, failed requests,
`Page.frameRequestedNavigation` for custom-scheme links). Applies to the Models WebView only (the
switch is read when ModelBrowser creates it).

**Build 44-50 results (WSA, 2026-10-10):**
- Verified on 44: selection banner buttons stay put; VLH panel at the right edge above Slice; undo
  after starting a temperature tower ends the calibration and restores plate and project name;
  pickers list user presets first, vendor presets nested.
- Models fixes, all verified on 49/50 (run 38043169042 = r50):
  - MakerWorld got the phone site (Handy prompt) -> desktop Chrome UA + BBL-Slicer suffix.
  - Home cards only add `?modelid=` (a pop-up that never shows) -> `doUpdateVisitedHistory` loads
    `<lang>/models/<id>` like the desktop (`WebViewPanel::get_model_mall_detail_url`).
  - "Open in Bambu Studio" -> Import fires `bambustudio://open?file=<urlencoded url incl. %26name%3D>`
    (anchorClick). The download landed in cache/models and `importFile` copied it onto itself (0
    bytes). Downloads now go to cache/downloads; `importFile` skips a self-copy. Verified: a
    250x240 pegboard 3MF imported.
  - AndroidView's default WRAP_CONTENT made WebView lay out with height 0 (CSS `100vh` = 0):
    Printables' CookieYes dialog had max-height 0, so only its backdrop showed and blocked taps.
    All WebViews get MATCH_PARENT layout params.
  - Printables "Download" saved `x.bin` (WebView guesses from octet-stream) -> the first name with a
    model / zip extension, else sniffed from content. Verified: an STL imported.
  - File names keep non-Latin letters (`\p{L}`).
- Orca Cloud build (r46) on WSA: the sign-in page loads, the `wx` bridge handshake works (a fake
  loopback callback failed with "state mismatch", not "expired"), the loopback listens on
  127.0.0.1 and ::1:41172. **On WSA, 127.0.0.1 refuses connections from the shell; ::1 works**
  (untested whether the browser's localhost reaches it). The real sign-in needs the user.
- Tooling: the system file picker's Back goes up folders; close it with
  `adb shell am force-stop com.android.documentsui` (cancels, nothing saved). Kotlin string
  regexes need `\d` (written via python heredocs, `\d` lost one backslash twice: compile errors).

**Orca Cloud sign-in (branch `claude/orca-cloud-login`, `5cd80e6`):**
- Port of upstream `OrcaCloudServiceAgent` (src-orca `src/slic3r/Utils/OrcaCloudServiceAgent.cpp`)
  and `WebUserLoginDialog.cpp` / `HttpServer::auth_handle_request`, in Kotlin: `net/OrcaCloud.kt`,
  `net/OrcaCloudLoopback.kt`, `ui/settings/OrcaCloudSection.kt` (More > Orca Cloud).
- Page `https://cloud.orcaslicer.com/orcaslicer-login`: it detects the slicer by `window.wx` /
  `webkit.messageHandlers.wx` (checked in its JS bundle), so the bridge is registered as `wx`.
  `get_login_cmd` -> reply `window.postMessage(login_config)` (PKCE S256, state, redirect
  `http://localhost:<41172..41174>/callback`, apikey). E-mail sign-in: `user_login` with flat
  tokens. Google / GitHub: `thirdparty_login` opens the browser; GoTrue redirects to the loopback
  with `code` + `orca_state`; exchange `POST auth.orcaslicer.com/auth/v1/token?grant_type=pkce`
  `{auth_code, code_verifier}` with the `apikey` header.
- Refresh `grant_type=refresh_token`, 15 min skew; 400/401/403 signs out, other failures keep the
  session. Stored: refresh token + user, AES-GCM with an AndroidKeyStore key in
  `noBackupFilesDir/orca_cloud/session.sec` (not in the encrypted backup yet).
- API `https://api.orcaslicer.com` (upstream's default has no scheme; http 301s, https works).
  "Subscribed plugins" = `GET /api/v1/plugins/subscriptions` (Bearer + apikey).
- To test: e-mail sign-in, Google sign-in round trip (WSA may pause the app while the browser is
  in front), app restart keeps the sign-in, sign out, plugin list.
- Next: preset sync (`/api/v1/sync/pull|push`), then the plugin runtime (embedded Python).

0. **Handoff to the local session (2026-10-09, user's request: cloud usage).** The cloud session
   `session_01Dycp4Bu9GrptBgymXRxiss` has stopped. The user's local Windows session
   (`session_01Dyz5iJaQCQ1WuH3ktn4KU9`, "orcastudio-d5", gh logged in, root adb on WSA) is now the
   **only writer**: it commits/pushes `claude/handoff-continuation-rseql3` in both repos, dispatches
   `android-apk.yml` with `gh workflow run android-apk.yml --ref claude/handoff-continuation-rseql3 -R
   BaIanced/OrcaStudio-Android`, and keeps this file current. Run the privacy scan before every push
   (rule 7).
   - The user approved (2026-10-09) pushes and `android-apk.yml` dispatches on this branch without
     asking each time. A merge to main still needs their go-ahead.
   - **Builds 19-22 (local session, 2026-10-09):**
     - Build 18 verified on WSA: cloud MQTT connects (status and temperatures arrive), and cloud
       filament sync reads all 4 slots with the right colours.
     - `2fd9f15` (build 20, verified): Bambu spools fell back to Generic PLA because upstream
       re-keyed the Bambu bundle's `filament_id` (ec207e67a, e.g. `OFoiVqVM`), while printers still
       report `GFA00`. The sync translates a reported `GF..` id through `setting_id` (`GFSA00_04`).
       WSA now syncs Bambu PLA Basic / Matte / Matte / iSanMate PETG HF.
     - `b361bb6` (build 20, verified): the Filament brands filter lists `filament_vendor` brands,
       with search and show/hide all.
     - `913870c` (build 21): filament picker with user presets first, then collapsible
       brand > material sections.
     - `c9914d0` (build 22): dialog number fields commit while typing (a typed shape size was lost
       on Add); Slice on an empty plate shows a message.
     - The user gave standing permission for an autonomous test-and-fix loop over every button and
       setting on WSA. Never print, sign out or delete presets without asking.
     - **Build 25** (`55df52c`, verified on WSA):
       - Fixes: the tool column stays below the top bar; a stopped print shows "Stopped", not
         "Error"; More > Compare presets opens the picker; Choose printers opens on a vendor with
         chosen printers; About shows the CI build ("0.1.2-r25").
       - Device panel for Bambu: job, temperatures, AMS slots, messages.
       - Desktop mouse controls: right/middle-drag pans, right click opens a context menu.
       - Long press opens the same context menu: object actions on an object, add / import /
         arrange on the empty bed.
     - **Build 28** (`a00c119`, verified on WSA). Adds:
       - the preset editor's "Only changed" filter;
       - a Flushing volumes matrix dialog (the button used to silently recalculate the matrix);
       - the view follows a newly added plate;
       - X/Y/Z units in the row label;
       - **crash fix:** painting crashed with SIGBUS in glBufferData. `FloatData` memory-mapped
         `paint_mesh.bin`, which the engine rewrites on every stroke; files are now read, not
         mapped.
     - **Build 31** (`b9eb502`, verified on WSA):
       - mesh and paint files are written to .tmp and renamed (atomic);
       - Prepare shows the prime tower on plates that use more than one filament (type 99 box,
         clamped to the bed);
       - **fix:** reloading a project (the autosave) gave filament slots 2+ false overrides,
         because `diff_options` compared slot i with preset variant i (e.g.
         `filament_dev_ams_drying_ams_limitations`). It now uses the preset's first entry.
     - **Build 32** (`288f71a`, verified on WSA 2026-10-09): first release-signed build; installed
       with `reinstall-with-data.ps1` (data kept, cloud status works). Share G-code uses the Save
       name. Also verified: save G-code, save .gcode.3mf (md5 matches), lay on face, cut, check for
       profile updates. Cut drops colour paint, like desktop with `keep_painting` off (default).
     - **Build 33** (`94f14e1`, run 37952962925, verified on WSA): the .gcode.3mf's slice_info had
       empty prediction / weight / printer_model_id and no `<filament>` entries. slice() now keeps
       the stats per G-code; the export adds them, mapping filament ids to Bambu's via
       `resources/printers/bambu_filament_ids.json`. WSA export: prediction 6456, weight 18.19,
       `printer_model_id` N2S, filaments `GFA00` / `GFA01` with colours and use. New androidTest
       `f02b` (CI doesn't run androidTests).
       - Also verified on build 32/33: plate add / delete, Add > Text / SVG / Sample models
         (a non-SVG file gives "no closed shapes"), object settings editor + undo, pauses & colour
         changes dialog, temperature tower (G-code steps 230 to 190 °C, 50 layers each).
     - **Build 34** (`9664bab`, cancelled; included in 35): the 3D view drew every part orange;
       parts now take their filament's colour (volume extruder, else object, else 1), like the
       thumbnails (`filament_of` moved to Thumbnails.hpp; mesh type 100 + filament).
     - **Build 35** (`a8afcb7`, run 37960398849, verified on WSA): **multi-select**, asked for by the
       user ("five cubes, duplicate two at once").
       - Ctrl/Shift+click adds a copy. On touch, "Select multiple" (tool column, long-press menu,
         or long press on an Objects row) turns on select mode: taps add / remove, a banner shows
         the count, Select all (active plate) and Done.
       - With 2+ copies: Duplicate, Delete, drag and the filament picker (Objects tab card) act on
         all of them, each one undo step. Engine: `duplicate` takes `items` [[obj, inst]],
         `deleteItems`, `moveItems`, `setObjectSetting` with `objects`. androidTest `c05`.
       - The scene and paint meshes tag copies as obj * 4096 + instance (`INSTANCE_ID_STRIDE`,
         OrcaEngine.hpp / PlateRenderer.kt); the shader highlights up to 64 selected copies.
       - Verified: five cubes, select two, duplicate (both 2x), filament 2 on both, drag both,
         long-press menu shows only Duplicate / Delete, delete two copies, one undo restores them,
         Select all = 7. Filament colours verified (yellow cube).
     - **Build 36** (`caa4734`, run 37964003695, verified on WSA): select mode keeps Objects rows
       compact (the first pick expanded its details and moved the rows under the next tap); very
       dark filaments get a minimum shade (black was a flat silhouette).
     - Fixed in build 43: the selection banner's buttons moved when its text changed length.
     - **Merged to main (2026-10-09, user's go-ahead):** PR #3 (builds 15-36); main build
       38003237247 published pre-release `android-v0.1.2-r37`.
     - **Builds 37-39: desktop mouse / keyboard controls** (user's request: "mimic Bambu Studio /
       Orca desktop", defaults from `src-orca/src/slic3r/GUI/Shortcuts.cpp`).
       - Mouse: Shift+drag rectangle select (adds), Alt+drag removes, Alt+click selects a part,
         Ctrl+wheel brush size while painting. Zoom stays centred (desktop `zoom_to_mouse` = false).
       - Ctrl keys, only while the 3D view has focus (it takes focus on touch): A / Shift+A select
         all (plate / all plates), C / V copy-paste (paste = duplicate), K clone, D delete all,
         0-7 camera views (iso, top, bottom, front, rear, left, right, plate). Ctrl+Z/Y/R/N global.
       - Single keys: Tab Prepare/Preview, I/O zoom, A / Shift+A arrange all / plate, Q orient,
         F lay on face, C cut, L/P/H/N paint, U measure, arrows 10 mm (Shift 1 mm), PgUp/PgDn
         rotate 45 deg, +/- copies, 1-9 filament; Preview: arrows layer / moves, Home/End.
       - Behaviour changed to match the desktop: Ctrl+A was arrange, Ctrl+D duplicate, Ctrl+1-3
         the tabs, O orient.
       - Build 37 failed to compile (`newProject` joined `deleteAll`); 38 fixed it. On 38, Ctrl
         shortcuts verified on WSA (Ctrl+3 front, Ctrl+A, Ctrl+K, Ctrl+C/V, Ctrl+D + Ctrl+Z), but
         arrows / Tab went to Compose's focus navigation (scrolled the side panel). Build 39
         (run 38005883012, verified on WSA): PlateView forwards its keys to the handler first. Arrows (10 mm), PgUp (45 deg), 2 (filament), Tab, Preview Down arrow all work; four Ctrl+Z restore.
       - Not testable over adb: Shift/Alt mouse drags (adb input has no modifier state).
     - **Build 40 (user report 2026-10-09):**
       - Mouse wheel orbited instead of zooming on WSA. Cause: WSA turns the mouse into emulated
         touches (wheel = swipe, Shift = horizontal) unless the app declares
         `android.hardware.type.pc` (Amazon WSA compatibility guide). Manifest now declares it, so the
         existing wheel zoom / middle-drag pan / right-click code gets real mouse events. Reproduce
         with a real Windows wheel event: `orca-android-tools/wheel.ps1` (-Notches, -Middle -DragX) (SetForegroundWindow needs the Alt
         key trick); adb `input` cannot.
       - A user printer preset (inherits "Bambu Lab A1 0.4 nozzle") lost the connection, the loaded
         filaments and the sync button: they were keyed by preset name. Now kept under the base
         system preset (`AppSettings.setPrinterBase`, engine printer list has `base` and the
         resolved vendor).
       - Settings showed per-variant vectors raw ("190,190,190,190,190"): equal entries are now
         shown / edited as one value. Not reproduced with the A1 presets on WSA (all single values);
         H2D-style user presets have 2-7 entries.
       - Bambu mode: for a Bambu printer the editor hides the desktop's non-BBL options plus
         Klipper / Marlin / pellet / toolchanger / print-host options (`option_states`); the
         connection dialog offers only the Bambu types.
       - Encrypted backup (More > Backup): settings, connections, user presets, obn credentials
         (login, slicer cert / key, printer certs); PBKDF2-SHA256 310k + AES-256-GCM, passphrase
         min 8. Restore reinstalls the printers' vendors and restarts the app.
     - **Build 40 verified on WSA (run 38017581298, APK r41, 2026-10-10):** the wheel zooms (no
       orbit), left drag orbits, a right click opens the context menu. Right / middle **drag** did
       nothing: the logcat shows `InputDispatcher: Asynchronous input event injection failed` twice
       per drag, so WSA's events for a held right / middle button don't arrive as touch moves.
       - **Build 41** (`2bb7e71`, run 38034948519, verified on WSA): the `OrcaInput` log confirmed
         WSA sends ACTION_DOWN + BUTTON_PRESS, then `ACTION_HOVER_MOVE buttons=4` (2 = right) for
         the drag. PlateView now pans on those hover moves; middle and right drag pan, a right drag
         opens no menu. Mouse event log: `adb shell setprop log.tag.OrcaInput DEBUG`.
     - **Build 43** (`13b183d`) failed to compile (ModelsScreen: `vm.toast` missing, progress setter);
       **build 44** (`264cc54`, run 38037031544) fixes it and is what to install. Contents, all untested:
       - fixes: the selection banner fills the width (buttons stay put); Undo back before a
         calibration started ends the calibration and restores the project name (engine
         `m_calib_undo_depth`, scene `calibration_active`); on wide layouts the VLH panel sits at
         the right edge above Slice.
       - preset pickers (user's request): user presets first in one open group, then one
         collapsed "Vendor presets" group (vendor; filaments brand > material). `PickerDialog`
         nests to any depth (`PickerItem.detail`), `presetItems()` in PreparePanel.kt.
       - **Models tab** (wishlist item 1): `ui/models/ModelsScreen.kt` (`ModelBrowser`, kept by
         AppScaffold across tab switches) + `net/ModelDownloads.kt`. MakerWorld loads through
         `makerworld.com/api/sign-in/ticket?to=...&ticket=` with obn `request_bind_ticket`
         (`abi_bind.cpp:110`, new JNI `ObnNative.webTicket`, **19 exports**). Handles
         `bambustudio://open?file=<url>&name=` links (Downloader.cpp / `import_model_id`),
         `makerworld_model_open`, MakerLab base64 messages, plain downloads and zips (Printables,
         Thingiverse chips). Files go through `FileController.openDownloaded` -> `openModels`
         (project 3MF on an empty plate opens as project, else adds the geometry).
       - To test: MakerWorld signed in, "Open in Bambu Studio" on a model, a Printables download,
         Back button in the page, tab switch keeps the page.
       - Test helper: `orca-android-tools/drag.ps1 -Middle -Down <flag> -Up <flag> -DragX 150`
         (`wheel.ps1` with selectable mouse_event flags: 2/4 left, 8/16 right, 0x20/0x40 middle).
     - **Wishlist (user, 2026-10-09; not started):**
       - Model sites in their own tab, "the more the merrier", MakerWorld as the proof of concept
         (then Printables, Thingiverse, ...): browse in-app, download straight into the plate.
       - Parametric 3D modelling inside the app: embed OpenSCAD (user's idea). Options: native
         headless build for arm64 (GPLv2+, deps mostly in Orca's: CGAL, GMP/MPFR, Boost, Eigen,
         maybe Manifold; adds a parser plus FreeType/HarfBuzz for text()) giving meshes straight
         into the plate; or openscad-wasm in a hidden WebView as a quick PoC. UI idea: code editor
         plus Customizer comments shown as sliders, .scad open / share intent, later MakerWorld
         parametric models (MakerWorld's Parametric Model Maker is OpenSCAD-based).
       - Orca Cloud login: upstream `OrcaCloudServiceAgent` (default `ORCA_CLOUD_PROVIDER` in
         GUI_App) for preset sync and the plugin store.
       - Orca plugins: upstream `src/slic3r/plugin/` = embedded Python (pybind11) with host bindings
         (model, mesh, presets, slicing, UI); types pages / printerAgent / script / slicingPipeline;
         `CloudPluginService` subscribes / downloads through the Orca Cloud account. Android: embed
         CPython (official Android support since 3.13) or Chaquopy; the UI / pages bindings are wx
         and need Compose counterparts. Order: cloud login, then script + slicingPipeline plugins,
         then printerAgent, then pages.
       - Not wanted: an iOS port (user, 2026-10-09: "I'll never want to do ios port").
     - **Wishlist (later, user: "can wait"): filament colour mixing.** Investigated: upstream OrcaSlicer in
       `src-orca` already has mixed filaments (`FilamentMixer.cpp`, `filament_is_mixed`,
       `filament_mixed_components` / `_sublayer_ratios` / `_gradient*`, process
       `enable_mixed_color_sublayer`, `ToolOrdering::resolve_mixed_filaments`). A mixed slot is a
       virtual filament (preset copied from component 1, blended colour) resolved per layer or
       sub-layer into its physical components. Android needs: an add/edit dialog, mixed rows in the
       filament list, the per-slot keys in `selection_config` (size the vectors to the slot count
       first), project save/load, and leaving virtual slots out of AMS mapping. Caveat for the A1:
       at least one filament swap per layer that uses a mixed slot.
     - Test loop findings: variable layer height and flow-rate calibration (9 tiles with per-object
       settings) work; the VLH panel covered the selected object on wide layouts (moved in build 43). WSA lost
       DNS once (cloud showed obn -2 / "Lookup error"); `wsaclient /shutdown` + relaunch fixed it.
     - **Fixed in build 43 (untested):** after a calibration, Undo back to the old plate keeps the calibration's
       project name ("Temperature tower") for Save / export names. The desktop has no undo across
       a calibration start (it makes a new project).
     - **Tooling:** `install-build.ps1` now defaults `-Device` to WSA (with the Shield attached,
       a bare `adb install` failed). Don't use `step.ps1` while a system file picker is open: its
       relaunch closes the picker; tap with `adb shell input tap` instead.
     - **Verified working:** measure, object settings and info dialogs, variable layer height,
       seam / colour painting, two-colour slicing with prime tower, share G-code.
     - **Left to test:** lay on face, save G-code / .gcode.3mf, Send (uploads to the printer),
       cloud print (needs the user at the printer).
     - Not a bug: a new modifier sits inside the opaque object, so it is not visible.
     - **Still to test:** text / SVG / samples dialogs, paint, cut, measure, plate add / delete,
       flushing volumes, prime tower position, the object settings editor, share / save G-code.
     - **WSA caveat:** WSA stops drawing the app while its window is not in the foreground. Bring it
       forward with `wsaclient /launch wsa://io.github.baianced.orcastudio_android` before each
       step, and use taps, not key events (a key event without focus gives an ANR kill).
   - **Build 18** ([run 37904663855](https://github.com/BaIanced/OrcaStudio-Android/actions/runs/37904663855),
     commit `3676dad`, dispatched by the local session) adds obn patch 0003: MQTT TLS without a CA
     file reads `SSL_CERT_FILE` first.
     - Build 17 on WSA: the cloud switch saved `block_cloud = 0`. LAN failed as expected, then
       `connect_server -> 0`, but the cloud MQTT never connected: `cloud mqtt disconnect rc=14`.
     - Cause: outside Windows, obn v2.2.0 gives the cloud broker no CA file and only probes Linux
       trust paths (`mqtt_client.cpp`), none of which exist on Android.
     - The app already exports Android's CA store to `cacert.pem` and sets `SSL_CERT_FILE`
       (`ObnCredentials.prepareTls`).
     - Test plan below is unchanged; run it on build 18.
     - The 4 slots per the user: Bambu PLA Matte Bone White, iSanMate PETG HF Black, Bambu PLA
       Sunflower Yellow, Bambu PLA Matte Black. The earlier "2 wrong colours" report was a
       misread, so just compare the sync against this list.
     - Printer for a test print: 0.4 hardened steel nozzle, SuperTack plate.
   - **Build 17** (commit `7383c7c`, green; WSA result above) adds:
     - **Opt-in Bambu cloud** (2 switches in the connection dialog of the signed type, stored in
       `obn.conf`):
       - `block_cloud = 0`: ObnHost falls back to obn's cloud MQTT when the LAN fails
         (`cloudConnect` JNI), and commands go through obn's `send_message`.
       - `cloud_print = try_lan_first`: obn `start_print` (patch 0002) prints over the LAN when it
         can, else through Bambu's cloud. That path previously returned 403 for this account.
       - JNI exports are now 18.
     - The settings editor shows single string-list values without quotes.
   - **Test on WSA:**
     - turn the cloud switch on, then Test ("connected through the Bambu cloud");
     - status, Sync filaments (check the 2 wrong colours);
     - optionally a cloud print;
     - the editor's Vendor value has no quotes.
   - **Next after that:** mouse support and the plate context menu (task #5 in the cloud session);
     the permanent signing-key secrets.
0. **Run 16 verified on WSA by the local session (2026-10-09):**
   - The filament picker crash is fixed (groups render, picking a synced preset works).
   - "Sync presets from Bambu account" loads 199 presets without a crash.
   - The settings editor opens.
   - Still open:
     - **Display bug:** the editor shows string options serialized, e.g. Vendor `"Bambu Lab"`
       with quotes, Default color `""`. `preset_values` returns `opt_serialize`.
       Pre-existing, not yet fixed.
     - **LAN filament sync fails on WSA:** `rc=14 No route to host`. WSA's bridged network can't
       reach the printer while the Windows host can, so this is not app code.
     - The wrong-colour check waits for cloud AMS sync or a device on the LAN.
     - **CI debug signing key differs between builds:** `INSTALL_FAILED_UPDATE_INCOMPATIBLE`
       on WSA. The fix is the 4 `ANDROID_KEY*` repo secrets, queued after the primary goal.
   - The local session is now `session_01Dyz5iJaQCQ1WuH3ktn4KU9` ("orcastudio-d5", after a
     restart). It has `~\orca-android-tools\install-build.ps1 -Run <id>` and root on WSA; send it
     run ids to test.
0. **Android test build run 16** ([run](https://github.com/BaIanced/OrcaStudio-Android/actions/runs/37871184670),
   commit `93b468a`) is **green** (2026-10-09 02:08Z). Run 15 results from the local session's
   device test:
   - Cloud preset sync no longer crashes.
   - Tapping a filament slot crashed with `Key "g:Bambulab" was already used`: PickerDialog emitted
     one header per run of a group, and synced user presets interleave with system ones. Fixed in
     `93b468a` (one header per group, de-duplicated keys). Re-test pending.
   - "Sync filaments from printer" needs LAN. The user wants cloud AMS sync instead (task below).
     The 2 wrong slot colours are still unchecked.
   - **Cloud AMS sync plan (waiting for the user's go-ahead):**
     - obn blocks cloud MQTT while `block_cloud = 1` (`abi_cloud.cpp:18`, `:66`; `send_message`
       fallback in `agent.cpp`).
     - An opt-in setting would write `block_cloud = 0`. obn re-reads `obn.conf` when
       `set_config_dir` is called again (`agent.cpp:1826-1842`, documented as idempotent).
     - Then `connect_server` + `add_subscribe([serial])`, a pushall through
       `bambu_network_send_message`, and the cloud reports go into `BambuReport`.
     - Printing stays LAN (`cloud_print = lan_only`).
0. **Android test build run 15** ([run](https://github.com/BaIanced/OrcaStudio-Android/actions/runs/37753117522),
   commit `7b7ceed`) is **green** (2026-10-08 09:22Z). User report on run 14 (2026-10-08): app
   installs, sign-in and PEM import work, filament sync works, but:
   - 2 synced slots show the wrong colour (details not reported yet);
   - tapping a filament slot afterwards (to change it or open its settings) closes the app with
     no message;
   - "Sync presets from Bambu account" closes the app the same way.
   The cause is **not determined**. Run 15:
   - adds `CrashReport.kt` (the report is shown with a Copy button on the next start);
   - restores the bundle state that `sync_ams_list` / `load_user_presets` change;
   - makes filament sync wait for a fresh AMS report.
   **Coordination:** the user's local Windows session (Remote Control,
   `session_01K9rgDzNwS1Ys37uHwxSUAE`, since 2026-10-09 `session_01Dyz5iJaQCQ1WuH3ktn4KU9`) does device debugging with adb and does not push. This
   cloud session is the only one that commits, dispatches CI and edits this file.
   Queued next: mouse support (left/right/middle-pan/back) and a plate context menu on right-click /
   long-press (e.g. add shape), modelled on OrcaSlicer desktop.
1. **Android test build run 14** ([run](https://github.com/BaIanced/OrcaStudio-Android/actions/runs/37577813513),
   commit `1139297` on Android branch `claude/handoff-continuation-rseql3`, which was restarted from
   `main` after PR #2 merged) is **green** (finished 06:11Z, so it compiles; APK artifact expires
   2026-10-14). The user asked for three features, all **untested on a device**:
   - **Printer messages with prompt buttons.**
     - `net/BambuReport.kt` parses `print_error` and `hms` from reports.
     - `net/HmsCatalog.kt` loads the texts and buttons per model like the desktop's HMSQuery
       (`e.bambulab.com/query.php` and `/hms/GetActionImage.php`, cached for a week). The
       session proxy blocks that host, so the response format was taken from the bundled files
       that HMSQuery saves unchanged.
     - The Device tab shows a message line and a prompt with the desktop's buttons
       (`DeviceErrorDialog::on_button_click` commands, checked identical at OrcaSlicer `f8dd560`).
     - The print notification shows the text and posts a separate notification for a new prompt.
     - Commands now wait 5 s for the printer's reply and surface `"result": "fail"`.
   - **Filament sync**: "Sync filaments from printer" under the filament slots. It feeds AMS /
     AMS lite / external-spool trays to `PresetBundle::sync_ams_list` (direct sync) via the new
     engine call `syncFilaments` (`core/jni/OrcaProject.cpp`).
   - **Cloud preset sync**: More > "Sync presets from Bambu account".
     - The new JNI `ObnNative.cloudPresets` runs obn's `get_setting_list` + `get_user_presets`.
     - Then `loadCloudPresets` runs `load_user_presets` + `save_user_presets`. App-only presets
       have no `setting_id`, so the sync never removes them.
     - The workflow's JNI export count is now 16.
   - Also: `ObnHost` instances share obn's single LAN session (reference counted), so the device
     tab's polls no longer drop the print notification's session.
   - The user's prompt that motivated this: `07FF-8007` "Please observe the nozzle ..." (A1, start
     of print). Handy offers "Filament Extruded, Continue" / "Not Extruded Yet, Retry"
     (`ams_control` `done` / `resume`). The earlier in-app cancel during that prompt did nothing
     visible. Why was **not** determined (no reply checking at the time).
2. Done 2026-10-07:
   - Run 12 printed on the device.
   - PR #2 merged (`8871376`), and the merge's run 13 published pre-release
     [android-v0.1.2-r13](https://github.com/BaIanced/OrcaStudio-Android/releases/tag/android-v0.1.2-r13).
   - Cause of the run 11 Print failure, verified against obn v2.2.0:
     - obn's default `mqtt_keep_connection = 1` (`config.hpp:62`) defers the disconnect.
     - The deferred teardown (`agent.cpp:117-129`) keeps the `app_cert_install_sent_` latch,
       and a clean disconnect reports `ConnectStatusOk` (`lan_session.cpp:130-133`).
     - So `install_device_cert` returned early (`agent.cpp:2062-2066`).
     - Fixed with `mqtt_keep_connection = 0`.
   - A possible upstream obn report: the deferred path should erase the latch like
     `disconnect_printer` does (`agent.cpp:330`).
   - Ask before merging the work branch to `main` again: that publishes a release.
3. **Not yet reported by the user:** whether the MakerLab tab works in Flatpak release
   **r9** (`arm64-v02.08.01.55-p6-obn-v2.2.0-r9`, published 2026-10-06 19:33Z). Untested
   areas:
   - ticket sign-in;
   - the 3MF/STL round trip;
   - whether MakerWorld shows its "open in slicer" actions.
4. Weekly upstream tracking (Android):
   - The first run built `upstream/orca-main` = main + OrcaSlicer `78f74a6` (2026-10-06).
     [Run 37549726219](https://github.com/BaIanced/OrcaStudio-Android/actions/runs/37549726219)
     is **green**.
   - The bump flagged `src/slic3r/GUI/Tab.cpp` for review. **Reviewed 2026-10-07: no impact.**
     In `f8dd5605..78f74a62` (40 commits), only `2d90345d` touches it, changing one wiki anchor
     (2nd argument of `append_single_option_line("infill_complete_top", ...)`). The extractor's
     `OPTION_RE` (`android/scripts/extract_settings_layout.py:27`) reads only the option key.
     None of the other port-dependent files in `android/UPSTREAM.md` step 2 changed in that range.
   - Merging it into main is the user's call.
5. Older optional items:
   - Find the real cloud 403 cause (see the Flatpak section).
   - Report obn patch 0001 upstream. The user doesn't want to learn PR mechanics, so prepare it
     and give them a link. Needs their OK.
   - Confirm the old `LD_LIBRARY_PATH` flatpak override was reset.

## Working rules (the user asked for these)

1. **Verify against source before recommending any change.** Read the obn / OrcaSlicer code
   path that decides the outcome and cite file:line. Earlier sessions went wrong when they
   skipped this:
   - `try_lan_first` was suggested without checking `start_print`.
   - "Sign out and back in" was suggested, but logout keeps the cloud MQTT session.
   - frames were counted at `debug` level, which never logs them.
2. Label anything untested as untested, inline.
3. **The user's output rules:**
   - Before any shell command the user must run, print a pre-flight block: 1. BLIND SPOTS,
     2. EXTRAPOLATED RISKS (2), 3. CAPABILITY VALIDATION (YES/NO).
   - Show calculations.
   - Give a direct verdict, brief, with nothing left out.
   - Web references as inline hyperlinks.
4. Keep check-ins cheap: single scheduled checks, not live monitors.
   - Builds run on GitHub. They're free for these public repos, ARM included: 0 billable ms.
5. Don't merge to main or publish releases without the user's go-ahead.
6. **Secrets:**
   - The user's `slicer_cert.pem` / `slicer_key.pem` / `slicer_crl.pem` must never go in a repo
     or bundle. Never explain how to obtain them.
   - `obn.auth.json` and trace logs contain tokens. Ask only for filtered output, e.g.
     `grep -o 'mqtt msg topic=[^ ]* bytes=[0-9]*'`.
7. **Both repos are public. Never put identifying details in them**: not in files, commit
   messages, PR text or GitHub comments. That covers printer serials, IP addresses, the user's
   e-mail address, account or display names, device models and tokens. Use placeholders such as
   `<serial>` and `<printer-ip>`.
   - The topic in the `grep` above contains the serial: ask the user to replace it with
     `<serial>` before pasting.
   - `.claude/hooks/privacy_scan.py` (in both repos) blocks this when the session runs inside
     the repo (Claude Code hook), and the `privacy scan` workflow checks every push.
   - In a multi-repo session started from the parent directory, the hook does **not** load. Run
     it yourself before every push:
     `python3 .claude/hooks/privacy_scan.py range "HEAD --not --remotes" <pathspecs>`
     (pathspecs: OrcaStudio `arm-build '.github/workflows/arm-*' .claude`; Android
     `. ':(exclude)src-orca'`).

## Repos

| Repo | Purpose |
|---|---|
| `BaIanced/OrcaStudio` | Public fork of jarczakpawel/OrcaStudio. Everything we own is in `arm-build/` and `.github/workflows/arm-*.yml`. `main` = `c3304375` (PR #1 merged: MakerLab patch + `publish` switch). Work branch `claude/handoff-continuation-rseql3`. |
| `BaIanced/OrcaStudio-Android` | cl1x/Orca-Android history plus signed Bambu printing via obn. `src-orca` submodule = OrcaSlicer. `main` = `8871376` (PR #2 merge; latest release `android-v0.1.2-r13`). Work branch `claude/handoff-continuation-rseql3` = main + `1139297` (printer messages, filament sync, cloud preset sync; **unmerged**). Bot branch `upstream/orca-main` (never commit to it). |
| `ClusterM/open-bamboo-networking` (obn) | Network plugin, pinned **v2.2.0** (`5e6a359c71a0c07476f5d372bf7ad0f2b43efe94`), with local patches. Read its source with WebFetch on `raw.githubusercontent.com/ClusterM/open-bamboo-networking/v2.2.0/src/<file>`. Main files: `agent.cpp`, `lan_session.cpp`, `lan_tls.cpp`, `abi_*.cpp`, `config.cpp`; `include/obn/config.hpp` has the defaults. |

In a new cloud session, add the Android repo with `add_repo` (BaIanced/OrcaStudio-Android) and
clone it next to OrcaStudio. A shallow single-branch clone needs a fetch refspec plus
`git push -u` before the stop hook stops complaining about "no remote branch".

## Flatpak (BaIanced/OrcaStudio)

- **`arm-flatpak.yml`** builds on `ubuntu-24.04-arm`:
  - Deps are cached under a `make-manifest.py --print-deps-key` key.
  - Then the app plus obn, the bundle, a smoke check (`ldd` in the sandbox), and a release
    `arm64-<os_tag>-obn-<obn_tag>-r<N>`.
  - Input `publish` (default true) gates the release job. Use `publish=false` for test builds.
  - Times: deps ≈ 26 min, app ≈ 41 min cold, ~5 min warm.
- **`arm-upstream-watch.yml`** runs daily: it bumps `arm-build/versions.json` on new upstream
  tags and calls the build.
- **`make-manifest.py` transformations:**
  - a) FFmpeg prefetch
  - b) obn module
  - c) launcher
  - d) BUILD_INFO
  - e) orca_deps as a reproducible tar
  - f) `shared/` added to the app module
  - g) wx `CMAKE_INSTALL_LIBDIR=lib`
  - h) `SSL_CERT_FILE`
  - i) feature patches from `arm-build/orcastudio-patches/*.patch`, applied in sorted order to
    the app module. These don't change the deps key.
- **obn patches** (`arm-build/obn-patches/`, mirrored in the Android repo's `android/obn/`):
  - **0001-cloud-callbacks-read-fresh** (r6, verified):
    - v2.2.0 snapshots `on_message_` in `connect_cloud()`.
    - A saved sign-in connects before the slicer registers callbacks, so every push_status was
      dropped.
  - **0002-start-print-try-lan-first** (r7, verified: the cube printed):
    - `start_print` always took the cloud path.
    - `POST /v1/user-service/my/task` returns **HTTP 403** on this account (cause unknown).
    - With `cloud_print = try_lan_first` plus dev_ip plus access code, the patch prints over
      LAN first: FTPS upload, then a signed `project_file`.
- **Feature patch `orcastudio-patches/0001-makerlab-tab.patch`** (in r9):
  - New `MakerLabPanel.{hpp,cpp}`: a WebView on `<model_http_url>makerlab?from=bambustudio`.
  - Signed in via `request_bind_ticket` + `api/sign-in/ticket`.
  - Allowlisted script messages:
    - `homepage_makerlab_open_3mf_binary`
    - `homepage_makerlab_stl_download`
    - `common_openurl`
    - `makerworld_model_open`
    - `homepage_login_or_register`
  - `MainFrame` adds the tab last (editor only). `show_device()` inserts Calibration before it.
- **Dark mode on Linux:**
  - The Preferences toggle exists only on Windows (`Preferences.cpp:1624-1627`). On Linux the
    app follows `wxSystemAppearance::IsDark()` (`GUI_App.cpp:3291-3294`).
  - Fix, confirmed by the user:
    `flatpak override --user --env=GTK_THEME=Adwaita:dark com.orcaslicer.OrcaStudio`.
  - Upstream bug: a theme change takes two launches (`:3227-3229` runs before `:3293`).
- **403 investigation (optional):**
  - Studio sends `start_print` directly when `cloud_print_only`, the access code is empty, or
    there's no SD card (`PrintJob.cpp:569-633`).
  - Find the cause at `log_level = debug`: `cloud_print.cpp` logs the `X-BBL-Client-Name` /
    `X-BBL-OS-Type` headers.
- **Logs:**
  - Studio log: `<data_dir>/log/debug_*.log.0`. Grep it with `grep -a`.
  - Job-log API returns only the last 5000 lines. The log zip host is blocked by the session
    proxy.

## OrcaStudio-Android (BaIanced/OrcaStudio-Android)

- **Base decision:** stay OrcaSlicer-based. OrcaStudio's engine lacks 53 libslic3r files and
  ~3289 profile files compared with OrcaSlicer. Its extras are desktop GUI/network glue, which
  Android doesn't build. The only portable candidate is the BMCU retry logic, and only if the
  user asks.
- **Upstream tracking:**
  - `.github/workflows/orca-upstream-watch.yml` runs weekly (Mondays 11:23 UTC), plus
    `workflow_dispatch` with a `force` input.
  - If OrcaSlicer main moved, it force-pushes bot branch `upstream/orca-main` (main + src-orca
    bump via `android/scripts/bump_upstream.py`, which updates `android/UPSTREAM.md` and lists
    port-dependent files) and dispatches `android-apk.yml` there.
  - Releases come only from `main`. The deps cache key hashes src-orca `deps/` +
    `cmake/modules`.
- **`android-apk.yml`:**
  - Triggers: `workflow_dispatch`, or a push to `main` touching `android/**`. Pushes to other
    branches don't build; dispatch them.
  - Build ≈ 18-26 min warm.
  - It checks for exactly **16** `ObnNative` JNI exports. Adding a JNI function means updating
    that number.
  - Artifacts are debug-signed. Release-signing secrets aren't set up.
- **obn on Android:**
  - Built as a static lib inside `liborca_jni.so` (`android/obn/obn.cmake`,
    `obn-android.patch`, patches 0001 + 0002).
  - Bridge: `android/core/jni/ObnBridge.cpp`.
  - Config dir: `noBackupFilesDir/obn`, holding `obn.conf`, the PEMs, `cacert.pem`,
    `printer.cer`, `obn.log` and `obn.auth.json`.
  - `writeDefaultConf` writes `cloud_print = lan_only`, `log_to_file = 1` and never overwrites
    an existing file. `block_cloud` stays at its default 1, which still allows sign-in and the
    printer list.
  - **Cloud HTTPS CA:** obn's vendored curl had no CA source.
    - `ObnCredentials.prepareTls` exports `AndroidCAStore` to `obn/cacert.pem`.
    - curl is compiled with `CURL_CA_BUNDLE=/data/data/io.github.baianced.orcastudio_android/no_backup/obn/cacert.pem`
      and `CURL_CA_FALLBACK` (`c23d34f`).
    - The user confirmed sign-in works with it.
- **Printer types:**
  - "Bambu Lab (LAN)": `BambuHost`, its own MQTT/FTPS client. Upload works. Print fails on MQTT,
    probably because the firmware rejects unsigned commands (not verified).
  - "Bambu Lab (signed, no LAN mode)": `ObnHost`, which prints with `start_local_print` over
    LAN, signed with the user's PEMs.
- **Account sign-in** (`net/BambuAccount.kt`, `ui/device/BambuAccountSection.kt`):
  - It mirrors `WebUserLoginDialog.cpp`: a WebView on `<host>/en/sign-in` with UA suffix
    `BBL-Slicer/v<ver> (dark) BBL-Language/en`.
  - A JS bridge maps `window.wx` / `webkit.messageHandlers.wx` / `chrome.webview` to
    `orcaNative`. Only bambulab.com/.cn may post.
  - The flow: the page posts `user_ticket_login` → `get_my_token` → `get_my_profile` → a
    `user_login` JSON → `change_user`.
  - "Use printer from account" (`get_user_print_info`) fills in the serial and access code.
  - Google sign-in in the WebView does nothing (not investigated).
- **Devices:** the user tests on several arm64 Android devices (phones and a TV box).

## User's environment

- **Chromebook:** Crostini, Debian 13, aarch64. They can also teleport the session with
  `claude --teleport <session id>`.
- **Flatpak:**
  - Installed `com.orcaslicer.OrcaStudio` r9 (MakerLab) via the updater
    `~/.local/bin/orcastudio-update.sh` (systemd user timer, daily). The updater skips the
    install while the app is running.
  - Data dir: `~/.var/app/com.orcaslicer.OrcaStudio/config/BambuStudio_OrcaSlicer/`.
  - The PEMs are there, with a backup in `~/obn-keys/`.
  - `obn.conf`: `block_cloud = 0`, `client_name = BambuStudio`, `cloud_print = try_lan_first`,
    `log_to_file = 1`, `log_level = info`.
- **A1:**
  - Its serial and LAN IP are in the user's app settings; never write them down (rule 7).
  - Cloud-bound, Developer Mode OFF, new authorization-control firmware.
  - The certificate exchange works. Bambu Handy works.
- **Android app:** signed in to the user's Bambu account, PEMs imported, printer configured as above.

## Useful facts

- GitHub access from the session is through the GitHub MCP tools: `actions_run_trigger`
  (dispatch), `actions_list` (runs), `get_job_logs`. They may fail to connect at session start;
  load them via ToolSearch.
- Tag pushes are blocked from the session. Actions create tags and releases.
- Auto mode denied cloning obn and probing the proxy. Read obn's source with WebFetch instead.
- obn logs per-frame MQTT only at `log_level = trace` (`mqtt_client.cpp`). Never ask for raw
  trace logs.
