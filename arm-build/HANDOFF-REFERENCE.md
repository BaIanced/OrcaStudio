# Handoff reference: devices, tools, recipes (read on demand)

How-to material moved out of `HANDOFF.md` on 2026-10-13 so the hot file holds only rules, state and open work.
Read the matching section before driving a device or building; grep the rest (`grep -n "Chromebook" HANDOFF-REFERENCE.md`).
Nothing pending lives here: open / untested items stay in `HANDOFF.md`.

## Test devices
**Phone** = main test device (root). **Chromebook's Android (ARC)** = big-screen layout checks (user wants the app there).
**WSA** when both are away. The user drives sessions from the phone: ask before taking it over. Don't drive WSA while the
user uses the PC.

### Chromebook (ARC)
- `<chromebook-ip>:5555` (memory `test-on-phone`), Android 13, arm64, 1920x1080 (app area ~1813x948, shelf below), **no root**.
- Install: `install-build.ps1 -Run <id> -Device <ip>:5555`. Launch:
  `am start -n io.github.baianced.orcastudio_android/app.orcaandroid.ui.MainActivity`
  (ARC draws only while unlocked: focus = MainActivity, not ARC's PlaceholderActivity). `ui.ps1 -Device <ip>:5555` works.
- Zoom the canvas: `input mouse scroll <x> <y> --axis VSCROLL,1` (repeat; works over adb). One-finger `input swipe` orbits
  (or paints with the paint tool on). Tuck the panel for room.
- Section view panel: X only hides the panel; the reset button (history icon) turns the cut off.
- The system file picker is a ChromeOS dialog (adb can't drive it); open files with a VIEW intent on the MediaStore URI
  (`content query --uri content://media/external/file --where "_display_name='x'"` -> `-d content://media/external/file/<id>
  -t application/zip --grant-read-uri-permission`), which works without root.

### Phone
- Serial = the `adb-...._adb-tls-connect._tcp` entry in `adb devices` (`adb disconnect` a stale `ip:port`).
- Setup: archive "Phone test setup", memory `test-on-phone`; `phone-ui.py` needs `PYTHONIOENCODING=utf-8`;
  pull binaries with `adb exec-out "su -c '...'"`; Delete key = `su -c 'input keyevent 112'`.
- **MCP on a real phone:** the `localabstract` forward works over wireless adb; the socket binds only after an
  app restart with AI tools on (archive "MCP on a real phone").
- Raw multi-touch: `~/orca-android-tools/pinch.sh` / `drag1.sh` (push with `MSYS_NO_PATHCONV=1` and a `C:/` source path).

### WSA
- adb `127.0.0.1:58526` (root via `su -c '...'`, Android 13 / API 33; `run-as` fails, release build); an Android TV box is
  also attached, so always pass `-s`. Close the app when done:
  `adb -s 127.0.0.1:58526 shell am force-stop io.github.baianced.orcastudio_android`.
- WSA stops drawing when its window isn't in front (taps lost, empty ui dump): focus it first (Alt + SetForegroundWindow
  trick from `wheel.ps1:17` / `tapf.sh`). WSA wedged (no window): stop WsaClient, `Start-Service WsaService`,
  `Start-Process wsa://<package>`. Lost DNS: `wsaclient /shutdown`.
- Real mouse drags (+Shift): `mdrag.ps1 x1 y1 x2 y2 [-Shift]`, real clicks: `mclick.ps1 x y [-Right]` (Android coords = Windows pixels on WSA); the builder's
  shape list scrolls only with a real mouse wheel.
- WSA 1080p: the editor panel is short; collapse the preview ("Hide preview") to reach buttons below the Customizer notice.
- **MCP on WSA:** never `adb forward tcp:X tcp:Y` (WSA routes Android loopback to Windows; the forward loops and wedges
  adb: kill adb.exe). Use `adb forward tcp:8765 localabstract:orcastudio_mcp`. Token: `su -c 'cat .../shared_prefs/app_settings.xml'`
  into a variable, never print it. Run adb calls in PowerShell jobs with timeouts while testing sockets.
- WSA -> LAN printer: run `wsa-lan.ps1 <printer-ip>` after each WSA start. Safe print-dialog test:
  `iptables -I OUTPUT -d <ip> -p tcp --dport 990 -j REJECT` (root), Print, Cancel, `iptables -D ...`.
- Closing the WSA window (`CloseMainWindow()` on the "OrcaStudio-Android" window) runs onStop (saves the session).
- Phone view on WSA (`phone-view.sh`): back-burnered (user, 2026-10-13: "didn't look right"); notes in the archive.

### All devices
- The app restores `files/session/session.3mf` on start and saves it in `onStop` (and by auto-save every 60 s when
  changed). `am force-stop` skips the onStop save.
- Draft of the open OpenSCAD design: `files/openscad/draft.scad|json` (read with `adb exec-out "su -c 'cat ...'"`; the Code
  tab text isn't in the ui dump).
- Shape-builder data = CSG JSON in the object's `module` metadata (`scad/ShapeModel.kt`).
- System file picker (phone/WSA): plain `adb input tap` (focus.ps1 finds no app window while it is up), scroll with `input swipe`, avoid its Search (list broke); delete test
  files from `/sdcard/Download` after. Close with `adb shell am force-stop com.android.documentsui`.
- adb `input` has no Shift/Alt state: use `keys.ps1 -Keys <vk codes>` (WSA; real key presses; tap a row first for focus).
- Action snackbar ("Add"): VIEW intent on `scadzip-test.zip` (MediaStore id via `content query`, see "Chromebook");
  it shows ~10 s, screenshot 3 s after the intent.
- Test with `ui.ps1` text dumps; screenshots only when the look matters. After launching the app, wait until `ui.ps1`
  lists the tabs before tapping (the first tap after start is often lost).

## Build and tools
- Compile Kotlin locally before every push (12 s warm):
  `cd OrcaStudio-Android/android && JAVA_HOME="/c/Program Files/Java/jdk-22" ANDROID_HOME='C:\android_sdk' ./gradlew --console=plain -q :app:compileReleaseKotlin`
  Add `:app:mergeReleaseResources` when strings change, and read the exit code (a grep on the output hid a failure once).
- Local native build in WSL: `MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /mnt/c/Users/Vince/orca-android-tools/wsl/corebuild.sh`
  (25 min cold, seconds incremental; details in the archive).
- CI (`android-apk.yml`, dispatch only: `gh workflow run android-apk.yml --ref <branch>`; cache details in the archive):
  checks **19** `ObnNative` JNI exports (update when adding one). Release-signed since build 32.
- `~\orca-android-tools`: `install-build.ps1 -Run <id> [-Device <serial>]` (WSA default), `ui.ps1 [-Device] [-Shot png]`,
  `step.ps1`, `wheel.ps1` (real mouse wheel / drags), `drag.ps1`, `reinstall-with-data.ps1`.
- Debug logs / Models WebView CDP: archive "Logs and CDP (moved 2026-10-12)".

## Environment and repos
- Working dir `C:\Users\Vince\OrcaProjectsGithub` with `OrcaStudio` (Flatpak; holds the handoff) and `OrcaStudio-Android`
  (`src-orca` submodule = OrcaSlicer). gh CLI logged in.
- The user's Chromebook Linux (Crostini, aarch64) runs the Flatpak; A1 printer is cloud-bound (Developer Mode off); the
  app is signed in to their Bambu account with PEMs imported.

| Repo | Notes |
|---|---|
| `BaIanced/OrcaStudio-Android` | cl1x/Orca-Android + signed Bambu printing via obn (static in `liborca_jni.so`, `android/obn`). Bot branch `upstream/orca-main` (never commit). |
| `BaIanced/OrcaStudio` | Flatpak fork; ours: `arm-build/`, `.github/workflows/arm-*.yml`. Latest release r9 (MakerLab tab). Details in the archive. |
| `ClusterM/open-bamboo-networking` | obn pinned v2.2.0 + local patches 0001 (cloud callbacks), 0002 (start_print try LAN first), 0003 (MQTT CA from `SSL_CERT_FILE`). |
