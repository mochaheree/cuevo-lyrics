# Changelog

Notable changes per release. Dates are ISO. The full engineering record,
including measurements and bugs that were found and fixed along the way, is
in [SRS.md](SRS.md).

## v0.11.0 - 2026-09-04

First public release.

### Added
- **Live tab.** Set list, clickable lyric lines, output preview, transport
  with play, pause, next, prev, sync offset, and a BLANK kill switch.
  Auto-timestamp mode and manual line mode.
- **Library tab.** LRCLIB search through one free-form box that takes title,
  artist, or both in any order. Local library that works offline. `.lrc`
  import.
- **Manual lyric editor.** Tap-to-timestamp, shift all timestamps, export
  `.lrc`.
- **Show tab.** Build a set list, drag to reorder, save and reopen
  `.showproject.json` files.
- **Style tab.** Layout, system fonts, size, colours, outline, line spacing,
  size and opacity falloff, edge fade, transition speed, context line count.
  Five built-in presets and user templates. Right-click any control to reset
  it, the way Resolume Arena behaves.
- **Settings tab.** Spout sender name, resolution, fps, file locations,
  shortcut list. Saves on field exit, no Apply button.
- **Operator Display.** A NOW/NEXT window for a second monitor.
- **Cast window.** One window for OBS window capture, TikTok Live Studio, and
  full screen on a second monitor. Detects that alpha does not survive window
  capture and offers a one-click fix.
- **Global hotkeys** through the Win32 API, no extra dependency.
- **OSC and MIDI remote control.** OSC uses a hand-written parser and needs
  nothing installed. MIDI needs `python-rtmidi` and degrades cleanly without
  it.
- **Donate tab** with Saweria, a QRIS code, and contact links.
- Application icon, built at every size Windows actually uses.
- Data lives under `%APPDATA%\CUEVO Lyrics\`, written atomically.

### Known limitations
- OSC and MIDI are implemented but not yet verified against real hardware.
  SRS section 3.13 lists exactly what is unverified.
- Spout output is Windows only. Everything else runs anywhere.
- Sync is manual by design. No audio analysis, no beat detection.
- The build is not code signed, so Windows SmartScreen will warn on first run.

### Notes for anyone forking
Replace the config block at the top of `ui/donate_view.py` and the QR at
`assets/qris.png` with your own. Both are documented in the README.
