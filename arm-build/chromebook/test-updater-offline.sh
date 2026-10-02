#!/usr/bin/env bash
# shellcheck disable=SC2015,SC2016  # ok()/bad() always return 0; stub bodies are literal on purpose
# Offline test harness for orcastudio-update.sh (developer machine, any arch).
# Starts a local HTTPS mock of api.github.com + github.com release downloads,
# stubs `flatpak`, `uname` and `notify-send` on PATH, then runs scenarios.
# Needs: bash, python3, openssl, curl, jq (for the jq-only parsing case).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPDATER="$HERE/orcastudio-update.sh"
T="$(mktemp -d)"
SERVER_PID=""
harness_cleanup() {
    if [[ -n "$SERVER_PID" ]]; then kill "$SERVER_PID" 2>/dev/null || true; fi
    rm -rf -- "$T"
}
trap harness_cleanup EXIT

PASS=0 FAIL=0
ok()   { PASS=$((PASS + 1)); printf 'PASS  %s\n' "$1"; }
bad()  { FAIL=$((FAIL + 1)); printf 'FAIL  %s\n' "$1"; }
expect() {  # expect <name> <expected-rc> <actual-rc> [grep-pattern-in-log]
    local name="$1" want="$2" got="$3" pat="${4:-}"
    if [[ "$got" != "$want" ]]; then bad "$name (rc $got, want $want)"; return; fi
    if [[ -n "$pat" ]] && ! grep -Eq -- "$pat" "$T/home/.local/state/orcastudio-update.log"; then
        bad "$name (log lacks /$pat/)"; return
    fi
    ok "$name"
}

# ------------------------------------------------------------- fixtures --
NEW_TAG="arm64-v02.08.01.55-p6-obn-v2.2.0-r7"
OLD_TAG="arm64-v02.08.01.55-p5-obn-v2.2.0-r6"
mkdir -p "$T/srv/BaIanced/orcastudio/releases/download/$NEW_TAG" "$T/home" "$T/bin" "$T/fp"
BUNDLE="$T/srv/BaIanced/orcastudio/releases/download/$NEW_TAG/OrcaStudio-aarch64.flatpak"
# Fake bundle: the stub flatpak "installs" it by copying it to BUILD_INFO.
printf 'orcastudio_tag=v02.08.01.55-p6\r\nobn_tag=v2.2.0\nrelease_tag=%s\n' "$NEW_TAG" >"$BUNDLE"
SHA="$(sha256sum "$BUNDLE" | awk '{print $1}')"
SIZE="$(stat -c %s "$BUNDLE")"
printf '%s  OrcaStudio-aarch64.flatpak\n' "$SHA" >"$(dirname "$BUNDLE")/SHA256SUMS.txt"

release_json() {  # release_json <digest>
    cat <<EOF
{"tag_name": "$NEW_TAG", "draft": false, "prerelease": false,
 "assets": [
  {"name": "SHA256SUMS.txt", "size": 92, "digest": null},
  {"name": "OrcaStudio-aarch64.flatpak", "size": $SIZE, "digest": "$1"}]}
EOF
}

openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj '/CN=127.0.0.1' \
    -addext 'subjectAltName=IP:127.0.0.1' -keyout "$T/key.pem" -out "$T/cert.pem" 2>/dev/null

cat >"$T/server.py" <<'PY'
import http.server, os, ssl, sys
root, port = sys.argv[1], int(sys.argv[2])
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, code, body=b"", headers=()):
        self.send_response(code)
        for k, v in headers: self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        mode = open(os.path.join(root, "mode")).read().strip()
        p = self.path
        if p == "/repos/BaIanced/orcastudio/releases/latest":
            if mode == "ratelimit":
                return self.send(403, b'{"message":"API rate limit exceeded"}',
                                 [("x-ratelimit-remaining", "0"), ("x-ratelimit-reset", "1900000000")])
            if mode == "norelease":
                return self.send(404, b'{"message":"Not Found"}')
            return self.send(200, open(os.path.join(root, "release.json"), "rb").read())
        if p.startswith("/repos/BaIanced/orcastudio/actions/workflows/arm-upstream-watch.yml/runs?"):
            assert "status=completed" in p and "per_page=1" in p, p
            c = "failure" if mode == "wffailed" else "success"
            return self.send(200, ('{"total_count": 9, "workflow_runs": [{"conclusion": "%s", '
                                   '"html_url": "https://github.com/BaIanced/orcastudio/actions/runs/42"}]}' % c).encode())
        if p == "/repos/BaIanced/orcastudio/actions/workflows/arm-upstream-watch.yml":
            st = "disabled_inactivity" if mode == "wfdisabled" else "active"
            return self.send(200, ('{"state": "%s"}' % st).encode())
        if p == "/BaIanced/orcastudio/releases/latest/download/SHA256SUMS.txt":
            tag = open(os.path.join(root, "tag")).read().strip()
            return self.send(302, b"", [("Location",
                f"https://127.0.0.1:{port}/BaIanced/orcastudio/releases/download/{tag}/SHA256SUMS.txt")])
        f = os.path.join(root, p.lstrip("/"))
        if os.path.isfile(f):
            return self.send(200, open(f, "rb").read())
        return self.send(404, b"nf")
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(sys.argv[3], sys.argv[4])
s = http.server.ThreadingHTTPServer(("127.0.0.1", port), H)
s.socket = ctx.wrap_socket(s.socket, server_side=True)
s.serve_forever()
PY
PORT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')"
echo "$NEW_TAG" >"$T/srv/tag"
echo normal >"$T/srv/mode"
python3 "$T/server.py" "$T/srv" "$PORT" "$T/cert.pem" "$T/key.pem" &
SERVER_PID=$!
for _ in $(seq 50); do
    curl -s --cacert "$T/cert.pem" --noproxy '*' -o /dev/null "https://127.0.0.1:$PORT/x" && break
    sleep 0.1
done

# ---------------------------------------------------------------- stubs --
# Fake flatpak state lives in $T/fp: installed(0/1) origin url running deploydir
cat >"$T/bin/flatpak" <<'SH'
#!/usr/bin/env bash
fp="$FAKE_FP"
echo "flatpak $*" >>"$fp/calls"
case "$1" in
  info)
    [[ "$2" == "--system" ]] && exit 1
    [[ "$(cat "$fp/installed")" == 1 ]] || exit 1
    case "$3" in
      --show-location) echo "$fp/deploy" ;;
      --show-origin) cat "$fp/origin" ;;
    esac ;;
  remote-list) printf '%s\t%s\n' flathub https://dl.flathub.org/repo/ "$(cat "$fp/origin")" "$(cat "$fp/url")" ;;
  ps) [[ "$(cat "$fp/running")" == 1 ]] && printf 'com.orcaslicer.OrcaStudio\n'; exit 0 ;;
  uninstall)  # next bundle install will get a fresh bundle origin (empty URL)
    echo 0 >"$fp/installed"; rm -rf "$fp/deploy"; echo orcastudio-origin >"$fp/origin"; : >"$fp/url" ;;
  install)
    [[ -f "$fp/fail_install" ]] && exit 1
    bundle="${*: -1}"
    mkdir -p "$fp/deploy/files/share/orcastudio-arm"
    cp "$bundle" "$fp/deploy/files/share/orcastudio-arm/BUILD_INFO"
    echo 1 >"$fp/installed" ;;
esac
SH
printf '#!/bin/sh\necho "${FAKE_ARCH:-aarch64}"\n' >"$T/bin/uname"
printf '#!/bin/sh\necho "notify: $*" >>"$FAKE_FP/calls"\n' >"$T/bin/notify-send"
chmod +x "$T/bin/"*

reset_fp() {  # reset_fp <installed 0/1> <installed-tag|-> <origin> <url> <running 0/1>
    rm -rf "$T/fp" "$T/home/.local/state"; mkdir -p "$T/fp"
    echo "$1" >"$T/fp/installed"
    echo "$3" >"$T/fp/origin"; printf '%s' "$4" >"$T/fp/url"; echo "$5" >"$T/fp/running"
    : >"$T/fp/calls"
    if [[ "$1" == 1 ]]; then
        mkdir -p "$T/fp/deploy/files/share/orcastudio-arm"
        if [[ "$2" != "-" ]]; then
            printf 'orcastudio_tag=x\nrelease_tag=%s\n' "$2" >"$T/fp/deploy/files/share/orcastudio-arm/BUILD_INFO"
        fi
    fi
}

run() {  # run [args...] -> rc in $RC
    set +e
    env -i HOME="$T/home" PATH="$T/bin:/usr/local/bin:/usr/bin:/bin" \
        FAKE_FP="$T/fp" FAKE_ARCH="${FAKE_ARCH:-aarch64}" \
        CURL_CA_BUNDLE="$T/cert.pem" NO_PROXY='*' no_proxy='*' \
        ORCASTUDIO_UPDATE_API_BASE="https://127.0.0.1:$PORT" \
        ORCASTUDIO_UPDATE_WEB_BASE="https://127.0.0.1:$PORT" \
        bash "$UPDATER" --quiet "$@" 2>/dev/null
    RC=$?
    set -e
}
installed_tag() { awk -F= '$1=="release_tag"{print $2}' "$T/fp/deploy/files/share/orcastudio-arm/BUILD_INFO" 2>/dev/null; }

# ------------------------------------------------------------ scenarios --
release_json "sha256:$SHA" >"$T/srv/release.json"

reset_fp 0 - "" "" 0; run
expect "fresh install" 0 "$RC" "installed $NEW_TAG"
[[ "$(installed_tag)" == "$NEW_TAG" ]] && ok "fresh install BUILD_INFO" || bad "fresh install BUILD_INFO"

reset_fp 1 "$NEW_TAG" orcastudio-origin "" 0; run
expect "up to date -> no install" 0 "$RC" "up to date"
grep -q 'flatpak install' "$T/fp/calls" && bad "up to date called install" || ok "up to date: no install call"

reset_fp 1 "$OLD_TAG" orcastudio-origin "" 0; run --check
expect "--check reports" 0 "$RC" "would install $NEW_TAG"
grep -q 'flatpak install' "$T/fp/calls" && bad "--check installed" || ok "--check: no install call"

reset_fp 1 "$OLD_TAG" orcastudio-origin "" 1; run
expect "running app -> skip" 0 "$RC" "is running; not updating"

reset_fp 1 "$OLD_TAG" orcastudio-origin "" 0; run
expect "bundle-origin update (no migration)" 0 "$RC" "installed $NEW_TAG"
grep -q 'flatpak uninstall' "$T/fp/calls" && bad "unexpected uninstall" || ok "no uninstall for bundle origin"
grep -q -- 'install --user --noninteractive --reinstall --bundle' "$T/fp/calls" && ok "install flags" || bad "install flags"

reset_fp 1 - local-repo "file:///home/u/orca/repo" 0; run
expect "local-repo origin + no BUILD_INFO -> migrate" 0 "$RC" "migrating .* off remote 'local-repo'"
grep -q 'flatpak uninstall --user --noninteractive com.orcaslicer.OrcaStudio' "$T/fp/calls" \
    && ok "migration uninstall keeps data (no --delete-data)" || bad "migration uninstall"
grep -q -- '--delete-data' "$T/fp/calls" && bad "delete-data used" || true

reset_fp 1 "$OLD_TAG" local-repo "file:///x" 0; touch "$T/fp/fail_install"; run
expect "migration install failure -> restore attempt, rc1" 1 "$RC" "trying to restore from 'local-repo'"
rm -f "$T/fp/fail_install"

reset_fp 1 "$NEW_TAG" orcastudio-origin "" 0; run --force
expect "--force reinstalls same tag" 0 "$RC" "installed $NEW_TAG"

release_json "sha256:$(printf '0%.0s' $(seq 64))" >"$T/srv/release.json"
reset_fp 1 "$OLD_TAG" orcastudio-origin "" 0; run
expect "GitHub digest mismatch -> fail" 1 "$RC" "GitHub asset digest"
[[ "$(installed_tag)" == "$OLD_TAG" ]] && ok "digest mismatch: old version kept" || bad "digest mismatch changed install"
release_json "sha256:$SHA" >"$T/srv/release.json"

cp "$(dirname "$BUNDLE")/SHA256SUMS.txt" "$T/sums.bak"
printf '%s  OrcaStudio-aarch64.flatpak\n' "$(printf 'a%.0s' $(seq 64))" >"$(dirname "$BUNDLE")/SHA256SUMS.txt"
release_json "" >"$T/srv/release.json"
reset_fp 1 "$OLD_TAG" orcastudio-origin "" 0; run
expect "SHA256SUMS mismatch -> fail" 1 "$RC" "SHA-256 mismatch"
cp "$T/sums.bak" "$(dirname "$BUNDLE")/SHA256SUMS.txt"

echo ratelimit >"$T/srv/mode"
reset_fp 1 "$OLD_TAG" orcastudio-origin "" 0; run
expect "API rate limit -> redirect fallback installs" 0 "$RC" "rate limit hit.*redirect"
[[ "$(installed_tag)" == "$NEW_TAG" ]] && ok "fallback BUILD_INFO" || bad "fallback BUILD_INFO"

echo norelease >"$T/srv/mode"
reset_fp 0 - "" "" 0; run
expect "no release yet -> rc0" 0 "$RC" "no published release"

echo wfdisabled >"$T/srv/mode"
reset_fp 1 "$NEW_TAG" orcastudio-origin "" 0; run
expect "watch workflow disabled -> warning + notify" 0 "$RC" "is 'disabled_inactivity'"
grep -q 'notify: .*OrcaStudio auto-build is paused' "$T/fp/calls" && ok "notification sent" || bad "notification"
echo wffailed >"$T/srv/mode"
reset_fp 1 "$NEW_TAG" orcastudio-origin "" 0; run
expect "last watch run failed -> warning" 0 "$RC" "concluded 'failure': https://github.com/BaIanced/orcastudio/actions/runs/42"
grep -q 'notify: .*auto-build: last run failure' "$T/fp/calls" && ok "failure notification sent" || bad "failure notification"
echo normal >"$T/srv/mode"
reset_fp 1 "$NEW_TAG" orcastudio-origin "" 0; run
grep -q 'notify' "$T/fp/calls" && bad "notification on healthy run" || ok "healthy: no notification"

reset_fp 0 - "" "" 0; FAKE_ARCH=x86_64 run
expect "non-aarch64 host refused" 1 "$RC" "only installs aarch64"

echo '{"tag_name": "evil;rm -rf ~", "assets": [{"name":"OrcaStudio-aarch64.flatpak","size":1},{"name":"SHA256SUMS.txt","size":1}]}' >"$T/srv/release.json"
reset_fp 0 - "" "" 0; run
expect "malicious tag rejected" 1 "$RC" "unexpected release tag format"
release_json "sha256:$SHA" >"$T/srv/release.json"

# ---- unit-level checks by sourcing the script (functions only) ----
# shellcheck source=orcastudio-update.sh
source "$UPDATER"
printf 'orcastudio_tag=a\r\nrelease_tag=arm64-x-r1  \r\nobn_tag=b\n' >"$T/bi"
[[ "$(read_build_info_tag "$T/bi")" == "arm64-x-r1" ]] && ok "BUILD_INFO CRLF/whitespace" || bad "BUILD_INFO CRLF"
read_build_info_tag "$T/nonexistent" >/dev/null && bad "missing BUILD_INFO" || ok "missing BUILD_INFO -> rc1"
printf '%s *OrcaStudio-aarch64.flatpak\n%s  other\n' "$SHA" "$SHA" >"$T/s1"
[[ "$(expected_sha "$T/s1" OrcaStudio-aarch64.flatpak)" == "$SHA" ]] && ok "sums binary-mode '*name'" || bad "sums *name"
printf '%s  OrcaStudio-aarch64.flatpak\n%s  OrcaStudio-aarch64.flatpak\n' "$SHA" "$SHA" >"$T/s2"
expected_sha "$T/s2" OrcaStudio-aarch64.flatpak >/dev/null && bad "duplicate sums accepted" || ok "duplicate sums rejected"
release_json "sha256:$SHA" >"$T/r.json"
py_out="$(parse_release_json "$T/r.json")"
printf '{"workflow_runs":[{"conclusion":null,"html_url":"u"}]}' >"$T/runs1.json"
printf '{"total_count":0,"workflow_runs":[]}' >"$T/runs0.json"
py_runs="$(json_last_run "$T/runs1.json")|$(json_last_run "$T/runs0.json")"
mkdir -p "$T/nopy"
for c in jq bash cat env; do ln -sf "$(command -v "$c")" "$T/nopy/$c"; done
jq_out="$(PATH="$T/nopy" parse_release_json "$T/r.json")"
jq_runs="$(PATH="$T/nopy" json_last_run "$T/runs1.json")|$(PATH="$T/nopy" json_last_run "$T/runs0.json")"
[[ "$py_runs" == "$jq_runs" && "$py_runs" == $'\tu|' ]] && ok "run parsers agree (null conclusion, empty list)" || bad "run parsers: [$py_runs] vs [$jq_runs]"
[[ "$py_out" == "$jq_out" && "$py_out" == *"tag	$NEW_TAG"* ]] && ok "python3 and jq parsers agree" || bad "parsers differ: [$py_out] vs [$jq_out]"
echo '{"tag_name":"arm64-a","prerelease":true,"assets":[]}' >"$T/pre.json"
parse_release_json "$T/pre.json" >/dev/null 2>&1 && bad "prerelease accepted" || ok "prerelease rejected"

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
