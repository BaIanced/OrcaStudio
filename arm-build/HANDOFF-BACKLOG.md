# Backlog (pending / untested / ideas). Grep, do not read up front. Moved here from HANDOFF.md 2026-10-15.
Rules: never delete an item; when one is verified, move its details to HANDOFF-ARCHIVE.md. User 2026-10-15: do NOT bring up the X2D again.
Pruned 2026-10-16: verified entries moved to archive "2026-10-16 Backlog stale-item prune". Before re-testing anything, grep the archive.
Each line says who last checked it, on which build, when (e.g. "user r249 2026-10-15: no vibration"). A user verdict in chat is logged here + archive at once.

## Plan
- **Plan (user, 2026-10-14):** camera LAN (done) -> off-LAN camera (cloud P2P path; REA on Handy is the tool; VPN-home the
  fallback) -> print history (capture Handy's history call, own client, Device tab) -> REA on MakerWorld. Own printer/account,
  personal use, own code only; rule 7 holds.
- **HIGH PRIORITY (user 2026-10-17, queued after r283): printer controls on the Device tab**, like Handy's Control page
  (user screenshot): tabs Control | XYZ. Control = nozzle temp cur/target + extrude up/down arrows + "More"; Speed level
  (Standard 100 %); Heatbed temp cur/target; Light toggle; Part Fan %. XYZ = jog + home. Orca's source already has every
  command (no REA needed for this): `DeviceManager.cpp` command_set_nozzle 1689, set_bed 1683, set_printing_speed 1928,
  axis_control 2007, extruder_control 2015, go_home 1560; `DevFan.cpp:54` control_fan; `DevLampCtrl.cpp:38` chamber light.
  Kotlin side: `android/.../ui/device/DeviceScreen.kt`. The user said they may use REA for other parts. Not started (Claude 2026-10-17).

## Open bugs
- Preview: shading gone after slice? (user unsure of convention, r284, 2026-10-17). Inner z-fighting when the layer slider
  is scrubbed down and the camera moves (user, r284, 2026-10-17): cracks + seam fights fixed r285 (Claude-verified
  2026-10-17, archive); user's look pending.
- Zoom too slow when zoomed out; user suggests zoom-dependent curve, hasn't tried the zoom speed slider (r284, 2026-10-17; lab opens again in r285).
- r197 NPE root cause fixed in 6ad69ef, built in r273 (Claude 2026-10-16); no UI path sends NaN since 776f261, so no in-app repro.

## Untested (needs the user or a special setup)
- Pinch (r280, run 39011426374; user: too sensitive, fingers close also pan): two-finger gesture locks to PINCH (zoom only)
  or PAN (pan+zoom) past the slop; gap ratio padded 40 dp; Layout lab "Pinch zoom speed" (default 60 %). Camera limits
  unchanged. Feel = user-only; ask after install (Claude 2026-10-17, not yet asked).
- User hasn't seen yet (Claude-verified by test): preview bead look (Chromebook, zoomed in), part shadows r266, light/shadow lab sliders (r263, via `labset.py`).
- "Failed OpenSCAD run clears the old log": no repro.
- Element blocker / ad-block rules in other WebViews: plugin pages, Device page (needs a printer with a web UI).
- Nozzle match: newer-firmware `device.nozzle.info` path; stale status after switching printer models; spool change -> printer's
  preset wins and the pick is dropped (only when the user swaps a spool). Phone plate: 1 slot "Bambu PLA Basic @BBL A1".
- A true EGL context loss (no repro). Badges are ~23 dp at plate zoom on the phone (under 48 dp; told the user).
- Model-mismatch guard (54b4ca6): built, can't be tested (user has one printer).
- SHIELD TV: r210 settings/logins copied from the phone; sign-ins untested.

## Waiting on the user
- Plate switcher pick (lab stays until they say; don't ask again).
- Launcher icon colour (still teal, "decide later").
- REA MCP (github.com/morluto/rea): installed, not enabled (the user enables it); fits release APK / `liborca_jni.so` inspection and
  HAR traces of the MakerWorld / Thingiverse flows only. Plan items need it.

## Ideas (not started)
- Floating Theme | Layout designer = ~half a day (+1-2 h for a collapsible icon); ask first.
- Maybe study Bambu Handy's MakerWorld integration.
- (2026-10-17, user, queued) Explore porting to Meta Quest (Quest runs Android/Horizon OS: check whether the existing APK installs and runs as a 2D panel app, what input (controllers/hands, no touch/stylus) and GL/Vulkan limits mean, and what a native VR view of the plate would take). **Desk research done 2026-10-17 (Claude, no Quest to test; web claims per Meta docs, unverified on device):** the APK should install as a 2D panel: Horizon OS is AOSP-based (min API 32 vs our minSdk 29), our manifest needs no GMS/camera/telephony (no play-services dep), GLES 3.0 only (`#version 300 es`, `GLSurfaceView` in PlateView/MeshPreviewView), arm64-only OK, v2 signing OK. Meta says taps/swipes map from controllers/hands to 2D apps; two-finger pinch/orbit likely does NOT (single pointer): the Layout lab pinch-speed slider and wheel zoom (mouse path exists in PlateView.onGenericMotionEvent) are the fallback, needs a zoom/orbit-mode button. Open unknowns: WebView version on Horizon OS (Models tab, Bambu login, plugin pages), min panel 384x500dp layout, long-press = right-click. Native VR view (Spatial SDK Kotlin/Compose panels + own GLES->OpenXR scene, or OpenXR NDK) is a big separate project: needs a headset to start. **User 2026-10-17: Quest is multi-pointer (so the pinch-risk above is probably moot); no single-pointer workarounds wanted; SKIPPED for now, resume only on request.** Next step: `adb install` + test panel input. User (2026-10-17) has a headset with dev mode on; wireless adb is unreliable and works when they trigger it manually; they will set it up later (ask them to connect it, don't poll).
- 3D wishlist: preview colours stay flat on purpose. Filament colour mixing (upstream `FilamentMixer.cpp`). Not wanted: iOS port.
- Orca plugin runtime: kept as a general capability (no plugin in use). Not done: audit prompts, create_window, per-preset config
  overrides, printerAgent capability. **FilamentHub is dropped for good; never suggest, test with, or mention it.**

## Known limits (no action)
- Design mode: hard-coded colours (delete popup #2B2C32 + red bin = user's pick 2026-10-14, `OverlayParts.kt:253`; preview legend)
  don't follow; the Models page keeps its own colours; a dark 3D background under a light theme hides the floating tool icons
  ("Prepare: floating buttons" can be changed).
- Real keyboard Ctrl+1 does nothing (system hotkey). Inactive-plate double tap re-frames (user: fine).
- Flatpak r9 MakerLab tab, weekly upstream bump, obn follow-ups: archive (2026-10-12 trim).
- (user, 2026-10-17, queued) Drag handles: a fast downward fling should collapse the panel (now it stops right where the finger lets go). DragHandle in AppScaffold (portrait sheet, OpenSCAD panel; wide PanelEdge flung sideways). r283 (user 2026-10-17): every fling crashed; fixed in r284 (Claude 2026-10-17, phone: portrait sheet flick up expands, down collapses, no crash). Open: user feel, wide PanelEdge + OpenSCAD grips untested.
- (user, 2026-10-17, queued, low priority "put makeup on it") Explore free open-source colour icon sets (licence must allow use in a public app, e.g. MIT/Apache/CC-BY) to give some icons colour, not all; the app is "beautiful as is". Deliver: shortlist + mockup of which icons get colour, user picks. Open, not started.
- (user, 2026-10-17, TOP) Slice button in the drag handle's right side (where the plates are); own size slider, follows only main UI scale. Built r281, untested (handoff Next).
- (user, 2026-10-17, queued) Stylus support: Samsung S Pen (check whether one API covers old and new: plain Android MotionEvent
  TOOL_TYPE_STYLUS / BUTTON_STYLUS_PRIMARY / pressure / hover vs Samsung's SDKs, e.g. Air actions only on newer pens).
  User's devices: Note 10.1 2014 tablet, Note 10+, S24 Ultra (screen broken now), a newer 13" Galaxy Tab S. Also a head start
  on the Lenovo Duet 5 (Chromebook) USI stylus, which only the user could test. Open. **Desk research 2026-10-17 (Claude, r289, no
  device; web per developer.android.com "advanced stylus features", unverified on hardware):** plain MotionEvent covers every
  pen: `getToolType` STYLUS / ERASER, AXIS_PRESSURE / TILT / ORIENTATION, hover = ACTION_HOVER_* (pen near screen), barrel button =
  `BUTTON_STYLUS_PRIMARY` (some devices report `BUTTON_SECONDARY`/`TERTIARY` instead, so test all three). Samsung SDKs (S Pen
  Remote, Air actions) are only for the in-air remote/gestures of Bluetooth pens (newer than 2014/Note 10.1); not needed for
  drawing/tapping. Not confirmed: whether the 2014 EMR pen sends hover/button on the Note 10.1, or ARC passes USI pressure/tilt.
  **Code today (PlateView.kt:191-320):** touch only, no tool-type use except `SOURCE_MOUSE` for right/middle (l.204); a pen
  already works as one finger (orbit / drag / paint / tap). Proposed (not built): pen barrel button or eraser end = pan (same
  as the mouse's middle path, l.205-206 + 258), pen hover shows the paint-brush cursor, pressure scales PAINT brush size.
  Palm rejection: OS cancels via ACTION_CANCEL (handled l.313). **BUILT 7d3a263 (run 39070383865, 2026-10-17), untested on a pen.**
  **User decisions 2026-10-17:** keep two-finger pan/pinch (like Squid); palm rejection ON for pen/stylus (also ignore
  TOOL_TYPE_FINGER while the pen is down or hovering); NO pressure/tilt use; eraser end + every pen button must be
  user-mappable to an app action (Settings list: pan, undo, redo, select, paint, none...; reads BUTTON_STYLUS_PRIMARY/
  SECONDARY/SECONDARY/TERTIARY + TOOL_TYPE_ERASER). Idea (user, open, not decided): **Sketch mode** = draw a rough object
  with the pen and have MCP create it (open: who interprets the sketch? Claude through MCP in a session, e.g. a saved PNG
  + `view_state`, vs. on-device; Claude can read the image and write OpenSCAD/primitives, no on-device model). Not started.
- (2026-10-17, user, open) Portrait Undo/Redo used to sit in the top-left corner (status bar area, fullscreen); moved at some point; File belongs in the status bar area right of the camera cutout. r283 (Claude, phone, 2026-10-17): Undo/Redo at top left y 58, File at top right x 1141; the user hasn't judged the look yet.
- (2026-10-17, user idea, open) Next MCP tool candidates: debug `app_state`, `log_tail`, `perf` (`slice` + `slice_result` done r289, archive). Last checked: Claude, r289.
