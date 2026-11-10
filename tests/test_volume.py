"""Regression test: set_volume must not raise on cameras without HTTP (Baichuan only)."""

from __future__ import annotations

import asyncio
import sys
from types import ModuleType, SimpleNamespace

import pytest

pytest.importorskip("homeassistant.components.media_player")  # needs real HA (test-ha CI job)

from custom_components.reolink_talk.media_player import ReolinkTalkPlayer, ReolinkTarget  # noqa: E402


class FakeReolinkError(Exception):
    pass


def _install_fake_reolink_aio(monkeypatch, host_cls) -> None:
    exceptions = ModuleType("reolink_aio.exceptions")
    exceptions.ReolinkError = FakeReolinkError
    exceptions.NotSupportedError = type("NotSupportedError", (FakeReolinkError,), {})
    exceptions.InvalidParameterError = type("InvalidParameterError", (FakeReolinkError,), {})
    api = ModuleType("reolink_aio.api")
    api.Host = host_cls
    package = ModuleType("reolink_aio")
    monkeypatch.setitem(sys.modules, "reolink_aio", package)
    monkeypatch.setitem(sys.modules, "reolink_aio.api", api)
    monkeypatch.setitem(sys.modules, "reolink_aio.exceptions", exceptions)


def _make_player():
    player = SimpleNamespace(
        _target=ReolinkTarget(
            host="camera.invalid",
            http_port=None,
            use_https=None,
            port=9000,
            username="u",
            password="p",
            title="t",
            channel=0,
        ),
        _lock=asyncio.Lock(),
        hass=object(),
        entity_id="media_player.test",
        _attr_volume_level=None,
        async_write_ha_state=lambda: None,
    )
    return player


class LoginFailingHost:
    logout_called = False

    def __init__(self, **kwargs) -> None:
        pass

    async def login(self) -> None:
        raise FakeReolinkError("HTTP disabled")

    async def set_volume(self, channel, volume_speak=None) -> None:
        raise AssertionError("set_volume must not be reached after a failed login")

    async def logout(self) -> None:
        LoginFailingHost.logout_called = True


async def test_set_volume_survives_failed_http_login(monkeypatch):
    _install_fake_reolink_aio(monkeypatch, LoginFailingHost)
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.aiohttp_client",
        SimpleNamespace(async_get_clientsession=lambda hass: None),
    )
    player = _make_player()

    await ReolinkTalkPlayer.async_set_volume_level(player, 0.4)

    assert player._attr_volume_level == pytest.approx(0.4)
    assert LoginFailingHost.logout_called
