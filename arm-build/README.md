# OrcaStudio aarch64 Flatpak (with open-bamboo-networking)

Fork-only overlay. Nothing outside `arm-build/` and `.github/workflows/arm-*.yml` differs from upstream.

## What happens automatically

1. **Daily, 10:41 UTC**: `ARM upstream watch` checks for new release tags on
   [jarczakpawel/OrcaStudio](https://github.com/jarczakpawel/OrcaStudio) and
   [ClusterM/open-bamboo-networking](https://github.com/ClusterM/open-bamboo-networking).
   On a new tag it bumps `arm-build/versions.json`, tries to merge the OrcaStudio tag into this fork, and builds.
   If the merge can't be done, it's skipped with a warning. The build doesn't depend on it.
2. **`arm64 Flatpak`** builds on a native `ubuntu-24.04-arm` runner in two jobs:
   - **Dependencies:** cached and reused until `deps/` changes.
   - **App + plugin:** uses ccache.
   - **Output:** publishes release `arm64-<orcastudio>-obn-<obn>-r<N>` with `OrcaStudio-aarch64.flatpak` + `SHA256SUMS.txt`, keeping the newest 3.
3. **Chromebook**: a systemd user timer downloads new releases daily, verifies the checksum and installs them.
   It skips the install while OrcaStudio is running.

Manual build: Actions → *arm64 Flatpak* → Run workflow. Tick *clean_cache* to force a full rebuild.

## One-time Chromebook setup (Linux terminal, Debian 13, aarch64)

```sh
sudo apt install flatpak curl jq git
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
git clone --depth 1 https://github.com/BaIanced/orcastudio ~/orcastudio-arm
bash ~/orcastudio-arm/arm-build/chromebook/install-updater.sh
~/.local/bin/orcastudio-update.sh          # first install (or wait for the timer)
```

### Your slicer credentials (never in this repo or the bundle)

Copy `slicer_cert.pem`, `slicer_key.pem` and `slicer_crl.pem` into:

```
~/.var/app/com.orcaslicer.OrcaStudio/config/BambuStudio_OrcaSlicer/
```

This folder survives app updates. On first launch the launcher creates `obn.conf` there with
`block_cloud = 0` and `client_name = BambuStudio` (Option B). It never overwrites an existing `obn.conf`.
Start OrcaStudio once, close it, then start it again. The plugin is enabled from the second launch.

## Details

- `NOTES-obn.md`: how OrcaStudio loads the plugin, what the launcher does, paths.
- `NOTES-ci.md`: build design, runner limits, timing.
- `NOTES-updates.md`: tag tracking, fork sync, Chromebook updater.
