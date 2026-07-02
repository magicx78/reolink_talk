# Reolink Talk (Two-Way Audio) for Home Assistant

![Reolink Talk](docs/banner.png)

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Tests](https://github.com/magicx78/reolink_talk/actions/workflows/tests.yaml/badge.svg)](https://github.com/magicx78/reolink_talk/actions/workflows/tests.yaml)

> **Maintained fork** of [joeblack2k/reolink_talk](https://github.com/joeblack2k/reolink_talk).
> The upstream project is no longer maintained; this fork fixes the crash on
> current Home Assistant / Python 3.13+ installs (upstream
> [issue #6](https://github.com/joeblack2k/reolink_talk/issues/6)), repairs the
> HACS installation, merges pending community fixes, and adds tests and CI.
> All credit for the original implementation goes to
> [@joeblack2k](https://github.com/joeblack2k) (MIT license).

Expose Reolink cameras that support **two-way audio** as `media_player` entities, so you can play:

- MP3/WAV files (local media or URLs)
- Home Assistant TTS output (anything that resolves to audio)

This integration piggybacks on the **official Reolink integration** for credentials and device selection, but it **does not depend on go2rtc, Frigate, or Docker** for talkback.

## Fixed in this fork

| Upstream issue | Problem | Status |
| --- | --- | --- |
| [#6](https://github.com/joeblack2k/reolink_talk/issues/6) | `TypeError: Object type <class 'str'> cannot be passed to C code` — the Extension XML was passed as `str` to `reolink_aio`'s AES encryption, crashing every talk/TTS playback on Python 3.13+/3.14 (current Home Assistant) | ✅ fixed (v0.2.0) |
| [#1](https://github.com/joeblack2k/reolink_talk/issues/1) | HACS installation crashed (`zip_release` without `filename` in `hacs.json`) | ✅ fixed (v0.2.0, via upstream [PR #3](https://github.com/joeblack2k/reolink_talk/pull/3)) |
| [#5](https://github.com/joeblack2k/reolink_talk/pull/5) | RLC-811A rejects TalkConfig with rspCode 421 when a stale talk session exists | ✅ fixed (v0.2.0, via upstream [PR #5](https://github.com/joeblack2k/reolink_talk/pull/5)) |

## Install (HACS)

1. In HACS, open **⋮ → Custom repositories** and add
   `https://github.com/magicx78/reolink_talk` with category **Integration**.
2. Install **Reolink Talk (Two-Way Audio)**.
3. Restart Home Assistant.
4. Add the integration in Settings → Devices & Services.

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=reolink_talk)

Manual install: copy `custom_components/reolink_talk/` into your Home Assistant
`config/custom_components/` directory and restart.

## Requirements

- Home Assistant with the **official Reolink integration** configured.
- `ffmpeg` available in your Home Assistant environment (used to decode/transcode audio before sending).

## Configuration

The config flow needs no input — it piggybacks on the official Reolink
integration. Via **Configure** (options) you can select which Reolink config
entries get a talk `media_player` and which camera channel to use (default 0).

## Usage

After setup, you will get one `media_player` per selected Reolink config entry:

- `media_player.<something>` (shown in UI as "Reolink Talk <camera title>")

You can:

- Use the media browser to pick local files from `media/` or TTS providers.
- Call `media_player.play_media` from automations/scripts.
- Use the volume slider (software volume; some camera models may also support hardware speak volume).

### Example: TTS to the camera speaker

```yaml
action: tts.speak
target:
  entity_id: tts.google_translate_de_de   # any configured TTS entity
data:
  media_player_entity_id: media_player.reolink_talk_haustuer
  message: "Paket bitte vor die Tür legen"
```

### Example: play a local file

```yaml
action: media_player.play_media
target:
  entity_id: media_player.reolink_talk_haustuer
data:
  media_content_type: music
  media_content_id: media-source://media_source/local/doorbell.mp3
```

## Compatible Cameras

This integration only works for cameras that expose Reolink **TalkAbility** with `audioType=adpcm` via the Baichuan protocol (that is what the official Reolink app uses for talkback).

### Confirmed Working

- Reolink **Video Doorbell series** (tested on a doorbell in the upstream author's setup)
- Reolink **RLC-811A** (community-tested, needs the 421 fix included in this fork)

### Expected To Work (Needs Community Confirmation)

In general, models that support **Two-Way Audio** in the official Reolink app/client are good candidates, as long as they are set up as standalone devices in Home Assistant (not behind an NVR/Home Hub limitation) and expose ADPCM TalkAbility.

Reolink maintains an official list of models that support Two-Way Audio:

- [Which Reolink Cameras Support Two-Way Audio](https://support.reolink.com/hc/en-us/articles/360003764334-Which-Reolink-Cameras-Support-Two-Way-Audio/)

Important caveats from Reolink:

- If a camera is connected to an NVR, two-way audio may not be usable in some configurations. See: [Introduction to Two-Way Audio](https://support.reolink.com/hc/en-us/articles/900000600906-Introduction-to-Two-Way-Audio/).

If you test a model successfully, please open a GitHub issue/PR and add it to the "Confirmed Working" list (include your model name and whether it is PoE/WiFi/battery).

## Stability / Compatibility Notes

- Cameras are only usable for talkback if the device reports `TalkAbility` with `audioType=adpcm`.
- Firmware differences exist. This integration tries to pick `FDX` + `mixAudioStream` automatically when supported.
- If a camera is offline during startup, it may still show as available; the definitive check happens when you actually play media.
- All data handed to the AES/Baichuan layer is normalized to `bytes`
  (`ensure_bytes()` in `util.py`) — the root cause of upstream issue #6.
  A defensive `str`-accepting signature in `reolink_aio._aes_encrypt` would be
  a nice upstream hardening, but is not required.

## Debug logging

```yaml
logger:
  logs:
    custom_components.reolink_talk: debug
```

Debug logs show media/PCM/ADPCM sizes, the chosen Baichuan encryption type and
payload types — never credentials or media URLs (TTS URLs can embed auth
tokens).

## Troubleshooting

This repo includes two debug scripts (optional):

- `scripts/reolink_talk_debug.py`: send a sine tone or a file to a specific camera using the same stored credentials as HA.
- `scripts/reolink_talk_e2e_capture_test.py`: capture RTSP audio while sending talk to confirm speaker output is present.

## Development

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-test.txt   # Windows: .venv/Scripts/pip
pytest -v
ruff check . && ruff format --check .
```

CI runs hassfest, HACS validation, ruff and pytest (Python 3.13/3.14) on every
push and pull request.

## License

MIT. See `LICENSE`. Original work © [@joeblack2k](https://github.com/joeblack2k).
