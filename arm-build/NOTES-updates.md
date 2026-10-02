# Upstream tracking and Chromebook auto-update (Agent C)

Files:

| File | Runs where | Purpose |
|---|---|---|
| `arm-build/bump-versions.py` | CI (any Python 3.8+, stdlib) | newest upstream release tags → `versions.json`, GitHub Actions outputs |
| `.github/workflows/arm-upstream-watch.yml` | GitHub Actions | daily: detect, merge upstream tag, push, call the build |
| `arm-build/chromebook/orcastudio-update.sh` | Chromebook, Crostini **host** (not the sandbox) | download, verify and install the newest bundle |
| `arm-build/chromebook/orcastudio-update.{service,timer}` | Chromebook, `systemd --user` | run the updater daily |
| `arm-build/chromebook/install-updater.sh` | Chromebook, host | install the files above, enable the timer, run a first `--check` |
| `arm-build/chromebook/test-updater-offline.sh` | any dev machine | offline tests (HTTPS mock of GitHub, stubbed `flatpak`), 34 checks |

## Flow

```
10:41 UTC daily (cron '41 10 * * *')  or  workflow_dispatch(force_build, dry_run)
  arm-upstream-watch.yml / job sync  (ubuntu-24.04, GITHUB_TOKEN or ARM_SYNC_PAT)
   ├─ checkout main, fetch-depth 0
   ├─ bump-versions.py --self-test         (ordering tests on the real tag lists)
   ├─ bump-versions.py --write             git ls-remote --tags (no API, no token)
   │     no change ──────────────────────────────────────────────► build=false (unless force_build)
   ├─ commit arm-build/versions.json
   ├─ if OrcaStudio changed:
   │     git fetch --no-tags <upstream> refs/tags/<tag>; check FETCH_HEAD^{commit} == ls-remote commit
   │     upstream diff touches .github/workflows/ and no ARM_SYNC_PAT ──► merge SKIPPED (warning); bump + build continue
   │     git merge --no-ff <commit>   conflict ──► merge --abort, FAIL (summary lists paths)
   │     warn if main != upstream tag outside arm-build/ and .github/workflows/arm-*.yml
   ├─ git push origin HEAD:refs/heads/main   (non-force; rejected ──► FAIL)
   ├─ summary table; outputs build, sha (= merged HEAD)
   └─ keepalive: PUT /actions/workflows/arm-upstream-watch.yml/enable (best effort)
  job build: uses ./.github/workflows/arm-flatpak.yml  with ci_ref=<sha>   (Agent B)
     └─ release arm64-<os_tag>-obn-<obn_tag>-r<run_number>: OrcaStudio-aarch64.flatpak + SHA256SUMS.txt

Chromebook, daily 13:30 local (+0–20 min), Persistent=true  → orcastudio-update.sh --quiet
   ├─ flock; uname -m == aarch64; needs flatpak curl sha256sum flock awk + (python3 | jq)
   ├─ GET api.github.com/repos/BaIanced/orcastudio/releases/latest (unauthenticated)
   │     404 → no release yet, exit 0 │ 403/429 → fallback: /releases/latest/download/SHA256SUMS.txt
   │     302 Location gives the tag   │ network error → exit 75 (systemd retries in 20 min)
   ├─ tag must match ^arm64-[A-Za-z0-9._-]+$ ; both assets must exist
   ├─ installed tag: $(flatpak info --user --show-location com.orcaslicer.OrcaStudio)/files/share/orcastudio-arm/BUILD_INFO
   │     (= /app/share/orcastudio-arm/BUILD_INFO inside the sandbox), key release_tag
   ├─ GET .../actions/workflows/arm-upstream-watch.yml (+ /runs?per_page=1&status=completed)
   │     state != active, or last run failed → log + notify-send
   ├─ equal tag (and no --force) → exit 0;  --check → report, exit 0;  app running (flatpak ps) → exit 0
   ├─ download SHA256SUMS.txt + bundle to ~/.cache/orcastudio-update.XXXXXX (size checked)
   ├─ sha256 vs SHA256SUMS.txt (exactly one entry) and vs GitHub asset "digest" when present
   ├─ re-check flatpak ps
   ├─ origin has a URL (old local flatpak-builder repo) and only this app uses it?
   │     → flatpak remote-modify --user --disable <origin>   (never uninstalls)
   ├─ LC_ALL=C flatpak install --user --noninteractive --reinstall --bundle <file>
   │     failure → installed version unchanged; network fetch error (Flathub) → exit 75
   │     (systemd retries), other → exit 1; "already installed" + same tag → exit 0
   └─ re-read BUILD_INFO: must equal the new tag; log + notify
```

## Decisions

**Tag ordering** (from the full tag lists, 2026-10-02). OrcaStudio: 13 tags, shapes
`vAA.BB.CC.DD` and `vAA.BB.CC.DD-pN`; mix of annotated (`v02.07.01.57*`, `v02.08.01.55`,
`-p3`) and lightweight tags. Every tag has a normal (not pre-release) GitHub release;
`-p6` is "Latest". So `-pN` is a post-release patch: `vX < vX-p1 < … < vX-p10 < vY`.
Commit history confirms it: every tag is an ancestor of the next. obn: `v1.0.0 … v2.2.0`,
all lightweight. Accepted regex `^v\d+(\.\d+)*(-p\d+)?$`, key = (numeric parts, N or 0).
Anything else (`-rc1`, `-beta`, `nightly`) is ignored and logged. Never downgrades; a
moved tag (same name, new commit) counts as a change and logs a warning. Self-test
includes the real ls-remote output and a mutation check (lexical `max()` fails 3 checks).

**Track tags, not GitHub releases.** obn's release list via the web was inconsistent
(v2.2.0 release exists but the list showed v2.1.0 as latest), and `api.github.com` for
other repos is not reachable from this workspace. `git ls-remote` needs no token and
has no REST rate limit.

**Build trigger: reusable workflow (`uses: ./.github/workflows/arm-flatpak.yml`), not
`gh workflow run`.**
1. A failed build fails the scheduled run, so it shows up where schedule notifications
   go. A run dispatched by GITHUB_TOKEN has `github-actions[bot]` as actor; who would be
   told about its failure is undocumented.
2. No `actions: write` needed just to dispatch.
3. Cost: in a called workflow `github.sha` is the caller's commit, which is main
   *before* the merge (actions/checkout v7 `src/input-helper.ts`: default `ref`/`commit`
   = `github.context.ref`/`sha`). So the caller passes `ci_ref: <merged sha>`, and B's
   workflow checks out `inputs.ci_ref || github.sha`. actionlint validates the input
   name against B's `workflow_call` block (tested: a wrong name is reported).
4. `github.run_number` in the called workflow is the caller's, so B's
   `arm64-…-r<run_number>` can collide with a manual arm-flatpak run. B's workflow
   already checks this and fails on collision.
5. Caller grants `contents: write` + `actions: write`, the union of B's job-level
   permissions (deps/app `contents: read`, release `contents: write`, prune-caches
   `actions: write`). Called workflows can only lower permissions.
6. Concurrency: caller group `arm-upstream-watch-singleton`, B uses
   `orcastudio-arm64-flatpak`. They differ, so no shared-group deadlock.

**Merge, not rebase**: `--no-ff` merge of the peeled tag commit (not of FETCH_HEAD, so
exactly the ls-remote commit is merged). Order: versions.json commit, then merge. On
failure nothing is pushed. Once someone merges by hand, the next run sees "Already up to
date" for the merge and pushes only the pin. Simulated on a real clone (fork at `-p3` +
our commit → `-p6`): workflow-file guard fires (p4 changed `build_windows_bridge.yml`);
merge with PAT succeeds; push and decide steps work; divergence warning fires on a local
edit; a conflict on `.gitattributes` aborts cleanly and lists the path.

**GITHUB_TOKEN cannot push workflow-file changes.** No `workflows` permission exists for
it (the docs' permissions list has none; GitHub staff in community discussion #26583:
"you'll need to continue to use a PAT that has the `workflow` permission"). Upstream
changed `.github/workflows/` in 4 of its 12 tag-to-tag steps (p1, 02.08.01.55, 55-p1,
55-p4). Without help, about a third of upstream updates would fail. Fix: optional repo
secret `ARM_SYNC_PAT` (fine-grained, this repo only, Contents RW + Workflows RW). With
it, checkout and push use the PAT. Without it, the fork-sync merge is skipped with a warning (lead change, 2026-10-02): the build compiles the pinned upstream commit directly, so it never depends on this merge. Conflicts are handled the same way.
Pushes made with a PAT do start `push` workflows. None of ours (and none of upstream's
branch triggers) listen on a branch push, so this causes no double build.

**Upstream `my_build_all.yml` will not fire.** It triggers on `push: tags: ['v*']`,
`release: published` and manual dispatch. (a) We fetch with `--no-tags` and push only
`HEAD:refs/heads/main`. With only a `tags` filter, branch pushes don't trigger it (docs).
(b) B creates releases and tags with GITHUB_TOKEN: "events triggered by the GITHUB_TOKEN,
with the exception of workflow_dispatch and repository_dispatch, will not create a new
workflow run". The tags are `arm64-*` anyway, which don't match `v*`.

**60-day auto-disable.** Docs: "In a public repository, scheduled workflows are
automatically disabled when no repository activity has occurred in 60 days." The docs
don't define "repository activity". Upstream gaps between tags reached 53 days
(55-p3 2026-08-03 → 55-p4 2026-09-25), so a quiet upstream could hit 60 days.
- Re-enabling from inside the workflow can't revive a disabled workflow, which never
  runs. While it still runs, the workflow calls `PUT …/workflows/arm-upstream-watch.yml/enable`
  daily (`continue-on-error`). Third-party tools say this resets the counter
  (gh-workflow-immortality); GitHub doesn't document it.
- I did not add dummy keepalive commits. They pollute history, and the best-known
  commit-keepalive action repo (gautamkrishnar/keepalive-workflow) is now "disabled by
  GitHub Staff due to a violation of GitHub's terms of service".
- What actually works: the Chromebook updater reads the workflow `state` daily
  (unauthenticated public endpoint) and sends a desktop notification if it is not
  `active`. Re-enabling takes one click in Actions. After a re-enable, schedule
  notifications go to the user who re-enabled it (docs).

**Failure notification claim ("GitHub emails the owner on failed scheduled runs"): only
partly true.** Docs: "Notifications for scheduled workflows are sent to the user who
initially created the workflow" (or whoever last changed the cron, or whoever
re-enabled). But Actions notification delivery is opt-in: Settings → Notifications →
System → Actions starts at "Don't notify". The docs say "To opt in to email
notifications… select Email", plus optionally "Only notify for failed workflows". The
fork has `has_issues=false`, so the failure goes to `$GITHUB_STEP_SUMMARY`. The
Chromebook updater also reports the newest completed watch run's conclusion and notifies
on failure.

**Crostini systemd user instance: verified, so the timer is primary.**
cros-container-guest-tools (HEAD 191fb50e, 2026-09-30) ships `cros-garcon.service`,
`sommelier@.service` and others into `/usr/lib/systemd/user` with
`default.target.wants` links. Its LXD test checks
`systemctl --user is-active cros-garcon.service`. Linux GUI apps launch through garcon,
so a user manager is running whenever the container runs. Network ordering: a user
manager can't depend on the system `network-online.target`, so the script retries
(curl `--retry 5 --retry-delay 30 --retry-all-errors`) and exits 75. The unit then has
`Restart=on-failure`, `RestartSec=20min`, `RestartPreventExitStatus=1 2`, and a start
limit of 4 per 6 h. `Restart=` on `Type=oneshot` needs systemd ≥ 244; Debian 13 has
257.13. XDG autostart is not a fallback: Crostini runs no desktop session that reads
`~/.config/autostart`. If `systemctl --user` doesn't work, the installer prints a
`~/.profile` one-liner instead (flock stops overlapping runs).

**Flatpak 1.16.6 behaviour (Debian 13 `flatpak 1.16.6-1~deb13u2`, from deb.debian.org
trixie arm64 Packages and sources.debian.org; read from the flatpak 1.16.6 tag source):**
- `flatpak info` has `--show-location/-l`, `--show-origin/-o`; `--user`; location
  printed = deploy dir whose `files/` is `/app` (`app/flatpak-builtins-info.c`).
- `flatpak install` has `--bundle`, `--reinstall`, `--noninteractive`. These combine:
  `install_bundle()` calls `flatpak_transaction_set_reinstall`.
- Origin mismatch doesn't actually error for bundles.
  `flatpak_dir_ensure_bundle_remote()` reuses the *existing deployment's origin* when the
  app is already installed. So a bundle installed over the user's local-repo install
  keeps that local remote as origin. `flatpak update` could then "update" back to a
  newer local build (it refuses an *older* commit: "Update is older than current
  version", checked with 1.14.6). So, if the origin remote has a non-empty URL and no
  other installed ref uses it, the updater runs `flatpak remote-modify --user --disable
  <origin>` and then installs the bundle onto it. A disabled remote is skipped by
  `flatpak update` ("Remote %s disabled, ignoring %s update", `flatpak-transaction.c`;
  checked with 1.14.6: "Nothing to do."), and a bundle installs fine onto a disabled
  origin, even with the old repo directory deleted (checked). A remote shared with other
  refs (e.g. a real repo) is left enabled. Fresh installs get an `orcastudio-origin`
  remote with an empty URL (B's build-bundle passes no `--repo-url`), which flatpak
  lists as disabled.
- **The app is never uninstalled.** An earlier version uninstalled first and, on
  failure, tried to reinstall from the old origin. That cannot work: `flatpak uninstall`
  prunes an unused `*-origin` `noenumerate` remote (the kind `flatpak install ./repo` /
  `flatpak-builder --install` create), so the restore fails with "No remote refs found",
  leaving no app (reproduced with 1.14.6). With `--runtime-repo` in the bundle, every
  `flatpak install --bundle` fetches `flathub.flatpakrepo` first, even when the runtime
  and the flathub remote are already present (reproduced), so a Flathub outage was
  enough to trigger it.
- **Install failures.** flatpak runs with `LC_ALL=C` so its messages can be matched. A
  failed install leaves the installed deployment as it was. Output matching a network
  fetch (`While fetching`, `While pulling`, curl resolve/connect/timeout errors) → exit
  75, which the unit retries (`RestartPreventExitStatus=1 2`); anything else → exit 1.
  `--reinstall --bundle` of the identical commit fails with "<app-id> already installed"
  (1.14.6); if the installed tag then equals the release tag, the updater logs
  "already installed, nothing to do" and exits 0 (relevant for `--force`).
- `flatpak ps --columns=application`, `flatpak remote-list --show-disabled
  --columns=name,url` exist. Non-tty output is tab-separated (`flatpak-table-printer.c`;
  checked live with flatpak 1.14.6 here).

**GitHub release lookup.** `releases/latest` = "most recent non-prerelease, non-draft
release, sorted by created_at", usable without authentication. Unauthenticated limit is
60 requests/h; over the limit gives 403 or 429 with `x-ratelimit-remaining: 0`. The
updater uses 3 API calls per run. Fallback (verified live on rhysd/actionlint):
`/releases/latest/download/<asset>` → 302 to `/releases/download/<tag>/<asset>`.
Release assets expose a GitHub-computed `digest` ("sha256:…") since 2025-06-03; the
updater checks it when present. Integrity only: `SHA256SUMS.txt` comes from the same
release, so it doesn't protect against a compromised repo or token.

**Actions versions**: `actions/checkout@v7` (latest v7.0.1; node24; v6+ stores the
persisted credentials in a separate file under `$RUNNER_TEMP`, and `git push` still works
per its CHANGELOG). Bot identity `41898282+github-actions[bot]@users.noreply.github.com`
is from the checkout README.

## Verification evidence
- `python3 bump-versions.py --self-test`: all checks pass. A live run against both repos
  gives `changed=false` (pins match). Offline `--write` from p3/v2.1.0 pins reproduces the
  current `versions.json` byte for byte. Invalid input gives rc 1.
- actionlint 1.7.12 (release binary, sha256-checked) with shellcheck 0.11.0 on
  `arm-upstream-watch.yml` + `arm-flatpak.yml`: clean.
- `bash -n` + shellcheck 0.11.0 (default severity) on all `chromebook/*.sh`: clean.
  `-o all` leaves only style SC2250 and intentional SC2310/SC2312 notes.
- `systemd-analyze verify` (255) on service + timer: clean. A negative test (typo,
  missing ExecStart) is reported.
- `test-updater-offline.sh`: 48/48 (2026-10-02). Covers fresh install, up to date,
  `--check`, app running, bundle-origin update, URL origin (remote disabled, never
  uninstalled, flatpak run with `LC_ALL=C`), already-disabled origin left alone, shared
  remote left enabled, failed install keeps the old version (exit 1), Flathub fetch
  failure → exit 75 (update and fresh install), `--force` same tag/different commit,
  `--force` identical commit → "already installed, nothing to do" exit 0, digest
  mismatch, SHA256SUMS mismatch, rate-limit
  redirect fallback, 404 no release, disabled workflow, failed last run, non-aarch64,
  malicious tag, BUILD_INFO with CRLF and padding, `*name` sums, duplicate sums,
  python3/jq parsers equal, prerelease rejected.
- `install-updater.sh` run in a stubbed home (aarch64 `uname`, stub `systemctl`/`flatpak`)
  for both systemd-present and absent paths. Its `--check` hit the real API: 404 → "no
  published release yet".

## I need to verify
- I need to verify [whether GITHUB_TOKEN pushes (merge/pin commits) or the daily
  `PUT …/enable` count as "repository activity"] for [the 60-day auto-disable]. The docs
  don't define it. The Chromebook state check is the backstop.
- I need to verify [whether GitHub sends an advance warning email before disabling a
  scheduled workflow] for [early notice]. Only a third-party blog says ~23 days.
- I need to verify [that Actions, and this scheduled workflow in particular, are enabled
  on the fork after the first push] for [daily runs]. Forks start with Actions disabled
  ("I understand my workflows, go ahead and enable them"), and community reports say fork
  schedules can need a separate enable. The `actions/*` API paths are blocked from this
  workspace.
- I need to verify [that a run dispatched or called this way has repository Settings →
  Actions → Workflow permissions allowing write] for [push + release]. Explicit
  `permissions:` in a personal (non-org) repo should be enough, but I couldn't read the
  setting (proxy blocks `actions/permissions`).
- I need to verify [that the unauthenticated `GET /actions/workflows/{file}` and
  `/runs` endpoints answer for this public repo] for [the Chromebook health check]. The
  docs say workflow endpoints work unauthenticated for public resources, but I couldn't
  call them from here. On failure the updater logs a note and carries on.
- I need to verify [that python3 or jq is present in the user's trixie container] for
  [JSON parsing]. Neither is in cros-guest-tools' Depends or Recommends. The installer
  checks and prints `sudo apt install jq`.
- I need to verify [that org.gnome.Platform//50 aarch64 resolves from the user's Flathub
  remote during `--noninteractive` bundle install] for [first install]. B's bundle
  carries `--runtime-repo` (flathub.flatpakrepo). If it can't be fetched or resolved,
  the install fails, the installed version (if any) stays, and a network error exits 75
  for a systemd retry.
- I need to verify [that flatpak 1.16.6 also refuses `--reinstall --bundle` of the
  identical commit] for [the `--force` no-op]. Seen with 1.14.6; the 1.16.6 source
  (`common/flatpak-dir.c`, `flatpak-transaction.c`) still words every such error
  "... already installed", and keeps "Can't load dependent file", "While fetching"
  (`flatpak-utils-http.c`) and "While pulling", so the matching should hold. If 1.16
  simply reinstalls, `--force` succeeds normally. Any unmatched failure is exit 1 with
  the installed version unchanged.
- I need to verify [`notify-send` delivery through cros-notificationd] for [desktop
  alerts]. libnotify-bin isn't installed by default, so the installer only suggests it.
