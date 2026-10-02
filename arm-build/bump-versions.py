#!/usr/bin/env python3
"""Find the newest upstream release tags for arm-build/versions.json.

Stdlib only. Tags are listed with `git ls-remote --tags <url>` (no API token,
no GitHub REST rate limit). Annotated tags are peeled via their `^{}` line so
the recorded commit is always a commit SHA, never a tag-object SHA.

Tag ordering (decided from the real tag lists, see SELF_TEST_FIXTURES):
  * jarczakpawel/OrcaStudio uses  vAA.BB.CC.DD  and  vAA.BB.CC.DD-pN
    "-pN" is a *post-release patch* (all published as normal, non-prerelease
    GitHub releases), so  vX < vX-p1 < vX-p2 < ... < next vY.
  * ClusterM/open-bamboo-networking uses  vA.B.C.
  Accepted shape: ^v<int>(.<int>)*(-p<int>)?$ ; key = (numeric parts, N or 0).
  Anything else (rc/beta/alpha/dev/arbitrary suffix) is ignored and reported,
  so a future "v3.0.0-rc1" can never be auto-selected.

Usage:
  bump-versions.py [--versions FILE] [--write] [--tags-file NAME=FILE ...]
  bump-versions.py --self-test

Outputs (stdout, and appended to $GITHUB_OUTPUT when that env var is set):
  changed=true|false
  <name>_repo, <name>_changed, <name>_tag, <name>_commit, <name>_prev_tag,
  <name>_prev_commit
  for every top-level entry of versions.json (e.g. orcastudio_*, obn_*).
Exit codes: 0 ok, 1 runtime error (network/git/invalid data), 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time

TAG_RE = re.compile(r"^v(?P<nums>\d+(?:\.\d+)*)(?:-p(?P<patch>\d+))?$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class BumpError(Exception):
    pass


# ---------------------------------------------------------------- ordering --
def tag_key(tag: str):
    """Sort key for an accepted release tag, or None if the tag is ignored."""
    m = TAG_RE.match(tag)
    if not m:
        return None
    nums = tuple(int(x) for x in m.group("nums").split("."))
    patch = int(m.group("patch")) if m.group("patch") is not None else 0
    return (nums, patch)


def _cmp_key(key):
    # Pad numeric parts so v1.2 == v1.2.0 compares sanely; patch compares last.
    nums, patch = key
    return (nums + (0,) * (8 - len(nums)), patch)


def latest_tag(tags):
    """Return (best_tag, ignored_tags) from an iterable of tag names."""
    accepted, ignored = [], []
    for t in tags:
        (accepted if tag_key(t) is not None else ignored).append(t)
    if not accepted:
        return None, sorted(ignored)
    best = max(accepted, key=lambda t: (_cmp_key(tag_key(t)), t))
    return best, sorted(ignored)


# ------------------------------------------------------------- ls-remote ---
def parse_ls_remote(text: str) -> dict:
    """Map tag name -> commit SHA (annotated tags peeled via ^{} lines)."""
    direct, peeled = {}, {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            raise BumpError(f"unexpected ls-remote line: {line!r}")
        sha, ref = parts
        if not SHA_RE.match(sha):
            raise BumpError(f"bad SHA in ls-remote line: {line!r}")
        if not ref.startswith("refs/tags/"):
            continue
        name = ref[len("refs/tags/"):]
        if name.endswith("^{}"):
            peeled[name[:-3]] = sha
        else:
            direct[name] = sha
    # peeled wins: for annotated tags the direct SHA is the tag object.
    return {name: peeled.get(name, sha) for name, sha in direct.items()}


def ls_remote(repo: str, attempts: int = 3) -> str:
    url = f"https://github.com/{repo}.git"
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    last = ""
    for i in range(1, attempts + 1):
        try:
            p = subprocess.run(
                ["git", "ls-remote", "--tags", url],
                capture_output=True, text=True, timeout=120, env=env, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            last = str(e)
        else:
            if p.returncode == 0:
                return p.stdout
            last = p.stderr.strip()
        if i < attempts:
            time.sleep(10 * i)
    raise BumpError(f"git ls-remote failed for {url} after {attempts} attempts: {last}")


# ------------------------------------------------------------- versions ----
def load_versions(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not data:
        raise BumpError(f"{path}: top level must be a non-empty object")
    for name, entry in data.items():
        if not re.match(r"^[a-z][a-z0-9_]*$", name):
            raise BumpError(f"{path}: entry name {name!r} must match [a-z][a-z0-9_]*")
        for k in ("repo", "tag", "commit"):
            if not isinstance(entry.get(k), str):
                raise BumpError(f"{path}: {name}.{k} missing or not a string")
        if not REPO_RE.match(entry["repo"]):
            raise BumpError(f"{path}: {name}.repo {entry['repo']!r} is not owner/name")
        if not SHA_RE.match(entry["commit"]):
            raise BumpError(f"{path}: {name}.commit is not a 40-hex SHA")
    return data


def dump_versions(data: dict) -> str:
    # Same layout as the hand-written file: one entry per line.
    lines = [f"  {json.dumps(k)}: {json.dumps(v)}" for k, v in data.items()]
    return "{\n" + ",\n".join(lines) + "\n}\n"


def write_atomic(path: str, text: str) -> None:
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".versions.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def evaluate(entry: dict, tag_map: dict, name: str, log) -> dict:
    """Decide the new tag/commit for one entry. Never downgrades."""
    cur_tag, cur_commit = entry["tag"], entry["commit"]
    best, ignored = latest_tag(tag_map)
    if ignored:
        log(f"{name}: ignored non-release tag shapes: {', '.join(ignored)}")
    if best is None:
        raise BumpError(f"{name}: no release-shaped tags found in {entry['repo']}")
    new_tag, new_commit = cur_tag, cur_commit
    cur_key = tag_key(cur_tag)
    if cur_key is None:
        raise BumpError(f"{name}: current tag {cur_tag!r} does not match the release tag shape")
    if cur_tag not in tag_map:
        log(f"{name}: WARNING current tag {cur_tag} no longer exists upstream")
    if _cmp_key(tag_key(best)) > _cmp_key(cur_key):
        new_tag, new_commit = best, tag_map[best]
    elif best == cur_tag and tag_map[best] != cur_commit:
        # Upstream force-moved the tag. Follow it, loudly.
        log(f"{name}: WARNING tag {cur_tag} moved {cur_commit} -> {tag_map[best]}")
        new_commit = tag_map[best]
    elif _cmp_key(tag_key(best)) < _cmp_key(cur_key):
        log(f"{name}: WARNING upstream newest {best} sorts below pinned {cur_tag}; keeping pin")
    return {
        "repo": entry["repo"],
        "changed": (new_tag, new_commit) != (cur_tag, cur_commit),
        "tag": new_tag, "commit": new_commit,
        "prev_tag": cur_tag, "prev_commit": cur_commit,
    }


def emit_outputs(results: dict) -> list:
    out = [f"changed={'true' if any(r['changed'] for r in results.values()) else 'false'}"]
    for name, r in results.items():
        out += [
            f"{name}_repo={r['repo']}",
            f"{name}_changed={'true' if r['changed'] else 'false'}",
            f"{name}_tag={r['tag']}",
            f"{name}_commit={r['commit']}",
            f"{name}_prev_tag={r['prev_tag']}",
            f"{name}_prev_commit={r['prev_commit']}",
        ]
    for line in out:  # values come from TAG_RE / SHA_RE validated data: no newlines
        assert "\n" not in line and "\r" not in line
    return out


def run(args) -> int:
    log = lambda msg: print(msg, file=sys.stderr)  # noqa: E731
    data = load_versions(args.versions)
    tag_files = {}
    for spec in args.tags_file or []:
        name, sep, path = spec.partition("=")
        if not sep:
            raise BumpError(f"--tags-file expects NAME=FILE, got {spec!r}")
        tag_files[name] = path
    results = {}
    for name, entry in data.items():
        if name in tag_files:
            with open(tag_files[name], encoding="utf-8") as f:
                text = f.read()
        else:
            text = ls_remote(entry["repo"])
        tag_map = parse_ls_remote(text)
        results[name] = evaluate(entry, tag_map, name, log)
        r = results[name]
        log(f"{name}: {entry['repo']} pinned {r['prev_tag']} -> newest {r['tag']} "
            f"({'CHANGED' if r['changed'] else 'unchanged'})")
    if args.write and any(r["changed"] for r in results.values()):
        for name, r in results.items():
            data[name]["tag"], data[name]["commit"] = r["tag"], r["commit"]
        write_atomic(args.versions, dump_versions(data))
        log(f"wrote {args.versions}")
    lines = emit_outputs(results)
    print("\n".join(lines))
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    return 0


# -------------------------------------------------------------- self-test --
# Real `git ls-remote --tags` output captured 2026-10-02.
SELF_TEST_FIXTURES = {
    "orcastudio": """\
7426e3c43349461b6e978648ecd8bb8ed0a2ebcf\trefs/tags/v02.07.01.57
bd81360eef328c707e16f7a723826355c2d2008d\trefs/tags/v02.07.01.57^{}
967f5938c118f8a264a449e5bf49a9ffabad19fd\trefs/tags/v02.07.01.57-p1
223675e357a80e5549b0fc466b1e3a868667a5ea\trefs/tags/v02.07.01.57-p1^{}
39816c34c86109daae24092ebd84c8f930a348c7\trefs/tags/v02.07.01.57-p2
846e1b182912a961ab5e388711e801ec296d2c5e\trefs/tags/v02.07.01.57-p2^{}
2c665af2cd933cb4877e6682fadd4f1910b1a31c\trefs/tags/v02.07.01.57-p3
58273a1c760815f020e1fc3956b02176a5f7c244\trefs/tags/v02.07.01.57-p3^{}
929d9a07c17458a607aaa0cb458cf4b5a1ffa824\trefs/tags/v02.07.01.57-p4
aadcad4ee429e45ef8624d0564a056fa1ef21941\trefs/tags/v02.07.01.57-p4^{}
118f6ff2d6e0394caca415c12be0d00f546afa0e\trefs/tags/v02.07.01.57-p5
8c219a35cd837fe6ac188323b83ad3c1bdf16489\trefs/tags/v02.07.01.57-p5^{}
2dcd7fabc8d98c652a71446459185dbe658a1c24\trefs/tags/v02.08.01.55
831f5a4ac03bd9da800533be027ff65eb1ae51c3\trefs/tags/v02.08.01.55^{}
2c3a5131c4fe569e7d1299cfd825350db8524cb0\trefs/tags/v02.08.01.55-p1
1da8e0e65161a2b8f3184b4f9d8cd3d74848e80a\trefs/tags/v02.08.01.55-p2
7dad246c7f8ba7b4f52107948d07b84c178dcd90\trefs/tags/v02.08.01.55-p3
d6576af0462831ce2938d0264b2b7697c3869803\trefs/tags/v02.08.01.55-p3^{}
e5d4354336109f829f2fec7a839911f9beae4fc2\trefs/tags/v02.08.01.55-p4
596413d0094e97c92724174dc075a9c3ea8df7a3\trefs/tags/v02.08.01.55-p5
bef044f40bb957bd0967378705fc24ae20655c45\trefs/tags/v02.08.01.55-p6
""",
    "obn": """\
fdd36080b73f7b7c5b8ff7bc87881166bed79f9a\trefs/tags/v1.0.0
ae98a374eae81d641d37cf01aa7b2e5a7c44bf4c\trefs/tags/v1.1.0
b2f956b3c0e6cb595ed2e1e236386331914d3134\trefs/tags/v2.0.0
84561aa23afdb393b920862b0fd9fd2a2e915fe2\trefs/tags/v2.0.1
01917237efd75c757f4a2a2a73f3690f0ef9e1a8\trefs/tags/v2.1.0
5e6a359c71a0c07476f5d372bf7ad0f2b43efe94\trefs/tags/v2.2.0
""",
}


def self_test() -> int:
    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    orca = parse_ls_remote(SELF_TEST_FIXTURES["orcastudio"])
    obn = parse_ls_remote(SELF_TEST_FIXTURES["obn"])
    # peeling: annotated -> ^{} commit, lightweight -> direct SHA
    check(orca["v02.07.01.57"] == "bd81360eef328c707e16f7a723826355c2d2008d", "peel annotated")
    check(orca["v02.08.01.55-p6"] == "bef044f40bb957bd0967378705fc24ae20655c45", "lightweight")
    check(len(orca) == 13 and len(obn) == 6, f"tag counts {len(orca)} {len(obn)}")
    # full expected order of the real OrcaStudio list
    expected = ["v02.07.01.57"] + [f"v02.07.01.57-p{i}" for i in range(1, 6)] + \
               ["v02.08.01.55"] + [f"v02.08.01.55-p{i}" for i in range(1, 7)]
    got = sorted(orca, key=lambda t: _cmp_key(tag_key(t)))
    check(got == expected, f"orca order {got}")
    # lexical sort would be wrong for p10 vs p9 -> numeric
    check(latest_tag(list(orca) + ["v02.08.01.55-p10"])[0] == "v02.08.01.55-p10", "p10 > p9")
    check(latest_tag(["v02.08.01.55-p9", "v02.08.01.55-p10"])[0] == "v02.08.01.55-p10", "p10>p9 b")
    check(latest_tag(list(orca) + ["v02.09.00.10"])[0] == "v02.09.00.10", "new base beats -pN")
    check(latest_tag(list(orca) + ["v02.10.00.01"])[0] == "v02.10.00.01", "02.10 > 02.09 numeric")
    best, ign = latest_tag(list(orca) + ["v02.09.00.10-rc1", "v02.09.00.10-beta", "nightly"])
    check(best == "v02.08.01.55-p6" and len(ign) == 3, f"prerelease ignored {best} {ign}")
    check(latest_tag(obn)[0] == "v2.2.0", "obn latest")
    check(latest_tag(list(obn) + ["v2.10.0"])[0] == "v2.10.0", "obn 2.10 > 2.2")
    check(latest_tag(list(obn) + ["v3.0.0-rc1"])[0] == "v2.2.0", "obn rc ignored")
    # evaluate(): against the lead's initial pins -> unchanged
    nolog = lambda m: None  # noqa: E731
    pin_o = {"repo": "jarczakpawel/OrcaStudio", "tag": "v02.08.01.55-p6",
             "commit": "bef044f40bb957bd0967378705fc24ae20655c45"}
    pin_b = {"repo": "ClusterM/open-bamboo-networking", "tag": "v2.2.0",
             "commit": "5e6a359c71a0c07476f5d372bf7ad0f2b43efe94"}
    check(not evaluate(pin_o, orca, "o", nolog)["changed"], "orca unchanged")
    check(not evaluate(pin_b, obn, "b", nolog)["changed"], "obn unchanged")
    # older pin -> bumps to newest
    r = evaluate(dict(pin_o, tag="v02.08.01.55-p3", commit="d" * 40), orca, "o", nolog)
    check(r["changed"] and r["tag"] == "v02.08.01.55-p6" and r["prev_tag"] == "v02.08.01.55-p3",
          f"bump {r}")
    # moved tag -> changed, same tag
    r = evaluate(dict(pin_o, commit="a" * 40), orca, "o", nolog)
    check(r["changed"] and r["tag"] == pin_o["tag"], "moved tag")
    # never downgrade
    r = evaluate(dict(pin_b, tag="v9.0.0"), obn, "b", nolog)
    check(not r["changed"] and r["tag"] == "v9.0.0", "no downgrade")
    # outputs format
    outs = emit_outputs({"orcastudio": evaluate(pin_o, orca, "o", nolog),
                         "obn": evaluate(dict(pin_b, tag="v2.1.0"), obn, "b", nolog)})
    check("changed=true" in outs and "obn_changed=true" in outs
          and "orcastudio_changed=false" in outs and "obn_tag=v2.2.0" in outs, f"outputs {outs}")
    # round-trip of the lead's file layout
    src = ('{\n  "orcastudio": {"repo": "jarczakpawel/OrcaStudio", "tag": "v02.08.01.55-p6", '
           '"commit": "bef044f40bb957bd0967378705fc24ae20655c45"},\n  "obn": {"repo": '
           '"ClusterM/open-bamboo-networking", "tag": "v2.2.0", "commit": '
           '"5e6a359c71a0c07476f5d372bf7ad0f2b43efe94"}\n}\n')
    check(dump_versions(json.loads(src)) == src, "dump layout round-trip")
    for bad in ["foo\tbar\tbaz", "zzzz\trefs/tags/v1"]:
        try:
            parse_ls_remote(bad)
            fails.append(f"bad line accepted: {bad!r}")
        except BumpError:
            pass
    if fails:
        for f in fails:
            print(f"SELF-TEST FAIL: {f}", file=sys.stderr)
        return 1
    print("self-test: all checks passed")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--versions", default=os.path.join(here, "versions.json"))
    ap.add_argument("--write", action="store_true", help="rewrite versions.json if changed")
    ap.add_argument("--tags-file", action="append", metavar="NAME=FILE",
                    help="use saved ls-remote output for entry NAME (offline testing)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    try:
        return run(args)
    except (BumpError, OSError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
