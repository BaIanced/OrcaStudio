#!/usr/bin/env python3
"""Generate the aarch64 OrcaStudio Flatpak manifest (com.orcaslicer.OrcaStudio.arm.yml).

Inputs (paths default relative to the repository root = parent of this script's dir):
  scripts/flatpak/com.orcaslicer.OrcaStudio.yml   upstream manifest (never modified)
  arm-build/versions.json                          pinned orcastudio/obn tags + commits
  arm-build/obn-module.yml                         obn module(s), with @OBN_TAG@/@OBN_COMMIT@
Output:
  scripts/flatpak/com.orcaslicer.OrcaStudio.arm.yml (same directory as the upstream
  manifest, so every relative `path:` in upstream and obn-module.yml stays valid).

Always-applied transformations (semantic changes):
  a) orca_deps: add the FFmpeg source archive (URL + SHA256 parsed from
     deps/FFMPEG/FFMPEG.cmake) right after the CPython source, unless already present.
  b) append the obn module(s) after the OrcaStudio module, placeholders substituted.
  c) command: orcastudio-arm-launcher; a final module rewrites the desktop file
     Exec to "orcastudio-arm-launcher %U" (upstream's post-install sets "entrypoint %U").
  d) final module "orcastudio-arm-integration" writes /app/share/orcastudio-arm/BUILD_INFO.
Optional CI-resource transformations (do not change what the app does):
  --jobs N          cap orca_deps parallelism (top-level `cmake --build --parallel`
                    is otherwise unbounded `make -j`; see arm-build/NOTES-ci.md).
  --no-debug-info   append -g0, set no-debuginfo + strip (no .Debug extension).
  --ccache-launcher use ccache for the OrcaStudio module (CMake compiler launcher).

YAML handling: PyYAML with a loader/dumper whose implicit scalar typing matches
flatpak-builder's own YAML->JSON conversion (src/builder-utils.c
parse_yaml_node_to_json): only true/True/TRUE/false/False/FALSE are booleans,
null/Null/NULL is null, base-10 integers are ints, everything else is a string.
Stock PyYAML (YAML 1.1) would turn `on`/`yes` into booleans and `0755` into octal.

Exit codes: 0 ok, 2 anchor/validation failure (upstream changed or bad input), 3 missing tool.
"""

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "make-manifest: ERROR: PyYAML is required (Debian/Ubuntu: apt-get install python3-yaml)\n")
    sys.exit(3)

APP_ID = "com.orcaslicer.OrcaStudio"
UPSTREAM_REL = "scripts/flatpak/com.orcaslicer.OrcaStudio.yml"
OUTPUT_REL = "scripts/flatpak/com.orcaslicer.OrcaStudio.arm.yml"
VERSIONS_REL = "arm-build/versions.json"
OBN_REL = "arm-build/obn-module.yml"
FFMPEG_CMAKE_REL = "deps/FFMPEG/FFMPEG.cmake"

APP_MODULE = "OrcaStudio"
DEPS_MODULE = "orca_deps"
PY_DEST = "external-packages/python3"
FFMPEG_DEST = "external-packages/FFMPEG"
LAUNCHER = "orcastudio-arm-launcher"
INTEGRATION_MODULE = "orcastudio-arm-integration"
BUILD_INFO_PATH = "/app/share/orcastudio-arm/BUILD_INFO"
DEPS_BUILD_CMD_RE = re.compile(r"^cmake --build \$BUILD_DIR --parallel\s*$")
TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
DEPS_KEY_SCHEMA = "orcastudio-arm-deps-v1"


class AnchorError(Exception):
    """An assumption about the upstream manifest / inputs no longer holds."""


def fail(msg):
    raise AnchorError(msg)


# --------------------------------------------------------------------------
# flatpak-builder-compatible YAML
# --------------------------------------------------------------------------
_BOOL_RE = re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$")
_NULL_RE = re.compile(r"^(?:null|Null|NULL)$")
_INT_RE = re.compile(r"^[-+]?[0-9]+$")


def _install_resolvers(cls):
    cls.yaml_implicit_resolvers = {}
    cls.add_implicit_resolver("tag:yaml.org,2002:bool", _BOOL_RE, list("tTfF"))
    cls.add_implicit_resolver("tag:yaml.org,2002:null", _NULL_RE, list("nN"))
    cls.add_implicit_resolver("tag:yaml.org,2002:int", _INT_RE, list("-+0123456789"))


class FBLoader(yaml.SafeLoader):
    pass


class FBDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):  # libyaml in flatpak-builder resolves aliases, but keep output plain
        return True


_install_resolvers(FBLoader)
_install_resolvers(FBDumper)


def _construct_int(loader, node):
    return int(loader.construct_scalar(node), 10)  # base 10 like g_ascii_strtoll(.., 10)


def _construct_bool(loader, node):
    return loader.construct_scalar(node).lower() == "true"


def _no_duplicate_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, "duplicate key %r" % (key,), key_node.start_mark)
        seen.add(key)
    return loader.construct_mapping(node, deep=deep)


FBLoader.add_constructor("tag:yaml.org,2002:int", _construct_int)
FBLoader.add_constructor("tag:yaml.org,2002:bool", _construct_bool)
FBLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicate_mapping)


_YAML11 = yaml.resolver.Resolver()


def _repr_str(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    # Quote strings any YAML 1.1 parser would type (3.5, yes, on, ~, dates) so the output
    # reads the same everywhere and flatpak-builder does not warn about "3.5".
    if _YAML11.resolve(yaml.ScalarNode, data, (True, False)) != "tag:yaml.org,2002:str":
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


FBDumper.add_representer(str, _repr_str)


def load_yaml_text(text, what):
    if re.search(r"^\s*<<\s*:", text, re.M):
        fail("%s uses YAML merge keys (<<:), which flatpak-builder does not support" % what)
    try:
        return yaml.load(text, Loader=FBLoader)  # noqa: S506 - FBLoader is a SafeLoader subclass
    except yaml.YAMLError as exc:
        fail("%s is not valid YAML: %s" % (what, exc))


def dump_yaml(data):
    return yaml.dump(data, Dumper=FBDumper, sort_keys=False, default_flow_style=False,
                     allow_unicode=True, width=4096, indent=2)


# --------------------------------------------------------------------------
# inputs
# --------------------------------------------------------------------------
def read_text(path, what):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        fail("cannot read %s (%s): %s" % (what, path, exc.strerror))


def load_versions(path):
    try:
        data = json.loads(read_text(path, "versions.json"))
    except json.JSONDecodeError as exc:
        fail("versions.json is not valid JSON: %s" % exc)
    for comp in ("orcastudio", "obn"):
        ent = data.get(comp)
        if not isinstance(ent, dict):
            fail("versions.json: missing object %r" % comp)
        for field in ("repo", "tag", "commit"):
            if not isinstance(ent.get(field), str) or not ent[field]:
                fail("versions.json: %s.%s missing or not a string" % (comp, field))
        if not TAG_RE.match(ent["tag"]):
            fail("versions.json: %s.tag %r has unexpected characters" % (comp, ent["tag"]))
        if not SHA1_RE.match(ent["commit"]):
            fail("versions.json: %s.commit %r is not a 40-hex commit id" % (comp, ent["commit"]))
    return data


def ffmpeg_source_from_cmake(path):
    """Return (url, sha256) of the non-MSVC FFmpeg ExternalProject in deps/FFMPEG/FFMPEG.cmake."""
    text = read_text(path, "FFMPEG.cmake")
    pairs = re.findall(r"URL\s+(https://github\.com/FFmpeg/FFmpeg/\S+)\s+URL_HASH\s+SHA256=([0-9A-Fa-f]{64})",
                       text)
    if len(pairs) != 1:
        fail("%s: expected exactly one 'URL https://github.com/FFmpeg/FFmpeg/... URL_HASH SHA256=...' "
             "pair, found %d" % (path, len(pairs)))
    return pairs[0][0], pairs[0][1].lower()


def load_obn_modules(path, versions):
    text = read_text(path, "obn-module.yml")
    for ph in ("@OBN_TAG@", "@OBN_COMMIT@"):
        if ph not in text:
            fail("obn-module.yml: placeholder %s not found (contract: source pinned with "
                 "@OBN_TAG@ and @OBN_COMMIT@)" % ph)
    text = text.replace("@OBN_TAG@", versions["obn"]["tag"]).replace("@OBN_COMMIT@",
                                                                       versions["obn"]["commit"])
    left = re.findall(r"@[A-Z][A-Z0-9_]*@", text)
    if left:
        fail("obn-module.yml: unsubstituted placeholders remain: %s" % ", ".join(sorted(set(left))))
    data = load_yaml_text(text, "obn-module.yml")
    if isinstance(data, dict) and "modules" in data and "name" not in data:
        data = data["modules"]
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        fail("obn-module.yml: expected a module mapping, a list of modules, or {modules: [...]}")
    for mod in data:
        if not isinstance(mod, dict) or not isinstance(mod.get("name"), str):
            fail("obn-module.yml: every module must be a mapping with a string 'name'")
    if LAUNCHER not in json.dumps(data):
        fail("obn-module.yml: no module mentions %r; the manifest command depends on a module "
             "installing /app/bin/%s" % (LAUNCHER, LAUNCHER))
    return data


# --------------------------------------------------------------------------
# transformations
# --------------------------------------------------------------------------
def find_module(modules, name):
    idx = [i for i, m in enumerate(modules) if isinstance(m, dict) and m.get("name") == name]
    if len(idx) != 1:
        fail("upstream manifest: expected exactly one top-level module named %r, found %d"
             % (name, len(idx)))
    return idx[0]


def ensure_env(mod):
    bo = mod.setdefault("build-options", {})
    if not isinstance(bo, dict):
        fail("module %r: build-options is not a mapping" % mod.get("name"))
    env = bo.setdefault("env", {})
    if not isinstance(env, dict):
        fail("module %r: build-options.env is not a mapping" % mod.get("name"))
    return bo, env


def add_ffmpeg_source(deps_mod, url, sha256):
    sources = deps_mod.get("sources")
    if not isinstance(sources, list):
        fail("module orca_deps: 'sources' is not a list")
    existing = [s for s in sources if isinstance(s, dict) and s.get("dest") == FFMPEG_DEST]
    if existing:
        if len(existing) == 1 and existing[0].get("url") == url and existing[0].get("sha256") == sha256:
            return "already present (upstream carries it)"
        fail("orca_deps already has a source with dest %s but it does not match FFMPEG.cmake "
             "(%s / %s); reconcile manually" % (FFMPEG_DEST, url, sha256))
    py = [i for i, s in enumerate(sources) if isinstance(s, dict) and s.get("dest") == PY_DEST]
    if len(py) != 1:
        fail("orca_deps: expected exactly one source with dest %s (FFmpeg insertion anchor), "
             "found %d" % (PY_DEST, len(py)))
    sources.insert(py[0] + 1, {"type": "file", "url": url, "sha256": sha256, "dest": FFMPEG_DEST})
    return "inserted after %s" % PY_DEST


def cap_deps_parallelism(deps_mod, jobs):
    cmds = deps_mod.get("build-commands")
    if not isinstance(cmds, list):
        fail("orca_deps: build-commands is not a list")
    hits = [i for i, c in enumerate(cmds) if isinstance(c, str) and DEPS_BUILD_CMD_RE.match(c)]
    if len(hits) != 1:
        fail("orca_deps: expected exactly one build command 'cmake --build $BUILD_DIR --parallel' "
             "(parallelism cap anchor), found %d" % len(hits))
    top = max(1, jobs // 2)
    cmds[hits[0]] = "cmake --build $BUILD_DIR --parallel %d" % top
    _, env = ensure_env(deps_mod)
    for k in ("CMAKE_BUILD_PARALLEL_LEVEL", "MAKEFLAGS"):
        if k in env:
            fail("orca_deps: build-options.env already sets %s; review the parallelism cap" % k)
    # Per-dependency builds (deps/CMakeLists.txt _build_j, FFMPEG.cmake) honour this.
    env["CMAKE_BUILD_PARALLEL_LEVEL"] = str(jobs)
    # Bounds the unbounded `make -j` used by GMP/MPFR (GNU make >= 4.4 reads /proc/loadavg).
    env["MAKEFLAGS"] = "-l%d" % (jobs + 2)
    return top


def append_flag(bo, key, flag):
    cur = bo.get(key)
    if cur is None:
        bo[key] = flag
    elif isinstance(cur, str):
        bo[key] = (cur + " " + flag).strip()
    else:
        fail("build-options.%s is not a string" % key)


def no_debug_info(manifest):
    bo = manifest.setdefault("build-options", {})
    if not isinstance(bo, dict):
        fail("top-level build-options is not a mapping")
    for key in ("cflags-override", "cxxflags-override"):
        if bo.get(key):
            fail("top-level build-options.%s is set; -g0 append would be ambiguous" % key)
    append_flag(bo, "cflags", "-g0")
    append_flag(bo, "cxxflags", "-g0")
    bo["no-debuginfo"] = True
    bo["strip"] = True


def ccache_launcher(app_mod):
    bo, env = ensure_env(app_mod)
    env["CMAKE_C_COMPILER_LAUNCHER"] = "ccache"
    env["CMAKE_CXX_COMPILER_LAUNCHER"] = "ccache"
    # CMake's clang PCH lacks -fno-pch-timestamp; ccache needs it to cache PCH users.
    append_flag(bo, "cflags", "-Xclang -fno-pch-timestamp")
    append_flag(bo, "cxxflags", "-Xclang -fno-pch-timestamp")


def integration_module(versions, release_tag):
    info = ("orcastudio_tag=%s\nobn_tag=%s\nrelease_tag=%s\n"
            % (versions["orcastudio"]["tag"], versions["obn"]["tag"], release_tag))
    for line in info.splitlines():
        if "'" in line or "\\" in line:
            fail("BUILD_INFO value contains a quote/backslash: %r" % line)
    return {
        "name": INTEGRATION_MODULE,
        "buildsystem": "simple",
        "build-commands": [
            "test -x /app/bin/%s || { echo 'ERROR: /app/bin/%s missing (obn-module.yml must "
            "install it)' >&2; exit 1; }" % (LAUNCHER, LAUNCHER),
            "test -x /app/bin/entrypoint || { echo 'ERROR: /app/bin/entrypoint missing' >&2; exit 1; }",
            "desktop-file-edit --set-key=Exec --set-value=\"%s %%U\" "
            "/app/share/applications/${FLATPAK_ID}.desktop" % LAUNCHER,
            "grep -qx 'Exec=%s %%U' /app/share/applications/${FLATPAK_ID}.desktop" % LAUNCHER,
            "install -d /app/share/orcastudio-arm",
            "printf '%%s' '%s' > %s" % (info, BUILD_INFO_PATH),
            "cat %s" % BUILD_INFO_PATH,
        ],
    }


def generate(upstream, versions, obn_modules, ffmpeg, release_tag, opts):
    m = copy.deepcopy(upstream)
    if not isinstance(m, dict):
        fail("upstream manifest is not a mapping")
    if m.get("app-id", m.get("id")) != APP_ID:
        fail("upstream manifest app-id is %r, expected %r" % (m.get("app-id", m.get("id")), APP_ID))
    if m.get("command") != "entrypoint":
        fail("upstream manifest command is %r, expected 'entrypoint' (launcher execs /app/bin/entrypoint)"
             % m.get("command"))
    modules = m.get("modules")
    if not isinstance(modules, list):
        fail("upstream manifest has no top-level 'modules' list")
    for mod in modules:
        if isinstance(mod, str):
            fail("upstream manifest references an external module file %r; inline modules only "
                 "are supported (paths would need rebasing)" % mod)
    app_idx = find_module(modules, APP_MODULE)
    deps_idx = find_module(modules, DEPS_MODULE)
    if deps_idx > app_idx:
        fail("orca_deps is after OrcaStudio in upstream manifest; deps/app job split assumes before")
    if app_idx != len(modules) - 1:
        fail("OrcaStudio is not the last upstream module; review where obn modules must go")
    app = modules[app_idx]
    post = app.get("post-install")
    if not (isinstance(post, list) and any(isinstance(c, str) and "desktop-file-edit" in c
                                            and "entrypoint %U" in c for c in post)):
        fail("OrcaStudio post-install no longer sets Exec=\"entrypoint %U\" via desktop-file-edit")
    names = {mm.get("name") for mm in modules if isinstance(mm, dict)}
    for om in obn_modules:
        if om["name"] in names or om["name"] == INTEGRATION_MODULE:
            fail("obn-module.yml module name %r collides with an upstream module" % om["name"])

    report = {}
    report["ffmpeg"] = add_ffmpeg_source(modules[deps_idx], ffmpeg[0], ffmpeg[1])
    if opts.jobs:
        report["deps_top_parallel"] = cap_deps_parallelism(modules[deps_idx], opts.jobs)
    if opts.no_debug_info:
        no_debug_info(m)
    if opts.ccache_launcher:
        ccache_launcher(app)
    m["command"] = LAUNCHER
    modules.extend(copy.deepcopy(obn_modules))
    modules.append(integration_module(versions, release_tag))
    return m, app_idx, report


# --------------------------------------------------------------------------
# deps cache key
# --------------------------------------------------------------------------
_KEY_TOPLEVEL = ("app-id", "id", "runtime", "runtime-version", "sdk", "sdk-extensions",
                 "build-options", "separate-locales", "base", "base-version", "base-extensions",
                 "var", "metadata", "tags", "writable-sdk", "build-runtime", "build-extension")


def _hash_path(h, path, rel):
    if os.path.islink(path):
        h.update(b"L" + rel.encode() + b"\0" + os.readlink(path).encode() + b"\0")
    elif os.path.isdir(path):
        h.update(b"D" + rel.encode() + b"\0")
        for name in sorted(os.listdir(path)):
            _hash_path(h, os.path.join(path, name), rel + "/" + name)
    elif os.path.isfile(path):
        h.update(b"F" + rel.encode() + b"\0" + (b"x" if os.access(path, os.X_OK) else b"-"))
        with open(path, "rb") as fh:
            h.update(hashlib.sha256(fh.read()).digest())
    else:
        fail("deps key: local source path %s does not exist" % path)


def deps_key(manifest, app_idx, manifest_dir):
    """sha256 over everything flatpak-builder uses for the modules before OrcaStudio."""
    pre = manifest["modules"][:app_idx]
    doc = {"schema": DEPS_KEY_SCHEMA,
           "top": {k: manifest[k] for k in _KEY_TOPLEVEL if k in manifest},
           "modules": pre}
    h = hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode())

    def walk(mods):
        for mod in mods:
            for src in mod.get("sources", []) or []:
                if isinstance(src, dict) and "path" in src and src.get("type") in ("dir", "file", "patch",
                                                                                   "script", "shell"):
                    p = os.path.normpath(os.path.join(manifest_dir, src["path"]))
                    _hash_path(h, p, src["path"])
                elif isinstance(src, dict) and src.get("paths"):
                    for sp in src["paths"]:
                        _hash_path(h, os.path.normpath(os.path.join(manifest_dir, sp)), sp)
            walk(mod.get("modules", []) or [])

    walk(pre)
    return h.hexdigest()


# --------------------------------------------------------------------------
# verification helpers
# --------------------------------------------------------------------------
def roundtrip_check(text, data):
    again = load_yaml_text(text, "generated manifest")
    if json.dumps(again, sort_keys=True) != json.dumps(data, sort_keys=True):
        fail("internal: generated YAML does not round-trip to the same data")


def show_manifest(path):
    exe = shutil.which("flatpak-builder")
    if not exe:
        return None
    res = subprocess.run([exe, "--show-manifest", path], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, universal_newlines=True, check=False)
    if res.returncode != 0:
        fail("flatpak-builder --show-manifest rejected %s:\n%s" % (path, res.stderr.strip()))
    return json.loads(res.stdout)


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo-root", default=os.path.dirname(here),
                    help="OrcaStudio source tree root (default: parent of arm-build/)")
    ap.add_argument("--upstream", help="upstream manifest (default: <root>/%s)" % UPSTREAM_REL)
    ap.add_argument("--versions", help="versions.json (default: <root>/%s)" % VERSIONS_REL)
    ap.add_argument("--obn-module", help="obn module YAML (default: <root>/%s)" % OBN_REL)
    ap.add_argument("--output", help="output manifest (default: <root>/%s)" % OUTPUT_REL)
    ap.add_argument("--release-tag", default=os.environ.get("RELEASE_TAG", ""),
                    help="release tag written to BUILD_INFO (default: $RELEASE_TAG)")
    ap.add_argument("--jobs", type=int, default=0,
                    help="cap orca_deps parallelism to N jobs per dependency (0 = upstream behaviour)")
    ap.add_argument("--no-debug-info", action="store_true", help="-g0 + no-debuginfo + strip")
    ap.add_argument("--ccache-launcher", action="store_true",
                    help="ccache as CMake compiler launcher for the OrcaStudio module")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true",
                      help="validate inputs/anchors and the result; write nothing")
    mode.add_argument("--print-deps-key", action="store_true",
                      help="print the sha256 cache key of everything before the OrcaStudio module")
    a = ap.parse_args(argv)

    root = os.path.abspath(a.repo_root)
    upstream_path = a.upstream or os.path.join(root, UPSTREAM_REL)
    versions_path = a.versions or os.path.join(root, VERSIONS_REL)
    obn_path = a.obn_module or os.path.join(root, OBN_REL)
    out_path = a.output or os.path.join(root, OUTPUT_REL)
    if os.path.dirname(os.path.abspath(out_path)) != os.path.dirname(os.path.abspath(upstream_path)):
        fail("--output must be in the same directory as the upstream manifest (relative source paths)")
    if a.jobs < 0:
        fail("--jobs must be >= 0")

    release_tag = a.release_tag
    if not release_tag:
        if a.check or a.print_deps_key:
            release_tag = "check-only"
        else:
            fail("release tag not set: pass --release-tag or export RELEASE_TAG")
    if not TAG_RE.match(release_tag):
        fail("release tag %r has unexpected characters" % release_tag)

    versions = load_versions(versions_path)
    upstream = load_yaml_text(read_text(upstream_path, "upstream manifest"), "upstream manifest")
    obn_modules = load_obn_modules(obn_path, versions)
    ffmpeg = ffmpeg_source_from_cmake(os.path.join(root, FFMPEG_CMAKE_REL))
    manifest, app_idx, report = generate(upstream, versions, obn_modules, ffmpeg, release_tag, a)

    if a.print_deps_key:
        print(deps_key(manifest, app_idx, os.path.dirname(os.path.abspath(upstream_path))))
        return 0

    header = ("# GENERATED by arm-build/make-manifest.py from %s -- do not edit or commit.\n"
              "# orcastudio %s, obn %s, release %s\n"
              % (os.path.basename(upstream_path), versions["orcastudio"]["tag"],
                 versions["obn"]["tag"], release_tag))
    text = header + dump_yaml(manifest)
    roundtrip_check(text, manifest)

    out_dir = os.path.dirname(os.path.abspath(out_path))
    if a.check:
        fd, tmp = tempfile.mkstemp(prefix=".arm-check-", suffix=".yml", dir=out_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(text)
            shown = show_manifest(tmp)
        finally:
            os.unlink(tmp)
        print("make-manifest: check OK (ffmpeg: %s; modules: %d; flatpak-builder --show-manifest: %s)"
              % (report["ffmpeg"], len(manifest["modules"]),
                 "parsed" if shown is not None else "not installed, skipped"))
        return 0

    fd, tmp = tempfile.mkstemp(prefix=".arm-gen-", suffix=".yml", dir=out_dir)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, out_path)
    print("make-manifest: wrote %s (ffmpeg: %s; obn modules: %s; release_tag=%s)"
          % (out_path, report["ffmpeg"], ", ".join(mm["name"] for mm in obn_modules), release_tag))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AnchorError as exc:
        sys.stderr.write("make-manifest: ERROR: %s\n"
                         "make-manifest: (upstream manifest, inputs or arguments changed; see arm-build/NOTES-ci.md)\n"
                         % exc)
        sys.exit(2)
