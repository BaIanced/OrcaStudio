# Handoff: OrcaStudio aarch64 Flatpak + OrcaStudio-Android (state as of 2026-10-06 03:05 UTC)

Read this first, then `arm-build/README.md` and the `NOTES-*.md` files next to it.

## Working rules for the next session (the user asked for these; the last session broke them)

1. **Verify against source before recommending any change.** Before telling the user to change a
   setting or try a workaround, read the obn / OrcaStudio code path that decides whether it works,
   and cite file:line. Last session's mistakes all came from skipping this step:
   - `cloud_print = try_lan_first` was suggested without checking that v2.2.0 only applies it to
     `start_local_print_with_record`, not to `start_print`.
   - "Sign out and back in" was suggested without checking that logout keeps the cloud MQTT
     session alive.
   - A push_status count was run at `debug` level, which never logs incoming frames.
2. Label anything untested as untested, inline: "I need to verify [X] for [Y]".
3. **User's output rules** (from his saved preferences):
   - Before any shell command, print a pre-flight block: 1. BLIND SPOTS, 2. EXTRAPOLATED RISKS
     (2), 3. CAPABILITY VALIDATION (YES/NO).
   - Show calculations instead of doing them silently.
   - Give a direct verdict, briefly, with nothing left out.
4. Keep check-ins cheap: scheduled single checks, not live monitors.
   - Builds run on GitHub (free for these public repos).
   - The user's environment is a Chromebook Linux container (Crostini, Debian 13, **aarch64**).
     It's the host side, not inside the Flatpak.

## Repos

| Repo | Purpose |
|---|---|
| `BaIanced/OrcaStudio` | Public fork of jarczakpawel/OrcaStudio. Everything we own is in `arm-build/` and `.github/workflows/arm-*.yml`; the rest stays identical to upstream. |
| `BaIanced/OrcaStudio-Android` | Plain repo (not a GitHub fork) holding cl1x/Orca-Android history, remote `upstream` = cl1x. Adds signed Bambu printing via obn. |
| `ClusterM/open-bamboo-networking` (obn) | Network plugin, pinned **v2.2.0** (`5e6a359c71a0c07476f5d372bf7ad0f2b43efe94`). We carry local patches. |

## Flatpak pipeline (BaIanced/OrcaStudio)

- `arm-flatpak.yml` builds on `ubuntu-24.04-arm` in two stages:
  - Deps are cached under a key from `make-manifest.py --print-deps-key`.
  - The app plus obn is built, then bundled, then smoke-checked, then released as
    `arm64-<os_tag>-obn-<obn_tag>-r<N>` with `OrcaStudio-aarch64.flatpak` and `SHA256SUMS.txt`.
- `arm-upstream-watch.yml` runs daily:
  - It bumps `arm-build/versions.json` on new upstream tags and calls the build.
  - Its fork merge is best-effort. The build checks out the upstream commit directly.
- `make-manifest.py` generates the manifest from upstream's
  `scripts/flatpak/com.orcaslicer.OrcaStudio.yml`. Its transformations:
  - **a)** FFmpeg prefetch.
  - **b)** obn module appended.
  - **c)** `command: orcastudio-arm-launcher`.
  - **d)** BUILD_INFO.
  - **e)** orca_deps `type: dir` replaced by a reproducible tar. flatpak-builder gives dir sources
    a random checksum, so they never cache.
  - **f)** add `shared/` to the app module. Upstream omits it, but `SlicerLinuxRuntimeForwarderExports.cpp`
    includes from it.
  - **g)** wxWidgets `-DCMAKE_INSTALL_LIBDIR=lib`. Without it the libraries landed in `/app/lib64`
    and the app failed at launch.
  - **h)** `--env=SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt`.
- The smoke check installs the bundle on the runner. It also runs `ldd` inside the sandbox on
  everything, and fails on "not found".
- Measured times (4 vCPU ARM runner): deps ≈ 26 min, app ≈ 41 min cold. With cache: ~5 min
  app + bundle.

### Local obn patches (`arm-build/obn-patches/`, applied by `obn-module.yml` after the obn git source)

- **0001-cloud-callbacks-read-fresh.patch** (released in r6, verified working by the user).
  - Bug: `Agent::connect_cloud()` snapshots `on_message_` / `on_printer_connected_`.
  - With a saved sign-in, `bambu_network_start()` auto-connects before OrcaStudio registers them,
    so every `push_status` was dropped and the Device tab showed "Failed to connect to the printer".
  - Proved with trace logs: 4.7 KB push_status frames arrived, Studio kept sending pushall every
    5 s, and nothing was forwarded.
  - Logout/login does **not** help: the cloud session stays connected, so the stale snapshot
    persists.
  - Upstream main fixed `on_printer_connected` but still snapshots `on_msg`.
- **0002-start-print-try-lan-first.patch** (released in r7, **verified working by the user**
  2026-10-05 21:52 −0600: the cube printed).
  - `bambu_network_start_print` (`abi_print.cpp`) in v2.2.0 always calls `run_cloud_print_job`.
  - That path fails at `POST /v1/user-service/my/task` → **HTTP 403** "The client does not have
    access rights to the content." on this account, even with `client_name = BambuStudio`
    (verified present in obn.conf).
  - Cause of the 403 is unverified. obn's comment names `X-BBL-Client-Name` or `X-BBL-OS-Type`
    mismatches.
  - 0002: with `cloud_print = try_lan_first` (and dev_ip plus access code known; the code comes
    from `lan_access_code_for()`), it runs `run_local_print_job` first: LAN FTPS upload, then the
    signed `project_file` via `send_message()`, which uses LAN MQTT if connected and the cloud
    channel otherwise. If that fails, it falls back to the cloud path.
  - The bundled `obn.conf.default` now ships `cloud_print = try_lan_first`.

### Session 2026-10-06 findings

- Run 37406830869 succeeded on 2bb3a93d. Release `arm64-v02.08.01.55-p6-obn-v2.2.0-r7` was published
  at 03:08:15Z.
  - The `Applying patch 0002` line was **not seen**. The job-log API returns only the last 5000
    lines, and the zip host (results-receiver.actions.githubusercontent.com) is blocked by the
    session proxy.
  - Indirect evidence: the obn module lists 0002 as a `type: patch` source, flatpak-builder aborts
    the build if a patch fails, and the job was green.
- When OrcaStudio calls `start_print` at all (`src/slic3r/GUI/Jobs/PrintJob.cpp:569-633`, cloud
  connection, not `lan_mode_only`):
  - Studio already runs `start_local_print_with_record` first when `!cloud_print_only &&
    password && dev_ip && has_sdcard`. It calls `start_print` only as a fallback (`:611`, `:626`).
  - Otherwise it goes straight to `start_print` (`:632`). In that case `params.comments` records
    why: `no_ip` / `low_version` (= `is_support_cloud_print_only`, `SelectMachine.cpp:3777`) /
    `no_sdcard` / `no_password` (`:574-581`).
  - So 0002 changes the outcome only when `dev_ip` is set. With `no_ip`, 0002 logs
    `try_lan_first skipped (missing dev_ip)` and the 403 cloud path still runs.
  - `dev_ip` for a cloud printer comes from push_status `net.info[].ip`
    (`DeviceManager.cpp:3546-3553`), which arrives only with 0001 in place.
- Studio's own log: `<data_dir>/log/debug_<Day>_<Mon>_<dd>_<HH>_<MM>_<SS>_<pid>.log.0`
  (`GUI_App.cpp:2879-2882`, `utils.cpp:384-391`). The default level is `info` (`AppConfig.cpp:349`),
  so the `print_job:` branch lines are logged.

- First user test (21:42 −0600) proved nothing about r7.
  - Both cube prints were at 20:56 and 20:57 −0600. r7 was published at 03:08Z, which is
    21:08 −0600, so both prints ran on r6.
  - The obn line shows `start_print ... ip=192.168.4.30`, so Studio does pass `dev_ip`.
    `no_ip` is ruled out, and 0002's LAN branch should be reachable.
  - The Studio log is detected as binary, so grep it with `grep -a`.
  - The Studio log for those prints shows `print_job: send with cloud`, i.e. the direct
    `start_print` branch (`PrintJob.cpp:629-632`). With `dev_ip` set, the cause is
    `cloud_print_only`, an empty access code, or no SD card; Studio does not log which.
    Either way 0002 should take the LAN path, since it needs only dev_ip, an access code
    (from `lan_access_code_for`) and a file.
  - The result was `-2120` = `BAMBU_NETWORK_ERR_PRINT_WR_POST_TASK_FAILED`
    (`bambu_networking.hpp:81`), which is the obn create_task 403.

### Next steps (Flatpak)

1. DONE. Patch 0002 is verified on r7.
   - The installed `libbambu_networking.so` contains the 0002 string (`grep -a -c` = 1).
   - BUILD_INFO shows `release_tag=...-r7`.
   - The 21:51:57 print logged, in order: `start_print: cloud_print=try_lan_first -> local print
     over LAN` → `local_print: upload path=ftps :990` → `ftps: logged in to 192.168.4.30:990` →
     `STOR /Cube.gcode.3mf ok (97646 bytes)` → `queued for printing`. Studio logged
     `print_job: send ok.`, which it logs at error severity (`PrintJob.cpp:701`, harmless).
   - The cube printed.
   - Still unknown: whether `project_file` went over LAN MQTT or the cloud channel. The grep filter
     did not include obn's send_message lines.
2. Watch for regressions on other print types (AMS mapping, timelapse, multi-plate). They are
   untested with 0002.
3. Optional: find the real 403 cause by running at `log_level = debug`.
   - `cloud_print.cpp` logs `X-BBL-Client-Name` / `X-BBL-OS-Type` and PoP headers for create_task.
   - Compare with upstream issues.
4. Consider reporting 0001 upstream (ClusterM/open-bamboo-networking). The user said he doesn't
   want to learn PR mechanics, so do it for him and give him a link.

### Session 2026-10-06 later findings

- **Dark mode.** The Preferences toggle exists only on Windows (`Preferences.cpp:1624-1627`). On
  Linux the app takes `dark_color_mode` from `wxSystemAppearance::IsDark()` at every start
  (`GUI_App.cpp:3291-3294`). In wx 3.3.2 that check compares window text brightness against the
  window background.
  - Fix (user-confirmed, the whole UI is dark):
    `flatpak override --user --env=GTK_THEME=Adwaita:dark com.orcaslicer.OrcaStudio`.
  - Upstream bug: after a theme change it takes two launches. `init_label_colours()` and
    `Update_dark_mode_flag()` (`:3227-3229`) run before the new value is written (`:3293`).
    The `:3314` re-check compares against the already-written value.
  - Offered the user an optional patch; not done.
- **OrcaStudio-Android:** patch 0002 was added (`android/obn/obn.cmake`), pushed on branch
  `claude/handoff-continuation-rseql3`, and **not merged to main**. A push to main that touches
  `android/**` triggers the APK build.
  - The app calls only `start_local_print` and writes `cloud_print = lan_only`, so 0002 has no
    runtime effect there.
- **Should Android be based on OrcaStudio?** Compared
  jarczakpawel/OrcaStudio `bef044f4` with OrcaSlicer `2769b12` (the Android `src-orca`
  submodule) using a tree-only fetch.
  - `src/libslic3r`: OrcaStudio adds 0 files, lacks 53 (CAD/sketch, FilamentMixer,
    TextureToColor, PreciseSeam, FillSpiralInset, FillCornerSmoothing, AssimpImport, ...), and
    differs in 149. Its only engine commits are the initial import and "update 02.08.01.55";
    the only engine marker is `SLIC3R_APP_FULL_NAME "OrcaStudio"`.
  - `resources/profiles`: OrcaStudio lacks 3289 files and has 1655 extra.
  - OrcaStudio's additions are all in the desktop GUI and network glue (`src/slic3r`): Linux
    runtime forwarder, gstreamer camera, PluginWebDialog, BMCU retry and X1C wait fixes in
    PrintJob/SelectMachine. Android doesn't build `src/slic3r`.
  - So rebasing Android onto OrcaStudio would subtract features. The only portable candidate
    is the BMCU retry logic, which needs the user's go-ahead.

- **OrcaStudio-Android tracks OrcaSlicer main** (branch `claude/handoff-continuation-rseql3`,
  not merged to main):
  - `0c4012c` adds `.github/workflows/orca-upstream-watch.yml`. It runs daily, and when
    OrcaSlicer main has moved it recreates and force-pushes bot branch `upstream/orca-main`
    (= main + src-orca bump), then dispatches android-apk.yml there. Releases come only from
    main.
  - `android/scripts/bump_upstream.py` updates the UPSTREAM.md table and lists the
    port-dependent files that changed.
  - The deps cache key now hashes `src-orca` `deps/` + `cmake/modules` trees instead of the
    commit.
  - `534db60` moves src-orca from `2769b12` to `f8dd5605` (172 commits; OCCT recipe changed, so
    the deps rebuild once).
  - Test build: run 37435400715, dispatched 08:20Z; check-in scheduled for 10:01Z. The user
    wants builds only for changes that might break.
  - The watch only becomes active once the branch is merged into main, which also publishes a
    release.

## User's Chromebook state

- **Installed:** com.orcaslicer.OrcaStudio from release **r7**, via the updater
  (`~/.local/bin/orcastudio-update.sh`, systemd user timer).
- **Data dir:** `~/.var/app/com.orcaslicer.OrcaStudio/config/BambuStudio_OrcaSlicer/`.
- **Keys:** `slicer_cert.pem` / `slicer_key.pem` / `slicer_crl.pem` are in that data dir, with a
  backup copy in `~/obn-keys/`. **Never** put them in a repo or bundle, and never explain how to
  obtain them.
- **obn.conf:** `block_cloud = 0`, `client_name = BambuStudio`, `cloud_print = try_lan_first`,
  `log_to_file = 1`, `log_level = info` (set 2026-10-05 21:42 −0600).
- **A1:** serial `03919C450802955`, LAN IP 192.168.4.30, cloud-bound, Developer Mode OFF. The
  firmware advertises the new authorization-control system (flag3 bit16).
  - The app-certificate exchange succeeds: `device certificate installed, pubkey cached`.
  - Bambu Handy works.
- **Backup:** an older copy of the data dir is at
  `~/.var/app/com.orcaslicer.OrcaStudio.bak-<date>` (from a reset). It's safe to delete once
  everything works.
- **Workaround status:** the temporary `LD_LIBRARY_PATH` flatpak override was supposed to be
  removed with `flatpak override --user --reset com.orcaslicer.OrcaStudio`. Confirm with the user.

## OrcaStudio-Android (BaIanced/OrcaStudio-Android)

- **What it adds:**
  - obn compiled with NDK r28c as a static lib inside `liborca_jni.so`
    (`android/obn/obn.cmake` and `obn-android.patch`).
  - Patch 0001 is applied too.
  - JNI bridge in `android/core/jni/ObnBridge.cpp`.
  - Kotlin: `net/ObnNative.kt`, `net/ObnHost.kt` (printer type "Bambu Lab (signed, no LAN mode)"),
    and `net/ObnCredentials.kt` (PEM import into `noBackupFilesDir/obn`).
  - App id `io.github.baianced.orcastudio_android`.
- **Releases:** `android-v0.1.2-r2` includes patch 0001 (run 37404624478, success).
  - Debug-signed. The keystore is cached in Actions.
  - Release-signing secrets are not set up yet: `ANDROID_KEYSTORE_B64`,
    `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`.
- **Untested on a real phone or printer.**
  - It prints with `start_local_print` (pure LAN), so patch 0002 is not needed there.
  - The camera is out of scope.
  - The user's phones are a OnePlus 15, a OnePlus 11 and a Note 10+, all arm64.

## Useful facts

- `gh` in Claude Code sessions is REST-only. `gh release download` (GraphQL) fails; use
  `gh api -H "Accept: application/octet-stream" repos/<r>/releases/assets/<id>`.
- Tag pushes are blocked from the session. Actions can create tags and releases.
- Run logs: `gh api repos/<r>/actions/jobs/<job_id>/logs`. Dispatch:
  `gh api -X POST repos/<r>/actions/workflows/<file>/dispatches -f ref=main`.
- obn logs per-frame MQTT only at `log_level = trace` (`mqtt_client.cpp` `s_on_message`). The
  user should share only filtered output (`grep -o 'mqtt msg topic=[^ ]* bytes=[0-9]*'`), never
  raw trace logs. They contain tokens.
