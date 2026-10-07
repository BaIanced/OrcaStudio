# Handoff: OrcaStudio aarch64 Flatpak + OrcaStudio-Android (state as of 2026-10-07 03:20 UTC)

Read this first, then `arm-build/README.md` and the `NOTES-*.md` files next to it. The user is
referred to as they/them.

## Start here: open items, in order

1. **Android test build run 12** ([run](https://github.com/BaIanced/OrcaStudio-Android/actions/runs/37565909438),
   commit `253ee71` on Android branch `claude/handoff-continuation-rseql3`) was dispatched at
   03:15Z, and one check-in is scheduled for about 03:45Z. When it's green, the user should
   install the APK, then press **Test** and then **Print** with type "Bambu Lab (signed, no LAN
   mode)".

   Run 11 on a device (user report, 2026-10-07):
   - Sign-in and **Test** worked. The sign-in and printer.cer fixes from `fcfbec5` are
     confirmed.
   - **Print** failed with "The printer did not complete the certificate exchange; check the
     slicer credentials". That text is the app's own check (`ObnHost.kt` `upload`), raised when
     `ObnNative.installCert` doesn't see obn's `device_cert_installed` message within 15 s.

   Cause, verified against the obn v2.2.0 source; run 12's fix is **untested on a device**:
   - Every app action connects and disconnects (`DeviceController.withHost`).
   - obn's default `mqtt_keep_connection = 1` (`include/obn/config.hpp:62`) makes
     `disconnect_printer` defer the teardown by 3 s (`agent.cpp:306-317`, `:37`).
   - The deferred teardown (`agent.cpp:117-129`) drops the session but doesn't clear the
     `app_cert_install_sent_` latch. The immediate path does clear it (`agent.cpp:330`).
   - A clean MQTT disconnect reports `ConnectStatusOk` (`lan_session.cpp:130-133`), and the
     latch is cleared only on a non-OK status (`agent.cpp:573-581`).
   - So after Test, `install_device_cert` returns early (`agent.cpp:2062-2066`): no
     `app_cert_install` is sent and no `device_cert_installed` message arrives.
   - Fix: `ObnCredentials.writeDefaultConf` sets `mqtt_keep_connection = 0`, and appends it to
     an existing `obn.conf` that doesn't set the key.
   - Side note, not acted on: with keep-connection on, obn would also sign on a new session
     without reinstalling the app cert. Its own comment (`agent.cpp:1180-1186`) says the
     printer rejects that with 84033545. This could be an upstream obn report, together with
     patch 0001.
   - Unverified edge: `PrintMonitorService` keeps its own `ObnHost` open. A second connection
     replaces obn's single LAN session (pre-existing; not changed).
2. If run 12 prints on the device, ask before merging the Android branch to `main`: a push to
   `main` that touches `android/**` publishes a release. If it fails, fix on the branch and
   dispatch `android-apk.yml` there (no release).
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
| `BaIanced/OrcaStudio-Android` | cl1x/Orca-Android history plus signed Bambu printing via obn. `src-orca` submodule = OrcaSlicer. `main` = `2b16b85` (release `android-v0.1.2-r5`). Work branch `claude/handoff-continuation-rseql3` = main + `4b4a6a5`, `f9f6f51`, `c23d34f`, `fcfbec5`, `3fdd2cc` (privacy scan), `253ee71` (account sign-in and signed printing work, **unmerged**). Bot branch `upstream/orca-main` (never commit to it). |
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
  - It checks for exactly **15** `ObnNative` JNI exports. Adding a JNI function means updating
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
