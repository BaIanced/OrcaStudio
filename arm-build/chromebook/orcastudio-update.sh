#!/usr/bin/env bash
# orcastudio-update.sh - install the newest aarch64 OrcaStudio Flatpak bundle
# published by BaIanced/orcastudio GitHub releases.
#
# Runs on the HOST side of the Crostini container (Debian 13 "trixie", aarch64),
# never inside the Flatpak sandbox. Installs into the per-user installation
# (~/.local/share/flatpak). App data in ~/.var/app/com.orcaslicer.OrcaStudio/
# (slicer_*.pem, obn.conf, profiles) is never touched by this script.
#
# Usage: orcastudio-update.sh [--check] [--force] [--quiet]
#   --check  dry run: report installed vs latest release, change nothing
#   --force  reinstall even if the installed release tag equals the latest
#   --quiet  log to the log file only (stderr stays silent unless error)
#
# Exit: 0 ok (updated, up to date, or skipped because app is running)
#       1 error   2 usage   75 temporary failure (network / rate limit)
#
# Log: ${XDG_STATE_HOME:-~/.local/state}/orcastudio-update.log

set -euo pipefail
shopt -s inherit_errexit 2>/dev/null || true

# ---------------------------------------------------------------- config --
REPO="${ORCASTUDIO_UPDATE_REPO:-BaIanced/orcastudio}"
APP_ID="com.orcaslicer.OrcaStudio"
BUNDLE_ASSET="OrcaStudio-aarch64.flatpak"
SUMS_ASSET="SHA256SUMS.txt"
WATCH_WORKFLOW="arm-upstream-watch.yml"
BUILD_INFO_REL="files/share/orcastudio-arm/BUILD_INFO"   # /app/share/... in sandbox
# Overridable only so the offline test harness can point at a local server.
API_BASE="${ORCASTUDIO_UPDATE_API_BASE:-https://api.github.com}"
WEB_BASE="${ORCASTUDIO_UPDATE_WEB_BASE:-https://github.com}"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}"
LOG_FILE="$STATE_DIR/orcastudio-update.log"
LOCK_FILE="$STATE_DIR/orcastudio-update.lock"
CACHE_BASE="${XDG_CACHE_HOME:-$HOME/.cache}"

EX_TEMPFAIL=75
CHECK_ONLY=0
FORCE=0
QUIET=0
WORK_DIR=""

# ---------------------------------------------------------------- logging --
log() {
    local line
    line="$(date '+%Y-%m-%dT%H:%M:%S%z') [$$] $*"
    mkdir -p "$STATE_DIR"
    printf '%s\n' "$line" >>"$LOG_FILE"
    if [[ "$QUIET" -eq 0 ]]; then printf '%s\n' "$line" >&2; fi
}

die() {  # die <exit-code> <message>
    local rc="$1"; shift
    QUIET=0 log "ERROR: $*"
    notify "OrcaStudio update failed" "$*"
    exit "$rc"
}

notify() {  # best effort desktop notification (Crostini: cros-notificationd)
    if command -v notify-send >/dev/null 2>&1; then
        notify-send --app-name="OrcaStudio updater" "$1" "$2" >/dev/null 2>&1 || true
    fi
}

trim_log() {  # keep the log bounded (~1 MiB)
    if [[ -f "$LOG_FILE" ]] && (( $(stat -c %s "$LOG_FILE") > 1048576 )); then
        tail -n 2000 "$LOG_FILE" >"$LOG_FILE.tmp" && mv -f "$LOG_FILE.tmp" "$LOG_FILE"
    fi
}

cleanup() {
    if [[ -n "$WORK_DIR" && -d "$WORK_DIR" ]]; then rm -rf -- "$WORK_DIR"; fi
}

# ------------------------------------------------------------ http helpers --
# http_get <url> <outfile> <headerfile> [api] -> prints HTTP status, "000" on
# transport failure. curl retries transient failures (incl. DNS / no network
# right after the container starts). Pass "api" to send GitHub REST headers.
http_get() {
    local url="$1" out="$2" hdr="$3" code rc=0
    local -a extra=(-H 'User-Agent: orcastudio-arm-updater')
    if [[ "${4:-}" == "api" ]]; then
        extra+=(-H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28')
    fi
    code="$(curl --silent --show-error --location --proto '=https' --tlsv1.2 \
        --connect-timeout 20 --max-time 3600 \
        --retry 5 --retry-delay 30 --retry-all-errors \
        "${extra[@]}" --dump-header "$hdr" --output "$out" \
        --write-out '%{http_code}' "$url")" || rc=$?
    if ((rc != 0)); then printf '000'; else printf '%s' "$code"; fi
}

# header_value <headerfile> <name> -> value of the LAST occurrence (after redirects)
header_value() {
    tr -d '\r' <"$1" | awk -v n="$(printf '%s' "$2" | tr '[:upper:]' '[:lower:]')" '
        { split($0, a, ":"); k = tolower(a[1]) }
        k == n { sub(/^[^:]*:[ \t]*/, ""); v = $0 }
        END { print v }'
}

# ------------------------------------------------------------ JSON parsing --
# parse_release_json <file> -> lines:
#   tag<TAB><tag_name>
#   asset<TAB><name><TAB><size><TAB><digest or empty>
# Uses python3 if present, else jq. Neither is guaranteed on Crostini; the
# installer checks for at least one.
parse_release_json() {
    local f="$1"
    if command -v python3 >/dev/null 2>&1; then
        python3 - "$f" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
if d.get("draft") or d.get("prerelease"):
    sys.exit("release is draft/prerelease")
print("tag\t%s" % d["tag_name"])
for a in d.get("assets", []):
    print("asset\t%s\t%s\t%s" % (a["name"], a.get("size", ""), a.get("digest") or ""))
PY
    elif command -v jq >/dev/null 2>&1; then
        jq -er 'if (.draft or .prerelease) then error("release is draft/prerelease") else . end
                | "tag\t\(.tag_name)",
                  (.assets[] | "asset\t\(.name)\t\(.size // "")\t\(.digest // "")")' "$f"
    else
        echo "neither python3 nor jq is installed (sudo apt install jq)" >&2
        return 1
    fi
}

# json_field_state <file> -> value of top-level "state" (workflow API)
json_field_state() {
    if command -v python3 >/dev/null 2>&1; then
        python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["state"])' "$1"
    elif command -v jq >/dev/null 2>&1; then
        jq -er '.state' "$1"
    else
        return 1
    fi
}

# json_last_run <file> -> "<conclusion>\t<html_url>" of workflow_runs[0], or nothing
json_last_run() {
    if command -v python3 >/dev/null 2>&1; then
        python3 -c 'import json,sys
r = json.load(open(sys.argv[1])).get("workflow_runs") or []
if r: print("%s\t%s" % (r[0].get("conclusion") or "", r[0].get("html_url") or ""))' "$1"
    elif command -v jq >/dev/null 2>&1; then
        jq -r '(.workflow_runs // [])[0] // empty | "\(.conclusion // "")\t\(.html_url // "")"' "$1"
    else
        return 1
    fi
}

valid_tag() { [[ "$1" =~ ^arm64-[A-Za-z0-9._-]+$ ]]; }

# --------------------------------------------------------- latest release --
# Sets LATEST_TAG, LATEST_BUNDLE_SIZE, LATEST_BUNDLE_DIGEST.
LATEST_TAG=""; LATEST_BUNDLE_SIZE=""; LATEST_BUNDLE_DIGEST=""
find_latest_release() {
    local json="$WORK_DIR/release.json" hdr="$WORK_DIR/release.hdr" code parsed
    code="$(http_get "$API_BASE/repos/$REPO/releases/latest" "$json" "$hdr" api)"
    case "$code" in
        200)
            parsed="$(parse_release_json "$json")" || die 1 "cannot parse release JSON"
            LATEST_TAG="$(awk -F'\t' '$1=="tag"{print $2}' <<<"$parsed")"
            local have_bundle have_sums
            have_bundle="$(awk -F'\t' -v n="$BUNDLE_ASSET" '$1=="asset" && $2==n' <<<"$parsed")"
            have_sums="$(awk -F'\t' -v n="$SUMS_ASSET" '$1=="asset" && $2==n' <<<"$parsed")"
            [[ -n "$have_bundle" ]] || die 1 "release $LATEST_TAG has no asset $BUNDLE_ASSET"
            [[ -n "$have_sums" ]] || die 1 "release $LATEST_TAG has no asset $SUMS_ASSET"
            LATEST_BUNDLE_SIZE="$(cut -f3 <<<"$have_bundle")"
            LATEST_BUNDLE_DIGEST="$(cut -f4 <<<"$have_bundle")"
            ;;
        404)
            log "no published release in $REPO yet; nothing to do"
            exit 0
            ;;
        403|429)
            local remaining reset
            remaining="$(header_value "$hdr" x-ratelimit-remaining)"
            reset="$(header_value "$hdr" x-ratelimit-reset)"
            if [[ "$remaining" == "0" ]]; then
                log "GitHub API rate limit hit (resets $(date -d "@${reset:-0}" '+%F %T' 2>/dev/null || echo '?')); using releases/latest/download redirect instead"
            else
                log "GitHub API returned HTTP $code; using releases/latest/download redirect instead"
            fi
            find_latest_release_via_redirect
            ;;
        000) die "$EX_TEMPFAIL" "network error contacting $API_BASE (offline?)" ;;
        *)   die "$EX_TEMPFAIL" "GitHub API returned HTTP $code for releases/latest" ;;
    esac
    valid_tag "$LATEST_TAG" || die 1 "unexpected release tag format: '$LATEST_TAG'"
}

# Fallback without the REST API (no rate limit): GitHub answers
# /releases/latest/download/<asset> with a 302 to /releases/download/<tag>/<asset>.
find_latest_release_via_redirect() {
    local loc
    loc="$(curl --silent --show-error --proto '=https' --tlsv1.2 --connect-timeout 20 \
            --retry 5 --retry-delay 30 --retry-all-errors --output /dev/null \
            --write-out '%{redirect_url}' \
            "$WEB_BASE/$REPO/releases/latest/download/$SUMS_ASSET")" \
        || die "$EX_TEMPFAIL" "redirect lookup failed"
    local prefix="$WEB_BASE/$REPO/releases/download/"
    [[ "$loc" == "$prefix"*"/$SUMS_ASSET" ]] || die "$EX_TEMPFAIL" "unexpected redirect target: '$loc'"
    LATEST_TAG="${loc#"$prefix"}"
    LATEST_TAG="${LATEST_TAG%"/$SUMS_ASSET"}"
}

# ------------------------------------------------------- installed state --
# Sets INSTALLED_TAG ("" if not installed, "unknown" if no BUILD_INFO),
# INSTALLED_ORIGIN, INSTALLED_ORIGIN_URL.
INSTALLED_TAG=""; INSTALLED_ORIGIN=""; INSTALLED_ORIGIN_URL=""
read_build_info_tag() {  # read_build_info_tag <BUILD_INFO path>
    [[ -r "$1" ]] || return 1
    awk -F= '$1=="release_tag"{sub(/^[^=]*=/, ""); gsub(/[ \t\r]+$/, ""); print; exit}' "$1"
}

read_installed_state() {
    local loc
    if ! loc="$(flatpak info --user --show-location "$APP_ID" 2>/dev/null)"; then
        INSTALLED_TAG=""
        return 0
    fi
    INSTALLED_ORIGIN="$(flatpak info --user --show-origin "$APP_ID")" \
        || die 1 "flatpak info --show-origin failed"
    INSTALLED_ORIGIN_URL="$(flatpak remote-list --user --show-disabled --columns=name,url \
        | awk -F'\t' -v o="$INSTALLED_ORIGIN" '$1==o{print $2; exit}')"
    INSTALLED_TAG="$(read_build_info_tag "$loc/$BUILD_INFO_REL" || true)"
    [[ -n "$INSTALLED_TAG" ]] || INSTALLED_TAG="unknown"
}

app_is_running() {
    flatpak ps --columns=application 2>/dev/null | grep -Fxq "$APP_ID"
}

# --------------------------------------------------------- verification --
# expected_sha <sums file> <asset> -> hex (exactly one matching line required)
expected_sha() {
    awk -v n="$2" '($2==n || $2=="*" n) {print tolower($1); c++} END {exit c==1?0:1}' "$1"
}

verify_bundle() {  # verify_bundle <bundle> <sums>
    local want got
    want="$(expected_sha "$2" "$BUNDLE_ASSET")" \
        || die 1 "$SUMS_ASSET has no single entry for $BUNDLE_ASSET"
    [[ "$want" =~ ^[0-9a-f]{64}$ ]] || die 1 "malformed checksum in $SUMS_ASSET"
    got="$(sha256sum -- "$1" | awk '{print $1}')"
    [[ "$got" == "$want" ]] || die 1 "SHA-256 mismatch for $BUNDLE_ASSET: got $got want $want"
    if [[ -n "$LATEST_BUNDLE_DIGEST" ]]; then
        # GitHub-computed asset digest ("sha256:<hex>") from the release API.
        [[ "$LATEST_BUNDLE_DIGEST" == "sha256:$got" ]] \
            || die 1 "GitHub asset digest $LATEST_BUNDLE_DIGEST != sha256:$got"
    fi
    log "sha256 verified: $got"
}

# ---------------------------------------------------------- watch health --
check_watch_workflow() {
    local f="$WORK_DIR/workflow.json" h="$WORK_DIR/workflow.hdr" code state
    code="$(http_get "$API_BASE/repos/$REPO/actions/workflows/$WATCH_WORKFLOW" "$f" "$h" api)"
    if [[ "$code" != "200" ]]; then
        log "note: could not read $WATCH_WORKFLOW state (HTTP $code)"
        return 0
    fi
    state="$(json_field_state "$f" 2>/dev/null || echo '?')"
    if [[ "$state" != "active" ]]; then
        log "WARNING: workflow $WATCH_WORKFLOW is '$state' - no new builds will be made. Re-enable: GitHub > $REPO > Actions > ARM upstream watch > Enable workflow"
        notify "OrcaStudio auto-build is paused" "GitHub workflow $WATCH_WORKFLOW is '$state'. Re-enable it in the repository's Actions tab."
    fi
    # GitHub only notifies about failed runs if the owner opted in (Settings >
    # Notifications > Actions), so surface the newest finished run here too.
    f="$WORK_DIR/runs.json"
    code="$(http_get "$API_BASE/repos/$REPO/actions/workflows/$WATCH_WORKFLOW/runs?per_page=1&status=completed" "$f" "$h" api)"
    [[ "$code" == "200" ]] || return 0
    local run conclusion url
    run="$(json_last_run "$f" 2>/dev/null || true)"
    conclusion="${run%%$'\t'*}"
    url="${run#*$'\t'}"
    case "$conclusion" in
        ""|success|skipped|neutral) ;;
        *)
            log "WARNING: last $WATCH_WORKFLOW run concluded '$conclusion': $url"
            notify "OrcaStudio auto-build: last run $conclusion" "$url"
            ;;
    esac
}

# ---------------------------------------------------------------- install --
install_bundle() {  # install_bundle <bundle>
    local bundle="$1" migrate=0
    # A bundle install onto an existing deployment reuses that deployment's
    # origin remote (flatpak 1.16 common/flatpak-dir.c ensure_bundle_remote).
    # If the app came from a URL remote (e.g. a local flatpak-builder repo),
    # `flatpak update` could later "update" it back to that build, so move it
    # to a bundle origin once: uninstall WITHOUT --delete-data, then install.
    if [[ -n "$INSTALLED_TAG" && -n "$INSTALLED_ORIGIN_URL" ]]; then
        migrate=1
        log "migrating $APP_ID off remote '$INSTALLED_ORIGIN' ($INSTALLED_ORIGIN_URL); user data in ~/.var/app/$APP_ID is kept"
        flatpak uninstall --user --noninteractive "$APP_ID" >>"$LOG_FILE" 2>&1 \
            || die 1 "flatpak uninstall failed (see log)"
    fi
    if ! flatpak install --user --noninteractive --reinstall --bundle "$bundle" >>"$LOG_FILE" 2>&1; then
        if [[ "$migrate" -eq 1 ]]; then
            log "bundle install failed after uninstall; trying to restore from '$INSTALLED_ORIGIN'"
            flatpak install --user --noninteractive "$INSTALLED_ORIGIN" "$APP_ID" >>"$LOG_FILE" 2>&1 \
                || log "restore from '$INSTALLED_ORIGIN' failed too; reinstall manually"
        fi
        die 1 "flatpak install --bundle failed (see $LOG_FILE)"
    fi
}

# ------------------------------------------------------------------- main --
usage() { sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; }

main() {
    while (($#)); do
        case "$1" in
            --check) CHECK_ONLY=1 ;;
            --force) FORCE=1 ;;
            --quiet) QUIET=1 ;;
            -h|--help) usage; exit 0 ;;
            *) usage >&2; exit 2 ;;
        esac
        shift
    done

    mkdir -p "$STATE_DIR" "$CACHE_BASE"
    trim_log
    exec 9>"$LOCK_FILE"
    flock -n 9 || { log "another update run holds $LOCK_FILE; exiting"; exit 0; }

    local arch
    arch="$(uname -m)"
    [[ "$arch" == "aarch64" ]] || die 1 "host architecture is '$arch'; this updater only installs aarch64 bundles"
    for c in flatpak curl sha256sum awk flock; do
        command -v "$c" >/dev/null 2>&1 || die 1 "required command '$c' not found"
    done

    WORK_DIR="$(mktemp -d "$CACHE_BASE/orcastudio-update.XXXXXX")"
    trap cleanup EXIT

    log "start (check=$CHECK_ONLY force=$FORCE) repo=$REPO"
    find_latest_release
    read_installed_state
    check_watch_workflow
    if flatpak info --system "$APP_ID" >/dev/null 2>&1; then
        log "WARNING: a system-wide $APP_ID is also installed; this updater manages only the --user one"
    fi
    log "latest release: $LATEST_TAG; installed: ${INSTALLED_TAG:-<not installed>} (origin: ${INSTALLED_ORIGIN:-n/a}${INSTALLED_ORIGIN_URL:+ $INSTALLED_ORIGIN_URL})"

    if [[ "$INSTALLED_TAG" == "$LATEST_TAG" && "$FORCE" -eq 0 ]]; then
        log "up to date"
        exit 0
    fi
    if [[ "$CHECK_ONLY" -eq 1 ]]; then
        log "--check: would install $LATEST_TAG (currently ${INSTALLED_TAG:-not installed})"
        exit 0
    fi
    if app_is_running; then
        log "$APP_ID is running; not updating now (next run will retry)"
        exit 0
    fi

    local base="$WEB_BASE/$REPO/releases/download/$LATEST_TAG" code
    code="$(http_get "$base/$SUMS_ASSET" "$WORK_DIR/$SUMS_ASSET" "$WORK_DIR/sums.hdr")"
    [[ "$code" == "200" ]] || die "$EX_TEMPFAIL" "download of $SUMS_ASSET failed (HTTP $code)"
    log "downloading $BUNDLE_ASSET ${LATEST_BUNDLE_SIZE:+($LATEST_BUNDLE_SIZE bytes) }from $LATEST_TAG"
    code="$(http_get "$base/$BUNDLE_ASSET" "$WORK_DIR/$BUNDLE_ASSET" "$WORK_DIR/bundle.hdr")"
    [[ "$code" == "200" ]] || die "$EX_TEMPFAIL" "download of $BUNDLE_ASSET failed (HTTP $code)"
    if [[ -n "$LATEST_BUNDLE_SIZE" ]] \
        && [[ "$(stat -c %s "$WORK_DIR/$BUNDLE_ASSET")" != "$LATEST_BUNDLE_SIZE" ]]; then
        die "$EX_TEMPFAIL" "downloaded size differs from release metadata (truncated download?)"
    fi
    verify_bundle "$WORK_DIR/$BUNDLE_ASSET" "$WORK_DIR/$SUMS_ASSET"

    # Re-check right before touching the installation.
    if app_is_running; then
        log "$APP_ID started during download; not updating now"
        exit 0
    fi
    install_bundle "$WORK_DIR/$BUNDLE_ASSET"

    read_installed_state
    [[ "$INSTALLED_TAG" == "$LATEST_TAG" ]] \
        || die 1 "post-install check: BUILD_INFO says '$INSTALLED_TAG', expected '$LATEST_TAG'"
    log "installed $LATEST_TAG (origin: $INSTALLED_ORIGIN)"
    notify "OrcaStudio updated" "Installed $LATEST_TAG"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
