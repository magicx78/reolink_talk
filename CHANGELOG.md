# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.1] - 2026-07-02

### Fixed

- **`'Baichuan' object has no attribute '_mutex'`** when sending talk audio
  on current Home Assistant. `reolink_aio` 0.21 moved the TCP/UDP plumbing
  from the `Baichuan` object (`_mutex`/`_transport`/`_protocol`) into a
  dedicated connection object; `send_talk_binary()` now uses
  `bc._connection.send()` (which writes under the connection's lock and
  awaits the camera ack) and keeps the old transport path as a fallback for
  older `reolink_aio` versions. Found during a real TTS hardware test.

### Added

- Integration-style regression test that drives the **real**
  `reolink_aio.Baichuan` class (only the network layer replaced), so future
  changes to reolink_aio's private attribute layout fail in CI instead of on
  the camera.

## [0.2.0] - 2026-07-02

First release of the maintained fork ([magicx78/reolink_talk](https://github.com/magicx78/reolink_talk)).

### Fixed

- **Upstream [#6](https://github.com/joeblack2k/reolink_talk/issues/6)**:
  `TypeError: Object type <class 'str'> cannot be passed to C code`.
  The Extension XML for talk binary frames (cmd 202) was built as `str` and
  passed directly to `reolink_aio`'s `Baichuan._aes_encrypt(body: bytes)`,
  which hands it straight to Cryptodome C code. Every talk/TTS playback with
  AES encryption crashed on Python 3.13+/3.14 (current Home Assistant).
  The extension is now UTF-8 encoded via a new `ensure_bytes()` helper and the
  whole payload chain is normalized to `bytes` before packet assembly.
  (The bug is in this integration, not in `reolink_aio`; a defensive
  `str`-accepting `_aes_encrypt` upstream would merely be a nice-to-have.)
- **Upstream [#1](https://github.com/joeblack2k/reolink_talk/issues/1)**:
  HACS installation crashed due to `zip_release: true` without `filename` in
  `hacs.json`. Cherry-picked from upstream
  [PR #3](https://github.com/joeblack2k/reolink_talk/pull/3) by @ineedjet.
- **RLC-811A talk start**: rspCode 421 is now treated like 422
  (stop stale talk session, then retry). Cherry-picked from upstream
  [PR #5](https://github.com/joeblack2k/reolink_talk/pull/5) by @kucau0901.

### Added

- `ensure_bytes()` helper (`custom_components/reolink_talk/util.py`).
- Regression test suite (pytest) with a strict Baichuan mock whose
  `_aes_encrypt` rejects `str` exactly like Cryptodome — the issue #6
  regression fails loudly if the bug ever returns.
- Debug logging across the pipeline (media/PCM/ADPCM sizes, encryption type,
  payload types) — no credentials or URLs are logged.
- CI: hassfest, HACS validation, ruff and pytest (Python 3.13/3.14).

### Changed

- `manifest.json`: version 0.2.0, documentation/issue tracker point to this
  fork.
- README/info documented as maintained fork with HACS custom-repository
  install instructions.
- Code formatted with ruff (mechanical, no functional changes).

## [0.1.0] - 2026-02-09

Initial upstream release by [@joeblack2k](https://github.com/joeblack2k):
[joeblack2k/reolink_talk v0.1.0](https://github.com/joeblack2k/reolink_talk/releases/tag/v0.1.0).
