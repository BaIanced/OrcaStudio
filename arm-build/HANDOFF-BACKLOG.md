# Backlog (pending / untested / ideas). Grep, do not read up front. Moved here from HANDOFF.md 2026-10-15.
Rules: never delete an item; when one is verified, move its details to HANDOFF-ARCHIVE.md. User 2026-10-15: do NOT bring up the X2D again.
Pruned 2026-10-16: verified entries moved to archive "2026-10-16 Backlog stale-item prune". Before re-testing anything, grep the archive.
Each line says who last checked it, on which build, when (e.g. "user r249 2026-10-15: no vibration"). A user verdict in chat is logged here + archive at once.

## Plan
- **Plan (user, 2026-10-14):** camera LAN (done) -> off-LAN camera (cloud P2P path; REA on Handy is the tool; VPN-home the
  fallback) -> print history (capture Handy's history call, own client, Device tab) -> REA on MakerWorld. Own printer/account,
  personal use, own code only; rule 7 holds.

## Open bugs
- r197 NPE root cause found + fixed in 6ad69ef (unbuilt, untested in app; no UI path still sends NaN since 776f261).

## Untested (needs the user or a special setup)
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
- 3D wishlist: preview colours stay flat on purpose. Filament colour mixing (upstream `FilamentMixer.cpp`). Not wanted: iOS port.
- Orca plugin runtime: kept as a general capability (no plugin in use). Not done: audit prompts, create_window, per-preset config
  overrides, printerAgent capability. **FilamentHub is dropped for good; never suggest, test with, or mention it.**

## Known limits (no action)
- Design mode: hard-coded colours (delete popup #2B2C32 + red bin = user's pick 2026-10-14, `OverlayParts.kt:253`; preview legend)
  don't follow; the Models page keeps its own colours; a dark 3D background under a light theme hides the floating tool icons
  ("Prepare: floating buttons" can be changed).
- Real keyboard Ctrl+1 does nothing (system hotkey). Inactive-plate double tap re-frames (user: fine).
- Flatpak r9 MakerLab tab, weekly upstream bump, obn follow-ups: archive (2026-10-12 trim).
