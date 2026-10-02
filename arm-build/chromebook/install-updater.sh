#!/usr/bin/env bash
# install-updater.sh - set up automatic OrcaStudio (aarch64 Flatpak) updates
# on the Chromebook's Linux container (Crostini, Debian 13). Run as your normal
# user from this directory, on the HOST side (a Terminal), not inside Flatpak:
#
#   bash install-updater.sh
#
# Installs:
#   ~/.local/bin/orcastudio-update.sh
#   ~/.config/systemd/user/orcastudio-update.service
#   ~/.config/systemd/user/orcastudio-update.timer   (enabled, daily)
# then runs one dry check (orcastudio-update.sh --check). No sudo needed.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ID="com.orcaslicer.OrcaStudio"
# OrcaStudio's data_dir name (wxApp name, see arm-build/NOTES-obn.md):
# sandbox XDG_CONFIG_HOME is ~/.var/app/<app-id>/config, same path on host.
DATA_DIR_NAME="BambuStudio_OrcaSlicer"
BIN_DIR="$HOME/.local/bin"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

say()  { printf '%s\n' "$*"; }
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[[ -f /.flatpak-info ]] && fail "this is running inside a Flatpak sandbox; run it in the Linux Terminal (host side)"
[[ "$(id -u)" -ne 0 ]] || fail "run as your normal user, not root (installs into your home directory)"
arch="$(uname -m)"
[[ "$arch" == "aarch64" ]] || fail "this Linux container is '$arch'; the published bundle is aarch64 only"

missing=()
for c in flatpak curl sha256sum flock awk systemctl; do
    command -v "$c" >/dev/null 2>&1 || missing+=("$c")
done
if ! command -v python3 >/dev/null 2>&1 && ! command -v jq >/dev/null 2>&1; then
    missing+=("jq (or python3)")
fi
if ((${#missing[@]})); then
    fail "missing: ${missing[*]}  ->  sudo apt install flatpak curl coreutils util-linux jq"
fi
command -v notify-send >/dev/null 2>&1 \
    || say "note: 'notify-send' not found; updates still work, but without desktop notifications (sudo apt install libnotify-bin)"
say "flatpak: $(flatpak --version)"

for f in orcastudio-update.sh orcastudio-update.service orcastudio-update.timer; do
    [[ -f "$HERE/$f" ]] || fail "$HERE/$f not found (run from arm-build/chromebook/)"
done
bash -n "$HERE/orcastudio-update.sh" || fail "orcastudio-update.sh has a syntax error"

mkdir -p "$BIN_DIR" "$UNIT_DIR" "${XDG_STATE_HOME:-$HOME/.local/state}"
install -m 0755 "$HERE/orcastudio-update.sh" "$BIN_DIR/orcastudio-update.sh"
install -m 0644 "$HERE/orcastudio-update.service" "$UNIT_DIR/orcastudio-update.service"
install -m 0644 "$HERE/orcastudio-update.timer" "$UNIT_DIR/orcastudio-update.timer"
say "installed $BIN_DIR/orcastudio-update.sh and units in $UNIT_DIR"

# Crostini runs a systemd user manager (garcon, sommelier are user units), so
# a user timer is the primary mechanism.
if systemctl --user show-environment >/dev/null 2>&1; then
    systemctl --user daemon-reload
    systemctl --user enable --now orcastudio-update.timer
    systemctl --user list-timers orcastudio-update.timer --no-pager || true
else
    say "WARNING: no systemd user manager reachable from this shell (systemctl --user failed)."
    say "         Fallback: run '$BIN_DIR/orcastudio-update.sh' manually, or add this line to ~/.profile:"
    # shellcheck disable=SC2016  # printed literally for the user to paste
    say '         ( "$HOME/.local/bin/orcastudio-update.sh" --quiet & ) >/dev/null 2>&1'
fi

say ""
say "First dry run (--check, changes nothing):"
"$BIN_DIR/orcastudio-update.sh" --check || say "(check failed; see ${XDG_STATE_HOME:-$HOME/.local/state}/orcastudio-update.log)"

data_dir="$HOME/.var/app/$APP_ID/config/$DATA_DIR_NAME"
say ""
say "Bambu slicer credentials (yours; never committed or bundled) go here on the HOST:"
say "  $data_dir/slicer_cert.pem"
say "  $data_dir/slicer_key.pem"
say "  $data_dir/slicer_crl.pem"
say "(same directory as obn.conf and OrcaStudio.conf; created on first app start)"
say "Suggested: chmod 600 '$data_dir'/slicer_*.pem"
say ""
say "Commands:  orcastudio-update.sh --check | --force"
say "Log:       ${XDG_STATE_HOME:-$HOME/.local/state}/orcastudio-update.log"
say "Timer:     systemctl --user list-timers orcastudio-update.timer"
say "Remove:    systemctl --user disable --now orcastudio-update.timer; rm ~/.local/bin/orcastudio-update.sh $UNIT_DIR/orcastudio-update.{service,timer}"
