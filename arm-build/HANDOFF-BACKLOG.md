# Backlog (pending / untested / ideas). Grep, do not read up front. Moved here from HANDOFF.md 2026-10-15.
Rules: never delete an item; when one is verified, move its details to HANDOFF-ARCHIVE.md. User 2026-10-15: do NOT bring up the X2D again.

## Plan
- **Plan (user, 2026-10-14):** camera LAN (done) -> off-LAN camera (cloud P2P path; REA on Handy is the tool; VPN-home the
  fallback) -> print history (capture Handy's history call, own client, Device tab) -> REA on MakerWorld. Own printer/account,
  personal use, own code only; rule 7 holds.


## Former "Next task" list
000. **Verification session 2026-10-15 done (details: archive "2026-10-15: verification session").** Verified: all r231-r243 items (camera/handle/plate select/tap plate/per-plate tower/design fold/tower clearance), pan + drag-start, colour dots, mixed-temp text (Claude tested on Chromebook), r216, r213, layout lab limits, large multi-plate slice. **Merged to main as PR #25.** Installed r243 (run 38837405092, head 43aebe7) on all 4 devices.
   **Logged findings (user's words, NOT acted on; the user wants the data first, then decides):**
   - L1/L3 + printer-model guard: DONE in 54b4ca6 2026-10-15, UNTESTED (see HANDOFF Next task).
   - L1. Design panel fold: a very fast rubber-band/ghost image of the panel snaps above it (functionality fine).
   - L2. VERIFIED on phone r245 2026-10-15 by Claude (readout card shows 'Text size: 95 %' + bar mid-drag; Reset restored 100 %; archive when next pruning): while a lab slider is dragged, a readout card (label, value, bar) stays at the top of the screen as More fades (`MoreScreen.kt` ScaleSlider + `LabPeek.readout`, `AppScaffold.kt` Screen.MORE).
   - L3. Camera card (phone, wrong access code / unreachable printer): error shown but its words are cut off (user has a picture to upload); the whole card should not error because the AMS can be read through the cloud.
   - L4. (Claude, Chromebook) Preview summary still shows the red "nozzle temperatures incompatible" warning (without the hint) even when "Remove mixed temperature restriction" is on and the slice works. **Source check 2026-10-15:** upstream design, `Print.cpp:1226-1228` and `:1264-1266` emit the same text with `is_warning=true` (no hint) when mixing is allowed. So the warning is correct; only its red styling might be softened to a warning colour **VERIFIED on phone r245 2026-10-15 (archive). Decided by Claude (user 2026-10-15 "you decide"):** when "Remove mixed temperature restriction" is on, that line uses the tertiary colour instead of red (`PreviewPanel.kt` ~133). UNTESTED on device.
   - L5. Inactive-plate double tap re-frames (user: fine, no change wanted).
0. **Still UNTESTED:** (a) German strings (user 2026-10-15: doesn't speak German, STUB: no more effort or testing, shipped as is) for the filament-choice dialog: added 2026-10-15 (commit 16251c4, pushed, not in a build yet, UNTESTED on device); (b) floating Theme | Layout designer idea = ~half a day (+1-2 h for a collapsible icon), not started.
2. **Phone checks waiting on the user** (all UNTESTED; they change the user's project):
   - (User 2026-10-15: keep this item, do NOT bring up the X2D again; they can't trigger it and may hit it by accident.)
   - r215 single-filament slice crash fix (`OrcaEngine.cpp` ~507) and r217 dual-nozzle fix (`heads = max(1, multiplier, nozzle_diameter count)`): slice with the X2D selected.
   - r213 haptics (settings tabs TextHandleMove, Models edge swipes CLOCK_TICK; can't be checked over adb).
   - 165 Hz: done, don't ask.
3. **Not done / ideas:** auto-select the A1 on the MakerWorld/MakerLab page at load (look at how the site stores its printer pick;
   CDP on the Models WebView); a slice/print-time guard comparing the sliced printer with the connected one; a line under inactive
   settings tabs (user's idea). 3D stage 4 wishlist: real shadow map. Preview colours stay flat on purpose.
   - Blind shader/light re-test findings (2026-10-16, `NOTES-blind-shader-test-2026-10-16.md`), all open, none fixed: shadow spills
     off the bed into the background; section ratio spans all plates' objects (0.5 cuts nothing on plate 1, 0.8 everything);
     shadow on parts subtle at 50 %; bias knob shows ~no effect; grid line breaks/shimmer in top views.
4. **Nav proposal: DONE (user answered: Back goes to plate view; built in 16aa31d, steps plate view > design view > close; device check not recorded).** Old analysis: Back = AppScaffold.kt:148; Models back + edge swipes
   ModelsScreen.kt:464/:182; settings tab swipe SettingsEditor.kt:303. Gap: no BackHandler for the OpenSCAD editor (`state.scad`,
   AppScaffold.kt:281 -> Back opens the quit prompt), the eye "design on plate" mode, the section panel, the design panel.
   Proposal: Back in OpenSCAD = on-plate view -> design view -> `scad.close()`; optional horizontal swipe between main tabs (not on Prepare).
5. Then: the plate switcher pick (lab stays until they say), the user-only items below.

Still open from earlier batches: **root cause of the r197 NumberField NPE not found** (stack traces now logged under `OrcaStore`);
"failed OpenSCAD run clears the old log" **untested** (no repro); the WSA lighter-background glitch is closed (user: caused by their other PC activity at the same time). Design mode known limits: hard-coded colours (delete popup #2B2C32, red bin,
preview legend) don't follow; the Models page keeps its own colours; a dark 3D background under a light theme hides the floating
tool icons ("Prepare: floating buttons" can be changed). User-only: retests, plate switcher pick, launcher icon colour (still teal, "decide later").


## Open and untested items
0. Element blocker + ad-block menu: verified phone + WSA; sign-ins verified (archive). **Untested:** rules in other WebViews (Device page etc.; needs a printer with a web UI).
1. Verified, nothing open (archive): preset re-link + syncs, section view, shape builder, .scad zips / 16 KB sniff, OpenSCAD
   phone layout / downloads / painting, MakerWorld sign-in ticket flow.
2. Nozzle match + filament picks per AMS tray: verified. **Untested:** newer-firmware `device.nozzle.info` path; stale status
   after switching printer models; spool change -> printer's preset wins and the pick is dropped (only when the user swaps a
   spool). Tray picks on WSA r194: verified. Phone plate: 1 slot "Bambu PLA Basic @BBL A1".
6. Ad blocking (`AdBlock.Client` in all app WebViews): verified (details: archive "2026-10-15: pruned verified details"). **Untested:** plugin pages, Device page on
   the phone (needs a printer with a web UI).
9. **Untested:** a true EGL context loss (no repro). Badges are ~23 dp at plate zoom on the phone (under 48 dp; told the user).
10. 325 MB slice retest: replaced by a verified 20+ plate slice (archive). MakerWorld pinch zoom works (user 2026-10-14).
    Real keyboard Ctrl+1 (camera top view, MainActivity.kt:190) does nothing: the system takes it as a hotkey (user
    2026-10-14). Offered: numpad 0-7 as an extra view binding (not done, untested).
11. Orca plugin runtime: kept as a general capability (no plugin in use). Not done: audit prompts, create_window, per-preset
    config overrides, printerAgent capability. **FilamentHub is dropped for good; never suggest, test with, or mention it.**
12. REA MCP (github.com/morluto/rea), looked at 2026-10-12, already installed by the user (2026-10-15), just not enabled (the user enables it): fits release
    APK / `liborca_jni.so` inspection and HAR traces of the MakerWorld / Thingiverse flows only.
13. Wishlist later: filament colour mixing (upstream `FilamentMixer.cpp`). Not wanted: iOS port. Flatpak r9 MakerLab tab,
    weekly upstream bump, obn follow-ups: archive (2026-10-12 trim).

