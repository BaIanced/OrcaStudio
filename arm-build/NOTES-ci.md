# ARM64 Flatpak CI: design notes (Agent B)

Files:
- `.github/workflows/arm-flatpak.yml`: the workflow.
- `arm-build/make-manifest.py`: generates `scripts/flatpak/com.orcaslicer.OrcaStudio.arm.yml`. That file is generated and is not committed (suggest adding `scripts/flatpak/*.arm.yml` to `.gitignore`).

All facts below were checked on 2026-10-02. Each one links to its source. Items that could not be verified are marked **I need to verify**.

## 1. Platform facts and limits

| Fact | Value | Source |
|---|---|---|
| `ubuntu-24.04-arm`, public repo | 4 vCPU, 16 GB RAM, 14 GB SSD (spec) | https://docs.github.com/en/actions/reference/runners/github-hosted-runners |
| Job execution time (GitHub-hosted) | 6 h per job, then terminated | https://docs.github.com/en/actions/reference/limits |
| Workflow run time | 35 days (includes waiting) | same |
| Job queue time | 24 h | same |
| Cache storage | 10 GB per repo; entries not accessed in 7 days are removed; over the limit, eviction runs by last access (oldest first); entries are immutable; key ≤ 512 chars; runs can restore caches from the current branch or the default branch | https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching |
| Cache entry size in `actions/cache` v6 code | `CacheFileSizeLimit = 10 GiB` | actions/cache `dist/save/index.js` |
| Artifact storage | Free plan: 500 MB. Public-repo usage is free for standard runners; storage for public repos is not explicitly itemised (**I need to verify** whether artifacts in a public repo count toward the 500 MB). Mitigation: one ~200–300 MB artifact with `retention-days: 3`. | https://docs.github.com/en/actions/reference/limits, https://docs.github.com/en/billing/concepts/product-billing/github-actions |
| GITHUB_TOKEN | Events it creates do not start new runs, except `workflow_dispatch` and `repository_dispatch` | https://docs.github.com/en/actions/concepts/security/github_token |
| Reusable workflows | The caller's token permissions can only be downgraded. The `github` context (`run_number`, `sha`) is the **caller's** | https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations |
| Concurrency | By default a newly queued run replaces the pending one in the same group | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax |
| Actual free disk on arm64 runner | Third-party measurement (2025-11-18): `/dev/root 72G, 46G avail`. After cleanup: 55G. **I need to verify** on our own run; the workflow logs `df -h` | https://www.geraldonit.com/mastering-disk-space-on-github-actions-runners-a-deep-dive-into-cleanup-strategies-for-x64-and-arm64-runners/ |

Software on the image ([arm-ubuntu-24-image.md](https://github.com/actions/partner-runner-images/blob/main/images/arm-ubuntu-24-image.md) and [Ubuntu2404-Readme.md](https://github.com/actions/partner-runner-images/blob/main/images/Ubuntu2404-Readme.md), repo HEAD d14c9de, 2026-05-13):
- flatpak and flatpak-builder are **not** preinstalled.
- Preinstalled: Python 3.12.3, gh 2.86.0, jq, shellcheck 0.9.0, zstd, `file`.
- PyYAML is not listed, so the workflow `apt-get install`s `flatpak flatpak-builder python3-yaml`.
- Ubuntu 24.04 (noble) gives flatpak 1.14.6 and flatpak-builder 1.4.2. These are the same versions as this workspace, where `flatpak-builder --show-manifest` and Agent A's local builds ran. **I need to verify** that the apt candidate on the runner is still 1.4.2. The cache key embeds the flatpak-builder version, so a change only costs one deps rebuild.

Flathub, aarch64 (`flatpak remote-info` / `remote-ls --arch=aarch64`, read-only):

| Runtime | Download | Installed |
|---|---|---|
| `org.gnome.Sdk/aarch64/50` (commit 01d05eb7…, 2026-09-23) | 808.7 MB | 2.4 GB |
| `org.gnome.Platform/aarch64/50` | 409.3 MB | — |
| `org.freedesktop.Sdk.Extension.llvm21/aarch64/25.08` | 122.3 MB | — |

## 2. Approach: native apt flatpak-builder, not the Flathub container action

Candidates:
- **`flatpak/flatpak-github-actions/flatpak-builder@v6`** (latest v6.8). It takes an `arch` input. Its README documents arm64 builds on `ubuntu-24.04-arm` inside `ghcr.io/flathub-infra/flatpak-github-actions:<runtime>` with `options: --privileged`. The `gnome-50` tag is an OCI index with linux/amd64 and **linux/arm64** (arm64 layers 1934 MB compressed). The image contains `org.gnome.Platform//50` + `org.gnome.Sdk//50` only, so llvm21 is still downloaded per job.
  - Its cache: one `actions/cache` entry. The default key is derived from the manifest path. The cache is saved only after a successful build, and only when the key differs from the restored one. It always passes `--ccache`, but there is no `--jobs` input.
- **Native** (chosen): `apt-get install flatpak flatpak-builder`, then `flatpak-builder --user --install-deps-from=flathub`.

Why native:
1. We need two jobs with an exact-key handoff (`--stop-at=OrcaStudio`), plus a partial-state save when a step fails or times out. The action's single build step does not allow this.
2. We need explicit `--jobs`.
3. Disk: native downloads 1.34 GB of runtimes. The container adds a ~1.9 GB compressed / multi-GB extracted image on top of that, and still installs llvm21.
4. No `--privileged` container is needed.

Costs of the native approach:
- flatpak-builder 1.4.2 is older than upstream 1.4.12.
- bwrap needs unprivileged user namespaces. The workflow sets `kernel.apparmor_restrict_unprivileged_userns=0` if that sysctl exists, then runs a `bwrap … true` probe so a failure shows up early and clearly. **I need to verify** whether the arm64 image enables that AppArmor restriction; the step is harmless either way.

## 3. Job design

```
deps  (ubuntu-24.04-arm, timeout 350 min, build step 300 min)
  checkout fork@ci_ref -> ci/ ; validate versions.json ; git ls-remote: tags still point at pinned commits
  release tag = arm64-<os_tag>-obn-<obn_tag>-r<run_number>   (fails if the tag already exists on attempt 1)
  checkout <orcastudio.repo>@<orcastudio.commit> -> src/ ; cp -a ci/arm-build src/arm-build
  make-manifest.py --jobs 4 --no-debug-info --ccache-launcher ; --print-deps-key
  key = fb-deps-aarch64-fb<flatpak-builder version>-<sha256>   (+ -clean-<run_id> when clean_cache)
  restore .fb-state/{cache,downloads,git} (exact key, else newest with the prefix fb-deps-aarch64-fb<ver>-)
  exact hit  -> done (no runtime install, no build)
  otherwise  -> free disk, swap, flathub remote, flatpak-builder --stop-at=OrcaStudio, save cache
              failure/timeout -> save <key>-partial-<run_id>-<attempt>; a re-run resumes from it
app   (ubuntu-24.04-arm, timeout 350 min, build step 300 min)
  same checkouts at the deps job's resolved ci_sha + regenerate. Asserts that the deps hash and the
  flatpak-builder version equal the deps job's.
  restore deps state by EXACT key (fail-on-cache-miss + cache-hit=='true' check)
  restore ccache (prefix ccache-aarch64-) ; ccache.conf: max_size 2G, PCH sloppiness
  flatpak-builder --ccache --repo=repo (deps stages are cache hits)
  save ccache (also on failure) ; build-bundle --runtime-repo=https://flathub.org/repo/flathub.flatpakrepo
  smoke check: install bundle on runner; check:
    - BUILD_INFO == expected
    - metadata command
    - launcher + entrypoint present
    - exported desktop Exec uses --command=orcastudio-arm-launcher
    - orca-studio is ARM aarch64
    - no slicer_cert/key/crl files
  sha256sum -> SHA256SUMS.txt ; upload-artifact (retention 3 days, no recompression)
release (ubuntu-24.04, contents: write)
  verify sha256 ; gh release create <tag> --target <ci_sha> --latest (re-run attempt: upload --clobber)
  delete all but the newest 3 arm64-* releases (gh release delete --cleanup-tag)
prune-caches (ubuntu-24.04, actions: write)
  delete fb-deps-aarch64-* except the key in use, and ccache-aarch64-* except this run's
```

Cache reuse is safe because of how flatpak-builder 1.4.2 computes checksums:
- Stage checksums do not include the SDK commit unless `--rebuild-on-sdk-change` is passed (`src/builder-manifest.c`, `builder_manifest_checksum`).
- `--ccache` and `--jobs` are not part of module checksums (`builder_module_checksum`, `builder_options_checksum`).

So the deps job (no `--ccache`) and the app job (`--ccache`) share cached stages. A Flathub SDK point update between runs does not invalidate the deps cache; Flathub's own builder behaves the same way by default.

The cache repo is ostree `BARE_USER_ONLY` (`builder-cache.c`), so it does not depend on xattrs and survives `actions/cache`'s `tar --posix`.

`--print-deps-key` hashes:
- the top-level fields that feed `builder_manifest_checksum`;
- every module before `OrcaStudio`, including the parallelism and `-g0` changes;
- the bytes of local `path:` sources (`../../deps`).

Changes to the app source, the obn module, or the release tag leave the key unchanged; a change under `deps/` changes it. Both cases were tested.

## 4. make-manifest.py

YAML handling uses PyYAML (apt `python3-yaml`) with a loader and dumper whose implicit typing matches flatpak-builder's `parse_yaml_node_to_json` (`src/builder-utils.c`):
- Booleans: only `true`/`True`/`TRUE`/`false`/`False`/`FALSE`.
- Null: `null`/`Null`/`NULL`.
- Integers: base-10 only.
- Everything else is a string.
- Duplicate keys and merge keys are rejected.

I chose this over text patching for robustness, and over stock `safe_load` because YAML 1.1 would turn `on` into a boolean and `0755` into octal. Tested: `x: on`, `x: 0755` and `x: 3.10` parse identically with flatpak-builder before and after generation.

Always applied:
- **a) FFmpeg source.** The URL and SHA256 are parsed from `deps/FFMPEG/FFMPEG.cmake`, so they track upstream bumps. The source is inserted after the `dest: external-packages/python3` entry. If upstream already carries the same entry, nothing is added. If it carries a different FFmpeg entry, the script stops with an error.
- **b) obn modules.** `arm-build/obn-module.yml` is appended after `OrcaStudio`, with `@OBN_TAG@` and `@OBN_COMMIT@` substituted.
- **c) Launcher.** Sets `command: orcastudio-arm-launcher`.
- **d) Integration module.** A final module, `orcastudio-arm-integration`, does the following:
  - fails if `/app/bin/orcastudio-arm-launcher` or `/app/bin/entrypoint` is missing;
  - runs `desktop-file-edit` to set `Exec=orcastudio-arm-launcher %U`, then checks the result with grep;
  - writes `/app/share/orcastudio-arm/BUILD_INFO` (`orcastudio_tag=`, `obn_tag=`, `release_tag=`, one per line, newline-terminated).
  - The release tag comes from `--release-tag` or `$RELEASE_TAG`; it is required unless `--check`/`--print-deps-key` is given.
  - Tested in bwrap against the GNOME 50 SDK (x86_64, read-only, with a fake `/app`). It passes, and it fails with a clear message when the launcher is absent.
- **e) Anchor checks.** Every anchor fails loudly (exit 2) if it is missing or ambiguous: app-id, `command: entrypoint`, a single `OrcaStudio` module that is the last module, a single `orca_deps` before it, the python3 source, the `desktop-file-edit … entrypoint %U` post-install, the deps build command (with `--jobs`), the placeholders, a module mentioning the launcher, and name collisions.

CI-only flags. These do not change what the app does:
- **`--jobs 4`.** Upstream's `cmake --build $BUILD_DIR --parallel` runs as unbounded `make -j`. I confirmed this on CMake 3.28 with a fake make program, and in CMake master's `cmGlobalUnixMakefileGenerator3.cxx` (`DEFAULT_BUILD_PARALLEL_LEVEL` → `-j`). Each dependency then runs its own `-j$NPROC`, and FFmpeg/GMP/MPFR use plain `make -j`. This is the likely cause of the earlier local OOM. The flag changes three things:
  - top level: `--parallel 2`;
  - `CMAKE_BUILD_PARALLEL_LEVEL=4` (honoured by `deps/CMakeLists.txt` `_build_j` and by `FFMPEG.cmake`);
  - `MAKEFLAGS=-l6` (GNU make ≥ 4.4 uses `/proc/loadavg` running jobs; the SDK has GNU Make 4.4.1, cmake 4.4.3 and ccache 4.14, checked in the x86_64 GNOME 50 SDK).
- **`--no-debug-info`.** Appends `-g0` to top-level cflags/cxxflags (the SDK default flags contain `-g`, per `etc/flatpak-builder/defaults.json`), and sets `no-debuginfo: true` and `strip: true`. Upstream's own `build_flatpak.sh` defaults to `no-debuginfo` + `strip`. This saves RAM, disk and link time, and drops the `.Debug` extension, which is not shipped.
- **`--ccache-launcher`.** Sets `CMAKE_{C,CXX}_COMPILER_LAUNCHER=ccache` on the OrcaStudio module, because flatpak-builder's `--ccache` only symlinks cc/c++/gcc/g++ and the manifest uses `CC=clang`. It also adds `-Xclang -fno-pch-timestamp`, because CMake's clang PCH flags omit it and ccache needs it for PCH users (libslic3r and libslic3r_gui use `target_precompile_headers` with clang).

Verification:
- `flatpak-builder --show-manifest` parses both outputs.
- A JSON diff of upstream against generated (both via `--show-manifest`) shows only the intended changes (listed above), and no warnings.
- The YAML round-trip check is built into the script.
- `--check` mode validates without writing.
- Failure-mode tests: FFmpeg already present or mismatched, python3 anchor missing, command changed, module renamed, deps command changed, post-install changed, placeholder missing, launcher not mentioned, bad release tag.

## 5. Timing estimate (4 vCPU, estimates; **I need to verify** with the first real run)

Assumption: one Neoverse-class arm64 vCPU is roughly one x86 runner vCPU for clang compiles. **I need to verify** this for the estimate.

**Deps job**, core-minutes per item:

| Item | Core-min |
|---|---|
| wxWidgets 3.3 | 40 |
| gst/glu/ECM/libspnav | 4 |
| Boost 1.84 | 20 |
| OCCT 7.6 | 110 |
| OpenCV 4.6 | 35 |
| OpenVDB + OpenEXR + Blosc | 35 |
| TBB | 5 |
| CPython 3.12 `--enable-optimizations` (PGO) | 25 |
| FFmpeg 7.0.2 | 15 |
| OpenSSL 1.1.1w + curl | 12 |
| misc (GMP, MPFR, NLopt, Qhull, Draco, GLFW, OpenCSG, libnoise, FreeType…) | 20 |

```
total  = 40+4+20+110+35+35+5+25+15+12+20 = 321 core-min
wall   = 321 / (4 × 0.70 efficiency)     = 114.6 min
+ serial PGO training                     = +10   -> 124.6 min
+ apt/runtime install 6, downloads 3, cache save 5, checkout 2 = +16 -> 140.6 min
margin vs 350-min job timeout: 350 / 140.6 = 2.49×
```

**App job**:

```
src+deps_src C/C++ files: 1419 (libslic3r 214, slic3r 424, rest 781)
core-min = 214×0.35 + 424×0.45 + 781×0.08 = 74.9 + 190.8 + 62.5 = 328.2
wall     = 328.2 / (4 × 0.85) = 96.5 min
+ link 3 + gettext/install 3 + finish/export/appstream 5
+ overhead 23 (runtimes 6, cache restore 4, checkout 2, bundle 3, smoke 2, ccache save 3, misc 3)
total    = 96.5 + 3 + 3 + 5 + 23 = 130.5 min; margin 350 / 130.5 = 2.68×
full ccache hit (obn-only bump, OrcaStudio unchanged): 96.5×0.1 + 34 = 43.7 min
```

On a deps cache hit (the usual upstream bump), the deps job takes about 3 minutes.

If the deps estimate is badly wrong, for example orca_deps alone runs longer than 300 minutes, there is a fallback: add a third job with `--stop-at=orca_deps` before the current deps job. wxWidgets and the small modules would then be cached separately.

**RAM** (estimates; **I need to verify** the peak RSS of the heaviest TUs on clang 21/aarch64):
- App: 4 jobs × ≤ 2.5 GB = 10 GB < 16 GB.
- Deps: ≤ 2 dependencies in parallel × 4 jobs, capped by `-l6`, each TU ≤ 1.5 GB, so ≤ 12 GB.
- An 8 GB swapfile is added when no swap exists and more than 40 GB is free.

**Disk** (app job peak, estimate):
```
runtimes 4.1 + deps cache repo 3 + downloads/git 0.8 + orca_deps checkout in build 5 + app build dir 4
+ app dir 1 + exported repo 0.6 + bundle 0.2 + ccache 2 = 20.7 GB
```
This is above the 14 GB spec but well under the measured ~46 GB free. Cleanup removes dotnet, swift and powershell (≈ 8 GB on arm64 per the source above).

**Cache budget**: a deps entry of about 1.5–3 GB compressed plus ccache of 2 GB or less. During a run where the deps change, up to about 2×(deps + ccache) ≈ 9 GB can exist briefly, close to the 10 GB limit. LRU eviction and the prune job keep it in bounds. **I need to verify** the real compressed size of the deps cache entry from the first run.

## 6. Interface notes for other agents and the lead

- **Release tag:** `arm64-<orcastudio_tag>-obn-<obn_tag>-r<run_number>`. When the workflow is called through `workflow_call`, `run_number` is the **caller's**. A tag that already exists on attempt 1 fails the run; it is never overwritten. A re-run attempt replaces that release's assets.
- **Assets:** `OrcaStudio-aarch64.flatpak` and `SHA256SUMS.txt` (`<sha256>  OrcaStudio-aarch64.flatpak`). The release is marked latest, and only the newest 3 `arm64-*` releases are kept.
- **Bundle:** ref `app/com.orcaslicer.OrcaStudio/aarch64/master`. The branch is `master`, matching upstream `build_flatpak.sh`, which uses the flatpak-builder default. It has a runtime-repo pointing at Flathub.
- **BUILD_INFO:** `/app/share/orcastudio-arm/BUILD_INFO` inside the sandbox. On the host after a `--user` install it is at `~/.local/share/flatpak/app/com.orcaslicer.OrcaStudio/current/active/files/share/orcastudio-arm/BUILD_INFO`.
- **Selecting releases:** the upstream workflows that live in this fork (`my_build_all.yml`) can also publish releases. The Chromebook updater should select `arm64-*` tags and not rely only on "latest".
- **Calling the workflow (watcher):**
  - Pass `ci_ref`, the commit or branch containing the bumped `versions.json`, because `github.sha` is the caller's pre-bump commit.
  - Grant `permissions: contents: write, actions: write` on the calling job.
  - If the caller defines `concurrency`, use a group name other than `orcastudio-arm64-flatpak`.
  - Alternatively dispatch it: `gh workflow run arm-flatpak.yml -f ci_ref=<sha>`. A dispatch made with GITHUB_TOKEN does start a run.
- **`obn-module.yml` contract** (checked by the script):
  - It is a single module mapping, a list of modules, or `{modules: [...]}`.
  - It contains the literal `@OBN_TAG@` and `@OBN_COMMIT@`; no other `@UPPER@` tokens may remain after substitution.
  - Module names must not collide with upstream names or with `orcastudio-arm-integration`.
  - Some module must install an executable `/app/bin/orcastudio-arm-launcher`; this is checked at build time.
  - Relative `path:` entries are relative to `scripts/flatpak/`, so the launcher is `../../arm-build/orcastudio-arm-launcher`.
  - The modules run after `OrcaStudio`, so `/app/bin/entrypoint` exists, and before the integration module.
  - Do not edit the desktop file there; the integration module does that.
  - These modules are not part of the deps cache key: an obn bump never rebuilds the deps.

## 7. Open items (**I need to verify**)

- The real build times, peak RAM and disk on `ubuntu-24.04-arm`. All numbers in section 5 are estimates.
- Whether the arm64 image restricts unprivileged user namespaces (mitigated with the sysctl).
- Whether apt's flatpak-builder 1.4.2 runs finish and `appstreamcli compose` for GNOME 50 on aarch64 without issues. Agent A's local x86_64 1.4.2 run is the nearest evidence.
- The ccache hit rate for PCH translation units with `-Xclang -fno-pch-timestamp` and the sloppiness settings. The `ccache statistics` step prints it.
- The SDK aarch64 `defaults.json` flags. Only the x86_64 file was inspected; `-g` is assumed to be present and is neutralised by `-g0` either way.
- Whether workflow-level `concurrency` in a called workflow is honoured under `workflow_call`. The docs do not say, hence the caller-side recommendation in section 6.
- Whether artifact storage in a public repo counts toward the 500 MB quota.
