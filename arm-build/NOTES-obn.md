# obn (open-bamboo-networking) inside the OrcaStudio aarch64 Flatpak

Files: `arm-build/obn-module.yml` (flatpak-builder module), `arm-build/orcastudio-arm-launcher`
(app command, runs inside the sandbox). Source references below are OrcaStudio `v02.08.01.55-p6`
(bef044f) and obn `v2.2.0` (5e6a359).

## 1. How OrcaStudio loads the network plugin on Linux

| Step | Where |
| --- | --- |
| `data_dir` = `$XDG_CONFIG_HOME/BambuStudio_OrcaSlicer` (`~/.config` fallback); `--datadir` overrides | `GUI_App.cpp:2816` (`SetAppName("BambuStudio_OrcaSlicer")`), `:2856`; `OrcaSlicer.cpp:7309` |
| App conf = `<data_dir>/OrcaStudio.conf` (JSON + trailing `# MD5 checksum`; Linux load is `ifs >> j`, no checksum check) | `AppConfig.cpp:1733-1737`, `:688`; `version.inc:5` (`SLIC3R_APP_KEY "OrcaStudio"`) |
| Plugin loaded only if `app.installed_networking` is true | `GUI_App.cpp:4256` |
| That flag also adds the `bbl` cloud provider | `NetworkAgentFactory.cpp:202` |
| Configured version collapsed to its 8-char series; numbered same-series files renamed onto `libbambu_networking_<series>.so`, older ones deleted | `GUI_App.cpp:2022-2066` (`migrate_network_plugin_config`), `bambu_networking.hpp:440,450` |
| Only series `02.08.01` (+ legacy `01.10.01.01`) accepted | `bambu_networking.hpp:10,380` |
| `dlopen(<data_dir>/plugins/libbambu_networking_<version>.so)`, fallback `libbambu_networking.so` | `BBLNetworkPlugin.cpp:476-492`, `:839` (`resolve_library_path`) |
| Must export `ft_abi_version` (>=1) + `ft_*` or load fails | `BBLNetworkPlugin.cpp:517`, `FileTransferUtils.cpp:8-39` |
| Compatible if first 8 chars of `bambu_network_get_version()` == configured series | `GUI_App.cpp:2321-2356` |
| `dlopen(<data_dir>/plugins/libBambuSource.so)` required, else "update needed" | `BBLNetworkPlugin.cpp:775`, `GUI_App.cpp:4362` |
| `create_agent(data_dir)` then `set_config_dir(data_dir)`, so obn reads `<data_dir>/obn.conf` and `<data_dir>/slicer_*.pem` | `GUI_App.cpp:4434`, obn `src/agent.cpp:1842` |
| `scan_plugin_versions` uses `is_regular_file(entry.status())`, which follows symlinks, so symlinks count | `BBLNetworkPlugin.cpp:910-937` |

**No hash or signature check on native Linux.** The ELF, manifest and sha256 validation in
`SlicerLinuxRuntimeConfig.cpp` only runs when `SlicerLinuxRuntime::enabled()` is true. That is
always the case on Windows and macOS. On Linux it is true only if the env var
`SLICER_LINUX_RUNTIME_ENABLED` is set (`SlicerLinuxRuntimeConfig.cpp:103-115`). That runtime is a
WSL/Lima bridge for non-Linux hosts. It does not get in the way here, as long as that env var is
not set. Its ELF check also accepts only x86_64 (`:41`).

**Stock-plugin download/overwrite paths:**
- `PresetUpdater::sync_plugins` downloads into `<data_dir>/ota/plugins` only when the online
  version is newer than the loaded one (`PresetUpdater.cpp:871`, `:620`). `.99` is never older
  than a stock build of the same series.
- A cached download with `force` sets `update_network_plugin=true`. On the next start,
  `install_network_plugin_from_ota` copies it to `plugins/libbambu_networking_<ver>.so` and sets
  `network_plugin_version` (`PresetUpdater.cpp:980`, `GUI_App.cpp:3525,4027-4235`).
- The user can also click "download plug-in" in the UI.
- Any of these drops a numbered stock file that `migrate_network_plugin_config` would rename over
  ours. The launcher undoes all of them on every start (see section 3).

## 2. ABI match (obn v2.2.0 vs OrcaStudio 02.08.01.55)
- obn ships `tools/abi_snapshot/v02.08.01` taken from Bambu Studio `v02.08.01.55`, the same
  number as OrcaStudio's `SLIC3R_VERSION`.
- The by-value structs and enums are identical after whitespace and comment normalisation. Checked:
  PrintParams, TaskQueryParams, FilamentQueryParams, FilamentDeleteParams, AmsSyncItem,
  AmsSyncParams, PublishParams, CertificateInformation, detectResult, the stage/status enums and
  MessageFlag.
- Every `bambu_network_*` symbol OrcaStudio dlsyms is exported, except
  `bambu_network_get_last_error_msg`. OrcaStudio only uses that one on the runtime-bridge path.
- obn's installer pins Orca to `02.03.00` (`packaging/install.sh:178`). That is right for
  upstream OrcaSlicer but would be **rejected** by OrcaStudio (`is_supported_network_version`).
  The module therefore builds `OBN_VERSION=<OrcaStudio series>.99`. The series is read at build
  time from OrcaStudio's own `bambu_networking.hpp`, the same `.99` rule as `install.sh:217`.
  The build fails if obn has no snapshot for that series.

## 3. What the launcher does (`/app/bin/orcastudio-arm-launcher`, POSIX sh, shellcheck-clean)

It mirrors obn `packaging/install.sh` (Orca branch, lines 178-375), with these differences:

| install.sh | launcher | why |
| --- | --- | --- |
| copies `libbambu_networking_<ver>.99.so` | symlink `plugins/libbambu_networking_<series>.so` -> `/app/lib/obn/libbambu_networking.so` | OrcaStudio renames `.99` onto the series name every start (`GUI_App.cpp:2022`). A symlink into `/app` follows app updates. dlopen, `exists` and `is_regular_file(status)` all follow symlinks. Verified. |
| copies `libBambuSource.so` | symlink | same reason |
| `liblive555.so` stub unless the existing file is >64 KiB (`:279`) | same rule, symlink | |
| `network_plugin_version = <ver>.99` | `= <series>` (`02.08.01`) | This is what OrcaStudio itself stores. It makes `migrate_network_plugin_config` a no-op and avoids rewriting the conf on every launch. |
| sets `installed_networking`/`network_plugin_remind_later` = `"true"`, strips the version from `network_plugin_skipped_versions`, backup `.obn-bak`, zero MD5 line (`:344-375`) | same, and strips both `<series>` and `<series>.99` | It treats an existing JSON `true` as already set, so it does not rewrite the conf on every start. The write is atomic (tmp + `os.replace`). |
| no conf: abort | no conf: skip with one stderr line | On first launch OrcaStudio has not written `OrcaStudio.conf` yet. The plugin is active from the second launch. |
| not done | moves numbered same-series files (`libbambu_networking_02.08.01.NN.so`, stock downloads) to `plugins/obn-displaced/` and removes `ota/plugins` | stops the stock plugin replacing obn (section 1) |

`obn.conf` is seeded only if absent, from `/app/share/obn/obn.conf.default`. That file is obn's
`packaging/obn.conf.in`, byte-for-byte, except `block_cloud = 0` and `client_name = BambuStudio`.
Checked with `diff`: only lines 142 and 170 differ. obn never overwrites an existing `obn.conf`
(`src/config.cpp:189-190`).

`slicer_*.pem` files are never read, written or copied. If `slicer_key.pem` is missing, or the path
`slicer_key_pem` sets in obn.conf is missing, the launcher prints one stderr line naming the folder.
It then always runs `exec /app/bin/entrypoint "$@"`.

## 4. Host paths on the Chromebook (Crostini, `flatpak --user`)
- data_dir (host path = sandbox path; Flatpak keeps `$HOME`):
  `~/.var/app/com.orcaslicer.OrcaStudio/config/BambuStudio_OrcaSlicer/`
- Put `slicer_cert.pem`, `slicer_key.pem` and `slicer_crl.pem` in that directory, next to
  `obn.conf` and `OrcaStudio.conf`.
- Logs: run `flatpak run com.orcaslicer.OrcaStudio` from a terminal. Launcher lines start with
  `orcastudio-arm-launcher:` and obn lines with `[obn]`. Setting `log_to_file = 1` in obn.conf
  writes `<data_dir>/obn.log`.

## 5. Build module (`obn-module.yml`)
- **Toolchain:** inherits the manifest's clang/lld (llvm21), the same compiler and libstdc++ as
  orca-studio. std::string, std::function and std::map cross the ABI by value, so they must match.
  obn forces `_GLIBCXX_USE_CXX11_ABI=1`.
- **Deps from org.gnome.Sdk//50 (verified):** cmake 4.4, ninja, pkgconf 2.5.1, git, libcurl
  8.21.0, OpenSSL 3.5.8, zlib 1.3.1.
- **Runtime libraries:** all of these are in org.gnome.Platform//50 (verified): `libssl.so.3`,
  `libcrypto.so.3`, `libcurl.so.4`, `libz.so.1`, `libstdc++`.
- **uthash:** `uthash-dev` is not in the SDK and is not needed. mosquitto ships
  `deps/uthash.h` and `deps/utlist.h`, and obn adds that include dir.
- **vcpkg.json:** Windows-only, not used.
- **Offline build:** FetchContent deps are pre-fetched as pinned git sources and passed to CMake
  with `FETCHCONTENT_FULLY_DISCONNECTED` and `FETCHCONTENT_SOURCE_DIR_*`:
  eclipse/mosquitto v2.1.2 (`99fa50f3…`, annotated tag, peeled commit) and DaveGamble/cJSON v1.7.18
  (`acc76239…`). The build fails if a new obn tag changes `OBN_MOSQUITTO_GIT_TAG` or
  `OBN_CJSON_GIT_TAG`.
- **Isolation from /app:** in the real manifest this module comes after `orca_deps`. That step
  installs static OpenSSL 1.1.1w and curl 7.75, with headers, into `/app`, because
  `deps/CMakeLists.txt:323` rejects the SDK's OpenSSL 3.5. The Flatpak build env also sets
  `C_INCLUDE_PATH`/`CPLUS_INCLUDE_PATH=/app/include`, `-L/app/lib` and `/app/lib/pkgconfig`.
  The module unsets or strips all of these, passes `CMAKE_IGNORE_PREFIX_PATH=/app`, and fails if
  CMakeCache or any `.d` depfile points into `/app`.
- **Build-time checks:** obn's own `probe_plugin` dlopens the plugin, checks every symbol and
  round-trips create/destroy_agent. A second check compares `nm -D` against the symbols that
  OrcaStudio's `BBLNetworkPlugin.cpp` and `FileTransferUtils.cpp` resolve, and fails on any
  unexpected gap.
- **Source paths:** `../../src/...` and `../../arm-build/orcastudio-arm-launcher`, relative to
  the generated manifest in `scripts/flatpak/`.

## 6. Verified on this x86_64 box (flatpak-builder 1.4.2, org.gnome.Sdk//50, llvm21//25.08)

**Standalone test manifest:** decoy `/app` OpenSSL/curl headers and `.pc` files that `#error` if
used, then this module with v2.2.0/5e6a359 substituted, then a fake `/app/bin/entrypoint`. It
built with EXIT=0, twice (the second build used the final launcher).
- **Plugin version and dependencies:** ABI `0x020801`, plugin version `02.08.01.99`. OpenSSL
  3.5.8 and libcurl 8.21.0 came from `/usr`. The decoys were never included.
- **NEEDED:** libssl.so.3, libcrypto.so.3, libz.so.1, libcurl.so.4, libstdc++, libgcc_s, libc,
  libm. No RPATH.
- **Exports:** no OpenSSL or curl symbols are exported. `nm -D` shows 222 defined symbols,
  including `ft_abi_version` and the `Bambu_*` set in libBambuSource.so.
- **probe_plugin:** `version: 02.08.01.99`, `ft_abi_version: 1`,
  `OK (all 108 + 21 symbols present)`.

**Installed files:** `/app/lib/obn/{libbambu_networking,libBambuSource,liblive555}.so`,
`/app/bin/orcastudio-arm-launcher`, `/app/share/obn/{VERSION=v2.2.0, COMMIT,
PLUGIN_VERSION=02.08.01.99, obn.conf.default}`, and the license file.

**Launcher tests** (`flatpak build` with a fake HOME, plus a real `flatpak run` after installing
the test app; the real run showed `XDG_CONFIG_HOME=/root/.var/app/com.orcaslicer.OrcaStudio/config`
and `/usr/bin/python3` 3.13 present in the Platform):
- **Fresh start:** creates the 3 symlinks, the stamp and `obn.conf`, then execs the entrypoint
  with the arguments intact (including one with spaces).
- **Existing install:** stock `02.08.01.55` and series files displaced, the `_custom` build kept,
  a 70 KB `liblive555.so` kept, `ota/plugins` removed. The conf was patched and the skipped list
  stripped. The pem files and an existing obn.conf were unchanged (sha256 identical).
- **Re-run, including after the app saves booleans:** the conf is not rewritten (mtime unchanged).
- **`--datadir DIR` and `--datadir=DIR`:** both honoured.

**Loader emulation:** a C++ test inside the sandbox mimics BBLNetworkPlugin. Through the symlinks
it showed: scan found `02.08.01`, dlopen worked, `get_version` gave `02.08.01.99` and was
compatible with series `02.08.01`, BambuSource loaded, and `create_agent` + `set_config_dir`
returned 0. obn left the existing `obn.conf` untouched.

## 7. I need to verify
- I need to verify **the obn build on aarch64 with clang 21** for **the CI build**. obn's own CI
  builds aarch64 with gcc on ubuntu-24.04-arm. The `probe_plugin` and symbol checks in the module
  will run natively on the arm runner.
- I need to verify **that `/app/bin/orca-studio` does not export OpenSSL or curl symbols in its
  dynamic symbol table** for **safely loading obn (system OpenSSL 3.5) into a process that
  statically links OpenSSL 1.1.1w / curl 7.75**. Exported symbols could interpose. Suggested CI
  check after the build:
  `flatpak build <dir> sh -c "nm -D --defined-only /app/bin/orca-studio | grep -cE ' (SSL|EVP|CRYPTO|OPENSSL|curl)_'"`
  should print `0`. Also `ls /app/lib` should contain no `libssl.so*`, `libcrypto.so*` or
  `libcurl.so*`.
- I need to verify **a real OrcaStudio start on the Chromebook** for **end-to-end loading**. A full
  OrcaStudio build was not run here. Look for log lines `BBLNetworkPlugin::initialize: ...
  library=.../libbambu_networking_02.08.01.so, version=02.08.01.99` and
  `check_networking_version: network_ver=02.08.01.99, expected=02.08.01`.
- I need to verify **the first-run wizard's network-plugin page** for **whether it offers a stock
  download before the conf exists**. The launcher displaces any such download on the next start.
- I need to verify **camera / liveview (`gstbambusrc` + `libBambuSource.so`) on aarch64 Crostini**
  for **video**. That needs a printer and Crostini GPU/GStreamer, and was not testable here.
- I need to verify **that the `SLICER_LINUX_RUNTIME_ENABLED` env var is unset on the user's
  host** for **the native load path**. Flatpak passes most host env vars through, and setting it
  would switch OrcaStudio to the runtime bridge. The launcher does not touch it.
