# Handoff: OrcaStudio aarch64 Flatpak + OrcaStudio-Android (state as of 2026-10-09 08:30 UTC)

Read this first, then `arm-build/README.md` and the `NOTES-*.md` files next to it. The user is
to be addressed as Supreme Master.

## Start here: open items, in order

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
