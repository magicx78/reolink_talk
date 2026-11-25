# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.5]

### Changed

- `media_player.play_media` again completes only after the complete realtime
  audio stream has played (or was explicitly stopped). The low-latency binary
  frame writes and the pre-warmed Baichuan connection remain in place.

## [0.3.4]

### Fixed

- **Standard local-media IDs work again.**
  `media-source://media_source/local/doorbell.mp3` now correctly interprets
  `local` as Home Assistant's media-directory ID; no duplicated `/local` is
  required.
- **Short announcements start without per-frame acknowledgement delays.**
  Binary Baichuan talk packets (cmd 202) are now written through
  `send_without_wait()` and paced locally instead of waiting for an often
  delayed or absent camera response for every frame.
- The talk session is pre-warmed after setup to avoid a Baichuan connection
  and login round-trip before every announcement.

## [0.3.1] - 2026-09-06

Compatibility pass for Home Assistant 2026.9.1 (Python 3.14, reolink-aio 0.21.15).

### Fixed

- **`media_play_pause` was still rejected after 0.3.0.** Home Assistant checks
  `features & (PLAY | PAUSE) == PLAY | PAUSE`, i.e. it requires *both* bits;
  0.3.0 only advertised `PAUSE`. `PLAY` is now advertised as well (the
  existing no-op `async_media_play()` handles it). Caught by the new
  in-Home-Assistant test — the 0.3.0 changelog claim was wrong.

### Changed

- `device_class` uses `MediaPlayerDeviceClass.SPEAKER` instead of a string.
- Platform setup typed with `AddConfigEntryEntitiesCallback`; media player
  enums imported from the `media_player` package instead of `.const`.
- Options flow follows the HA >= 2024.11 pattern (no `config_entry`
  constructor argument; uses the framework-provided `self.config_entry`).
- `manifest.json` declares `single_config_entry`.
- Test pins bumped to `reolink-aio==0.21.15` (the version bundled with HA
  2026.9.1); the private Baichuan API used by `send_talk_binary` is unchanged
  between 0.21.3 and 0.21.15 (verified by the real-class test).

### Added

- `tests/test_setup_ha.py`: sets the integration up inside a real Home
  Assistant (config entry, entity/features, card services, options flow, and
  a guard against HA deprecation warnings). Runs via
  `requirements-test-ha.txt` and a dedicated CI job on Python 3.14.

## [0.3.0] - 2026-08-23

### Added

- **Stop / pause support**: a running announcement can now be aborted
  (`media_player.media_stop`, `media_player.media_pause`, or the play/pause
  button on a media player card). The streaming loop reacts immediately and
  still closes the talk session cleanly (Baichuan cmd 11).

### Fixed

- **`Entity ... does not support action media_player.media_play_pause`**:
  media player cards (e.g. `custom:mini-media-player`) call
  `media_play_pause` unconditionally, which failed because the entity
  advertised neither `PLAY` nor `PAUSE`. The entity now advertises
  `STOP | PAUSE`, and `async_media_play()` is implemented as an explicit
  no-op so pressing play while idle does nothing instead of raising.
  `PLAY` itself is deliberately **not** advertised — this player has nothing
  to resume; it only speaks what `play_media`/TTS hands it.

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
