# Handoff: OrcaStudio-Android + OrcaStudio aarch64 Flatpak (state as of 2026-10-11, AMS mapping)

Read this first. Address the user as Supreme Master. Older history (builds 14-50, past causes,
Flatpak details) is in `HANDOFF-ARCHIVE.md`. **Don't read the archive or `README.md` / `NOTES-*.md`
up front**; open them only when a question needs them (grep first).

## Now

Both repos work on branch `claude/handoff-continuation-rseql3` (the "test branch").
**Autonomy (user, 2026-10-11):** decide and act on whatever makes the most sense; don't stop to ask
about branch handling (there was no "two streams" rule). Main merges / releases still need the user.

- Run 38072645925 (test branch, Orca Cloud sync merge + CI cache) green, ~20 min; not installed.
- **r59 = run 38074555972 (test branch) installed on WSA:** OOM fix (user crash: a big slice's 325 MB
  `extrusions.bin` was copied into a direct ByteBuffer twice, `Viewport.kt:161` and
  `PreviewPanel.kt:268`, over the 512 MB heap). Now `Buffers.kt` memory-maps, and `Preview.cpp`
  FloatWriter writes `.tmp` + rename like the scene/paint meshes. WSA: the user's plate (97 MB
  extrusions.bin) slices and previews, Java heap 5 MB. The 325 MB slice itself: user to retest.
- **Orca plugin runtime (general capability, kept for future plugins).** User, 2026-10-11: uses no
  Orca plugins today; wants the ability kept. **FilamentHub is dropped for good (user dislikes its
  ToS); never suggest, test with, or mention it again.** The user's real filament site is
  3dfilamentprofiles.com (built in, below). Verified on WSA with a test plugin 2026-10-10/11: install
  from Orca Cloud, load, Pages page renders + messages, process option "Slicing Pipeline Plugin"
  picker (`SettingsEditor.kt` PluginPicker; engine `selection_config()` calls
  `update_plugin_manifest()`), post-process runs on Share (logcat tag OrcaPlugins), capability
  settings (r71, below). Pieces: embedded CPython 3.12.12 (Chaquopy build,
  `android/scripts/stage_python.py`) + upstream plugin host compiled unchanged
  (`android/core/plugins.cmake`); Android replacements in `android/core/plugin/` (PluginManager,
  PluginAuditManager = no sandbox hook yet, orca.host app/ui); `PluginConfig.cpp` extracted by
  `android/scripts/extract_plugin_config.py`. JNI `jni/OrcaPlugins.cpp` <-> `plugins/PluginNative.kt` /
  `Plugins.kt`; pages `ui/settings/PluginPage.kt`. Installs to
  `files/data/orca_plugins/_subscribed/<user>/<uuid>`. Not done: audit prompts, create_window,
  per-preset config overrides, printerAgent capability. Pure-Python plugins only. Uninstall (r80):
  subscribed list has Remove (`PluginManager::delete_plugin` in `AndroidPluginManager.cpp`);
  Install over a loaded plugin now replaces it (was "restart to update"). Verified on WSA with Orca
  Inspector (install, reinstall, remove; it was not installed before, so removed again).
  WSA wedged once (no app window): stop WsaClient, `Start-Service WsaService`, `Start-Process wsa://<package>`.
  "Plugins Used" restore fix (1fcfb56) verified. G-code save picker remembers a folder in the user's
  own project dir: test saves via Share + logcat.
- **3D Filament Profiles (3dfilamentprofiles.com) = r67, run 38108434060, verified on WSA
  2026-10-10.** The utility the user actually uses (all features wanted). No public API (issue #134),
  Vercel bot checkpoint (scripted fetches 429; WebView passes). Built in, not a plugin:
  - Models tab 4th site (`ModelSite.FILAMENT_PROFILES`); the user is signed in there (email/GitHub/
    Discord; Google likely blocks WebView sign-in).
  - Preview > More > "Log print to 3D Filament Profiles": `net/FilamentProfiles.kt` builds
    `/my/print/log?v=1&f=&p=&d=<base64url G-code comment lines>` like the site's own
    `tools/slicer-print-log/3dfp-print-log.py`; opens in the Models tab (`UiState.modelsUrl`). Verified:
    page lists printer, time, 66.70 g per filament + spool picker. Never press Subtract in tests.
  - Spool profile export (My Spools row > Actions > Export slicer profile > OrcaSlicer/A1/0.4) is a
    blob: JSON revoked on click: BRIDGE_JS keeps blobs 60 s (`__orcaBlobs`), the download listener
    reads them back; `.json`/`.orca_*`/zips of JSON go to the preset import (`FileController.openDownloaded`).
    Imported "Overture PETG White (3DFP T41GBvwn4) @A1" (user approved exporting any spool).
  - CDP on its page: `cdp.mjs` / `pick.mjs` (Radix selects need pointer events) in the scratchpad.
- Branches: `claude/orca-plugins` was fast-forwarded into the test branch; work on the test branch.
- **Session gotcha:** the app restores `files/session/session.3mf` on start and saves it only in
  `onStop` (41 MB, takes a while). `am force-stop` skips the save, so test edits reset before a
  force-stop come back. WSA: HOME / another app did not trigger onStop.
- **AMS mapping (2026-10-11, b361cad, r70 = run 38119747043, installed on WSA).** Verified (FTPS :990
  blocked by iptables during the test so nothing could print): dialog maps "1 · PLA" (#FEC600) to
  A1 PLA Basic (yellow), dropdown lists A1-A4; Cancel; export slice_info now has prediction, weight,
  `<filament id="1" type="PLA" color="#FEC600" .../>`. Real print (user OK'd): 10 mm cube on a temp
  Plate 2, dialog -> A1, "Print started", obn log `use_ams=1` (all earlier prints 0). **User confirmed
  2026-10-11: printed yellow from A1 = AMS mapping verified.** Temp plate deleted, app closed via window close. User: the r69
  LAN cube printed from AMS A4 (PETG) instead of yellow PLA and globbed the nozzle. Cause: obn print
  got `use_ams=false`, empty `ams_mapping` (`ObnHost.kt` print call; `BambuHost.kt` same). Fix:
  `net/AmsMapping.kt` (port of `DevMapping.cpp:122` ams_filament_mapping: same type, closest CIE76;
  serialization as `SelectMachine.cpp:1343`), Print on Bambu -> `ui/preview/AmsMappingDialog.kt`
  (pre-filled, pick per filament) -> `DeviceController.confirmPrint`; JNI `ObnNative.print` gained
  `amsMapping2`. Also fixed: `.gcode.3mf` slice_info had no filaments/time/weight since plugin
  post-process made exports a copy (lookup by path; `exportGcode3mf(..., sliced)`).
  User's AMS lite: A1 yellow, A2 matte black, A3 white, A4 PETG. **Test print needs the user's OK.**
  Safe dialog test: `iptables -I OUTPUT -d <ip> -p tcp --dport 990 -j REJECT` (root), Print, Cancel,
  then `iptables -D ...`. Closing the WSA window via `CloseMainWindow()` on the WsaClient
  "OrcaStudio-Android" window runs onStop (session save verified 2026-10-11), unlike force-stop.
- **Session handling (user, 2026-10-11):** keep this file current before stopping any task so the
  user can /clear at any point; cheaper (haiku/sonnet) subagents OK for builds/installs/searches.
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
- Verified 2026-10-11 (r77): MakerWorld "Full site" chip (header, no BBL UA, back to slicer mode);
  theme switch recreates the Models browser (page prefers-color-scheme follows Light/Dark); CI
  cache works (builds ~6 min). Orca Cloud pull/upload: user tested on r72 (see below).
- **r79 = run 38155435432 (Models zoom fix), installed + verified on WSA 2026-10-11:** Ctrl+wheel / pinch did nothing on MakerWorld because
  its viewport meta has `maximum-scale=1.0, user-scalable=no`. `ZOOM_JS` in `ModelsScreen.kt` strips
  those (MutationObserver re-applies). Verified on r79 (CDP + real Ctrl+wheel): meta unlocked on load, scale 1 -> 1.21 -> 1.46 -> 1.
  (The first Ctrl+wheel right after a meta change is ignored; later ones work.) Pinch: user to test.
- **Section view (r80 = run 38157697528; r82 = 38158608656 panel fit + mirrored winding; r83 =
  38159448169 panel clears the tool column; r84 = 38159995534 two-row panel, installed on WSA, layout
  verified), verified on WSA r80/r82/r84:**
  port of GLCanvas3D's section view. `render/SectionView.kt` (ratio, normal = camera direction at
  first use, plane over the objects' bounding sphere as `_get_section_view_plane`), shaders discard
  the camera side (`uSection`), back faces through the cut drawn dark grey as cut faces (no
  MeshClipper). View menu > Section view toggles + opens the panel (`SectionViewPanel.kt`: slider,
  Set viewing angle, Reset, Close); Alt+wheel +/-0.01 (verified 0.50 -> 0.52 -> 0.48); Esc closes the
  panel. Mirrored copies: scene/paint export now keeps triangles facing out (`OrcaScene.cpp`
  transform(..., true), `OrcaTools.cpp` emit swaps corners); verified r82 by mirroring a copy on the
  user's plate, then force-stop (no session save) -> plate unchanged. Reset/Close verified r82.
  Not done: travels/markers aren't clipped, picking ignores the cut.
  WSA gotcha: screenshots go stale while the window isn't foreground; run focus.ps1 first.
- **Plugin capability settings (2026-10-11), r71 = run 38122146536 (38eb085), installed + verified
  on WSA:** More > Orca Cloud section: "<capability> settings" button per capability ->
  `ui/settings/PluginConfigDialog.kt` (custom page from get_config_ui with the plugin-config-ui.js
  bridge via JS interface `orcaConfigHost`, host theme vars; else JSON editor); native
  `config_open/save/restore` in `AndroidPluginRuntime.cpp` (global config layer only). Saves land in
  `files/data/orca_plugins/config.json` and reload correctly.
- **r77 = run 38128522536 (f80e7a0), installed + verified on WSA 2026-10-11:** Ctrl camera
  shortcuts fixed. Two causes: (1) Android offers Ctrl keys to `onKeyShortcut` only when normal
  dispatch leaves them unused, which never happened with the 3D view focused ->
  `MainActivity.dispatchKeyEvent` runs `onKeyShortcut` first for Ctrl key-downs while the view has
  focus; (2) the view only took focus on a click -> `PlateView.onGenericMotionEvent` takes focus on
  any hover/scroll unless a text field has it (desktop `GLCanvas3D.cpp:4472-4482`). Verified: View
  menu used, hover only, Ctrl+0 resets the view; `adb shell input keycombination 113 8` (Ctrl+1) ->
  Top view. **Windows-side Ctrl+1..9 (keys.ps1 keybd_event) never reach Android** (log shows only the
  Ctrl key; Ctrl+0 arrives): WSA or something on the PC drops them, not fixable in the app. Ask the
  user whether a real keyboard's Ctrl+1 works. OrcaInput DEBUG logs "focus" / "shortcut" / "key".
- **r74 = run 38126545229, installed on WSA 2026-10-11:** Quit dialog verified (centred title, note,
  equal No/Yes). Modifier input verified with modin.ps1 (synthetic real-OS input): Ctrl/Alt/Shift+wheel
  arrive as ACTION_SCROLL (meta CTRL 0x3000 / ALT 0x12 / SHIFT 0x41, Shift as h=-1) and zoom (screenshot
  diff); Ctrl/Alt/Shift+middle-drag pan (WSA sends touch DOWN + hover moves buttons=4, no touch MOVE/UP).
  The saved r72 log (`~/orca-android-tools/orcainput-r72.log`) has no modifier events in the new
  format, so the user's earlier "deliver nothing / plain drag" reports aren't reproduced; ask the
  user to retest on r75 if they still see it. Alt+wheel section view: done in r80 (below).
  modin drags shift the camera: restore with View (camera icon) > Fit plate.
- **r73 = run 38125719209 (built, superseded by r74):** undo limit setting (More > Misc, 1-5000, default 200; was a
  fixed 30, `OrcaScene.cpp` m_undo_limit / engine call setUndoLimit). Verified on r71 (temp plate,
  removed): Delete key (adb + real keyboard), real Ctrl+Z, arrows 10 mm / Shift+arrow 1 mm all work
  already. Scratch tools: `keys.ps1 -Keys <vk...>` (real keys), `click.ps1` (picks the wrong WsaClient
  window, unfinished).
- **r72 = run 38125329109 (installed on WSA 2026-10-11, OrcaInput DEBUG on):** Back on Prepare with nothing to clear asks
  "Quit?" Yes/No (Back closes it); More > Misc > "Press Back twice to quit" option (toast, 2 s).
  Shift+wheel in the 3D view used AXIS_HSCROLL (=0 -> always zoom out): fixed. OrcaInput log now
  has meta/axes/tool/source. User test results 2026-10-11: Orca Cloud pull no error (same presets),
  upload "0 uploaded" (fine); plain wheel zooms 3D view (= desktop). Ctrl/Alt+wheel and modifier+middle-drag:
  see r74 (work in synthetic tests). Capture tool: `scratchpad/modin.ps1 -Key 0x10|0x11|0x12 -Mode
  middle|wheel` + `setprop log.tag.OrcaInput DEBUG` (WSA input isn't visible to getevent/dumpsys).
- Order (user): Orca Cloud login (done), preset sync (built, testing), plugin runtime (done as a
  general capability; no plugin in active use). **Next (user, 2026-10-11): modeling in the app**
  - OpenSCAD, or any other way to use the slicer as 3D-printing modeling software. Not started;
  no code yet. Ideas to check first (all unverified): upstream src-orca may already have a
  "Design" tab (GLCanvas3D.hpp comment mentions "the Design tab's canvas" + studio lighting) -
  grep `src-orca/src/slic3r/GUI` for it; OpenSCAD's WebAssembly build (openscad-wasm /
  openscad-playground) could run in a WebView and hand the STL to the import path; upstream
  shapes + mesh boolean gizmo as a native option. Present options to the user before building.
  **Checked 2026-10-11 (recommended: native OpenSCAD core in `liborca_jni.so`, not WASM):**
  - WASM build forces `MANIFOLD_PAR OFF` (single-threaded) and NULLGL; native gets Manifold + TBB
    on all cores. OpenSCAD @c0ac828 has `HEADLESS`/`NULLGL` and a static `OpenSCADLibInternal`.
  - Shared with our Android deps prefix: Boost (has regex; lacks program_options, used only by
    `openscad.cc` main -> patch out), CGAL, GMP/MPFR, Eigen, TBB, FreeType, OpenSSL, zlib, expat.
    New: Manifold + Clipper2 (submodules; Orca's `deps_src/clipper2` is 2.0.1 -> watch duplicate
    symbols), double-conversion, libzip, libxml2, harfbuzz, fontconfig, flex/bison (host).
  - glib use outside `src/gui` is ~10 `g_utf8_*`/`gunichar` calls (`str_utf8_wrapper.h`,
    `UnicodeIdentifier.cc`, `Value.cc`, `FreetypeRenderer.cc`) -> small shim over utf8proc
    (minSdk 29, so NDK ICU (API 31) is out).
  - Upstream "Design tab" (`src/slic3r/GUI/CAD/*`, `libslic3r/CAD/*`, OCCT B-rep sketch/primitives)
    exists but is wx GUI; Android builds with `SLIC3R_CAD OFF` (`android/core/CMakeLists.txt:38`).
  - **Step 1 started (user said "start", 2026-10-11):** `android/openscad/` superbuild ->
    `libopenscad.so` (C API `bridge/scad_bridge.h`: `scad_render(src, file, params_json)` ->
    triangle soup + log, `scad_parameters()`), only `scad_*` exported (`--exclude-libs,ALL`).
    `shim/` = glib subset over utf8proc + gettext no-ops. `patch_openscad.cmake` drops
    `src/openscad.cc` + program_options and adds the bridge subdir. CI `android-openscad.yml`
    (push to `claude/**` touching android/openscad; restores the apk deps cache, own deps cache +
    ccache; artifact `libopenscad-arm64-v8a` incl. `scad_smoke`, fonts, MCAD). **Step 1 DONE: run 38168198443 green, verified on WSA 2026-10-11** (lib 12 MB stripped; scad_smoke:
    parameters JSON, CSG render 1792 tris, Customizer override works; `text()`/fonts/perf untested). Test:
    `gh run download <id> -n libopenscad-arm64-v8a`, `MSYS_NO_PATHCONV=1 adb push` lib+bin+resources to
    /data/local/tmp/scad, `LD_LIBRARY_PATH=. ./scad_smoke /data/local/tmp/scad/resources`. Fixed on the way:
    pipx meson >=1.6.1, expat.pc, libxml2 pinned (NDK host .so), target `scad_core` (name clash).
  - **Step 2 DONE (2026-10-11): r85 = run 38170713625, r86 = 38172403593, r87 = 38173875723 (installed
    on WSA, verified below); r88 = 38174598085 (gear example pitch fix only, not installed).**
    `bridge/scad_jni.cc` (JNI for `app.orcaandroid.scad.ScadNative`, writes binary STL, returns
    {ok,dimension,triangles,log}; OPENSCAD_FONT_PATH=/system/fonts, HOME/XDG_CACHE_HOME=cache).
    CI: android-openscad.yml caches `out/` as `android-openscad-out-<tree hash of android/openscad>`;
    android-apk.yml restores it and stages `$BUILD_ROOT/openscad-jniLibs` + `openscad-assets/openscad`
    (gradle adds both; miss = warning, APK without OpenSCAD -> "This build does not include OpenSCAD").
    App: `scad/ScadService.kt` (process `:scad`, Messenger, 256 MB-stack thread, unpacks assets to
    `files/openscad-resources` per lastUpdateTime; `OrcaApp.onCreate` returns early in `:scad`),
    `scad/ScadClient.kt` (cancel = kill the :scad process via runningAppProcesses),
    `scad/ScadModel.kt` (Customizer JSON parse/encode, vectors as "[a, b]" strings; 3 examples),
    `ui/ScadController.kt` (UiState.scad; draft in `files/openscad/draft.scad|json`; render -> loadModels,
    replaces the object it placed (by name) keeping offset xy/rotation/scale/mirror; auto-render on
    Customizer change once an object is on the plate), `ui/scad/ScadEditor.kt` (panel: Code tab with
    highlighting/line numbers/auto-indent/Tab, Customizer tab, console with clickable "line N",
    Render/Update/Add as new/Stop; F5/F6/Ctrl+Enter render, Ctrl+S save). Entry: Prepare + menu and
    bed context menu "OpenSCAD model"; opening .scad files (also in zips; main = file no other includes).
    Wide: panel replaces the 380 dp side panel (45% width, 420-640 dp); phones: over the view with
    "Show plate". **Verified on WSA (r85/r86):** editor look (highlighting, line numbers, tabs);
    box renders + places (414 tris, 0.4 s); Customizer slider auto re-renders in place; text tag
    (fonts) 3,506 tris; error log auto-opens console; Stop kills :scad and a fresh one serves the next
    request; 6000-sphere for() renders after the RLIMIT_STACK raise (was a false "Recursion detected");
    new objects go to a free spot (2nd box beside the 1st). Fixed on the way: `parser_init()` (library
    path), RLIMIT_STACK 240 MB in scad_init, client restarts :scad after a "Recursion detected" log
    (OpenSCAD's 1M tail-call limit left the process rejecting all calls), `handleDependencies()`.
    r87: MCAD gear renders (use<> works; the example's pitch was in old units -> 2.5 m gear, fixed in
    r88: MCAD spur gear takes mm per tooth, involute_gears.scad:324). Console "line N" tap switches
    to Code and scrolls to the line (r86). Untested: Save/Open .scad via the picker, phone layout,
    Ctrl+Enter/F6/Ctrl+S, Tab/auto-indent, opening .scad from a download/zip.
    Test helper: `~/orca-android-tools/tapf.sh x y` (focus + tap; unfocused WSA taps are lost).
    **WSA session gotcha (2026-10-11):** the session got saved mid-test (14:22) with test objects;
    `CloseMainWindow()` now kills the app without onStop (no save). Reliable save: open the system
    file picker from the app (Add > Import model), wait for session.3mf mtime, force-stop
    documentsui. Test on a temp Plate 2 and remove it after. When deleting objects by list
    position, verify the selection first (the list shifts; Pose08 got deleted once, undone).
  - **Step 3 DONE: r89 = run 38178385444 (commit "keep the design with the object in the 3MF"), installed +
    verified on WSA 2026-10-11:** box with a modifier, Customizer width 60->90 replaced the mesh in
    place, modifier kept; session.3mf held `module` = openscad JSON (source newlines intact); after
    force-stop + restart the restored box offered "Edit OpenSCAD design", which loaded the box (draft
    was the gear) and Update on plate replaced it (object count unchanged). Painting remap untested.
    Temp plate deleted, session saved clean (8 objects). Details: design kept in
    `ModelObject::module_name` = "openscad:" + compact JSON {name, source, values} (`ScadDesign` in
    `scad/ScadModel.kt`; 3MF writes it as `<metadata key="module">`, desktop Orca round-trips it;
    no submodule change). Scene JSON `module` -> `SceneObject.module`. Engine calls `replaceMesh`
    (port of `Plater.cpp:11602` replace_volume_with_stl: keeps settings/modifiers/instances, remaps
    painting) and `setObjectModule` (no undo step) in `OrcaScene.cpp`. Object context menu "Edit
    OpenSCAD design" -> `ScadController.editObject`. Native + Kotlin compiled locally. To test:
    render, paint/setting on it, Customizer change keeps both; save project, reload, Edit design.
    Not done: small in-editor preview; relative include<> files aren't embedded.
  - **r90 = run 38182983535 (commit "Modeling: Assemble ..."), CI green, installed on WSA;
    results below:**
    - Engine `assemble(items)` (port of `GUI_ObjectList.cpp:3045` merge: copies become parts of one
      "Assembly", world placement kept) and `mesh_boolean(object, src, tool, op, keepTool)` (port of
      `GLGizmoMeshBoolean.cpp:381-431` via `MeshBoolean::mcut::make_boolean`, painting remapped).
      Deviation: the gizmo sets the result's offset to the old part's offset (`:503`), which shifts a
      union with an off-centre part; we keep add_volume's centred offset. Added parts are named "Part N".
    - UI: multi-select toolbar + context menu "Assemble"; object More menu "Add part" (box at the
      object centre) and "Mesh boolean" (dialog `PrepareDialogs.kt` MeshBooleanDialog; context menu
      entry when the object has 2+ parts).
    - OpenSCAD: `ScadDeps.collect` embeds local include<>/use<> files (relative to the main file,
      2 MB cap, library files excluded) in the design JSON `files`; `ScadDesign.unpack` restores them
      under `files/openscad/designs/<hash>/` on Edit design. Draft meta now always keeps an opened
      file as the include base (was dropped once the text changed).
    - **r90 on WSA (temp Plate 2, 2026-10-11):** Assemble verified (cube + cylinder -> "Assembly",
      positions kept, 732 tris). Mesh boolean dialog verified; difference ran (cylinder didn't overlap,
      so result = cube). Found: "Add part" threw "Unsupported volume type" (code 0 missing) and parts
      couldn't be moved at all.
    - **r91 = run 38183994457:** fixes Add part (placed beside the object at +X like
      `GUI_ObjectList.cpp:2565-2578`), part/modifier Position-in-object / Rotation / Size fields under
      the selected part in the object card (engine `setTransform` takes `volume`; scene JSON volumes
      carry rotation + scale).
    - **r91 verified on WSA 2026-10-11 (temp Plate 2, deleted after; session saved clean, 8 objects):**
      Add part = 10 mm box beside the 20 mm cube; part X 15 -> 8 via the new field moved it into the
      corner; difference 12 -> 38 tris; undo -> 2 parts; intersection = 7x10x10 box in place (centre
      +6.5/-5 mm); union 46 tris, centre +1.5 mm (no shift). Painting through a boolean: untested.
      Label "(mm) (mm)" fixed after (commit "Part position label", not built yet - goes with the next build). OpenSCAD: a .scad zip with a local include, render, Edit design
      after restart.
  - Plan: separate cached OpenSCAD deps stage (don't touch the Orca deps cache key), JNI
    `renderScad(src, params)` -> TriangleMesh straight into the plate, source + Customizer values
    stored in the 3MF so the object re-renders when edited; Compose code editor + Customizer panel.

### Orca Cloud (Kotlin port of upstream `OrcaCloudServiceAgent.cpp`)
- `net/OrcaCloud.kt`, `net/OrcaCloudLoopback.kt`, `ui/settings/OrcaCloudSection.kt`.
- Sign-in page `https://cloud.orcaslicer.com/orcaslicer-login`, JS bridge registered as `wx`;
  `get_login_cmd` -> `window.postMessage(login_config)` (PKCE S256, loopback
  `http://localhost:41172..41174/callback`). Code exchange `POST auth.orcaslicer.com/auth/v1/token
  ?grant_type=pkce`. Refresh with 15 min skew; 400/401/403 signs out. Session: AES-GCM with an
  AndroidKeyStore key in `noBackupFilesDir/orca_cloud/session.sec`; the app backup carries it
  decrypted inside its passphrase-encrypted zip (`AppBackup.kt`), plus `orca_plugins/config.json` (r80).
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

### Plugin host surface (what upstream plugins expect; implemented)
- orca.base, @orca.plugin, orca.register_capability, orca.ExecutionResult.{success, skipped},
  capability get_name/get_icon/has_config_ui/get_config_ui/get_default_config/get_config/on_load/
  on_unload/on_message/post_message/get_ui, orca.host.preset_bundle(), orca.host.plugin.storage(),
  orca.host.app_language(); `webbrowser.open` routed to the app. Page JS bridge = upstream
  ORCA_BRIDGE_JS (`src-orca/src/slic3r/GUI/Widgets/WebHosting.cpp`). SlicingPipeline runs only
  at `psGCodePostProcess` on Android (on the exported G-code, in place).
- Pull files from WSA with `adb exec-out "su -c 'cat ...'"` (plain `adb shell` mangles binaries).

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

### Task list (user, 2026-10-11; not started unless noted)
- **Auto-save:** the session is saved only in `onStop`, so a crash / force-stop loses edits. Desktop
  Orca has Preferences "Backup" switch + interval (grep `backup_switch` / `backup_interval` in
  src-orca) - port as More > Misc "Auto-save every N min" and/or save on plate change (user: a
  setting would be a nice touch unless saving on build plate change is the logical choice).

### Other open items
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
- WSA lost DNS once: `wsaclient /shutdown` and relaunch fixed it. adb `input` has no Shift/Alt state.
- **WSA -> LAN printer:** WSA shares the PC's address; only its virtual gateway answers ARP, so LAN
  hosts give "No route to host" (Local network access is on; no effect). Fix after each WSA start:
  `wsa-lan.ps1 <printer-ip>` (routes the host via the gateway in table 1002). Ping stays dead, TCP
  works. Verified 2026-10-11: cube printed over LAN (FTPS upload, queued), r69.
- Cloud-only print (no LAN) fails `-2060 upload poll timeout`: server stays "running" (> 2 min;
  obn uploads the full .gcode.3mf as the config file). Patch 0004 tried a longer poll; reverted.
- Printing from the app shows "Log print to 3D Filament Profiles" after success (verified).
- The user's Chromebook (Crostini, aarch64) runs the Flatpak; A1 printer is cloud-bound
  (Developer Mode off); the app is signed in to their Bambu account with PEMs imported.

## Repos
| Repo | Notes |
|---|---|
| `BaIanced/OrcaStudio-Android` | cl1x/Orca-Android + signed Bambu printing via obn (static in `liborca_jni.so`, `android/obn`). main = PR #3 merge (pre-release `android-v0.1.2-r37`). Bot branch `upstream/orca-main` (never commit). Builds run on dispatch only (`gh workflow run android-apk.yml --ref <branch>`). |
| `BaIanced/OrcaStudio` | Flatpak fork; ours: `arm-build/`, `.github/workflows/arm-*.yml`. Latest release r9 (MakerLab tab). Details in the archive. |
| `ClusterM/open-bamboo-networking` | obn pinned v2.2.0 + local patches 0001 (cloud callbacks), 0002 (start_print try LAN first), 0003 (MQTT CA from `SSL_CERT_FILE`). |
