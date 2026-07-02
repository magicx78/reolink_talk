## Reolink Talk (Two-Way Audio)

**Maintained fork** of [joeblack2k/reolink_talk](https://github.com/joeblack2k/reolink_talk) —
fixes the `TypeError: Object type <class 'str'> cannot be passed to C code`
crash on current Home Assistant (upstream issue #6), the broken HACS install
(#1) and RLC-811A rspCode 421 handling (#5).

Adds a `media_player` per selected Reolink camera (from the official integration) so you can play MP3/WAV/TTS to the camera speaker.

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=reolink_talk)
