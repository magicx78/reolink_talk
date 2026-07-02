"""Shared fixtures: a strict fake of reolink_aio's Baichuan client.

FakeBaichuan mimics the private attributes that send_talk_binary() touches on
the real reolink_aio Baichuan object. Its _aes_encrypt is intentionally
STRICTER than a plain mock: like Cryptodome's C layer it rejects anything
that is not bytes, so the regression test for upstream issue #6 fails loudly
if a str ever reaches the encryption layer again.

The test environment deliberately does NOT install homeassistant (it is
heavy and lags Python releases). The module-level homeassistant imports in
custom_components/reolink_talk are satisfied with minimal stubs; real
imports are exercised by the hassfest CI job and on a real HA instance.
"""

from __future__ import annotations

import asyncio
import sys
from types import ModuleType

import pytest


def _install_homeassistant_stubs() -> None:
    try:
        import homeassistant  # noqa: F401

        return  # real HA available -> use it
    except ImportError:
        pass

    ha = ModuleType("homeassistant")

    core = ModuleType("homeassistant.core")

    class HomeAssistant:
        pass

    core.HomeAssistant = HomeAssistant

    config_entries = ModuleType("homeassistant.config_entries")

    class ConfigEntry:
        pass

    config_entries.ConfigEntry = ConfigEntry

    helpers = ModuleType("homeassistant.helpers")
    aiohttp_client = ModuleType("homeassistant.helpers.aiohttp_client")

    def async_get_clientsession(hass):
        raise NotImplementedError("homeassistant stub: not usable in unit tests")

    aiohttp_client.async_get_clientsession = async_get_clientsession

    network = ModuleType("homeassistant.helpers.network")

    def get_url(hass, **kwargs):
        raise NotImplementedError("homeassistant stub: not usable in unit tests")

    network.get_url = get_url

    ha.core = core
    ha.config_entries = config_entries
    ha.helpers = helpers
    helpers.aiohttp_client = aiohttp_client
    helpers.network = network

    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.aiohttp_client"] = aiohttp_client
    sys.modules["homeassistant.helpers.network"] = network


_install_homeassistant_stubs()


class FakeTransport:
    def __init__(self) -> None:
        self.written: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.written.append(data)


class FakeBaichuan:
    def __init__(self) -> None:
        self._logged_in = True
        self._mess_id = 0
        self._host = "127.0.0.1"
        self._mutex = asyncio.Lock()
        self._transport = FakeTransport()
        # None forces send_talk_binary() into the simple write path
        # (no ack-future machinery), which is what unit tests want.
        self._protocol = None
        self._loop = None
        self.aes_calls: list[object] = []
        self.login_calls = 0

    def _aes_encrypt(self, body):
        self.aes_calls.append(body)
        if not isinstance(body, bytes):
            # Reproduce Cryptodome's behavior for non-bytes input (issue #6).
            raise TypeError(f"Object type {type(body)} cannot be passed to C code")
        return b"ENC:" + body

    async def _connect_if_needed(self) -> None:
        return None

    async def login(self) -> None:
        self.login_calls += 1
        self._logged_in = True


class FakeConnection:
    """Mimics reolink_aio >= 0.21 BaichuanTcpConnection/BaichuanUdpConnection."""

    def __init__(self) -> None:
        self.sent: list[tuple[bytes, int, int, int | None]] = []

    async def send(self, data, cmd_id, full_mess_id, channel=None, log_mess=""):
        assert isinstance(data, bytes)
        self.sent.append((data, cmd_id, full_mess_id, channel))
        return (b"", 0, b"")


class FakeBaichuanModern:
    """Mimics reolink_aio >= 0.21: the TCP/UDP plumbing lives in _connection.

    Deliberately does NOT define _mutex/_transport/_protocol — exactly like
    the real Baichuan class since 0.21 — so a regression back to the old
    attribute layout fails with the same AttributeError seen on real HA.
    """

    def __init__(self) -> None:
        self._logged_in = True
        self._mess_id = 0
        self._host = "127.0.0.1"
        self._connection = FakeConnection()
        self.aes_calls: list[object] = []
        self.login_calls = 0

    def _aes_encrypt(self, body):
        self.aes_calls.append(body)
        if not isinstance(body, bytes):
            raise TypeError(f"Object type {type(body)} cannot be passed to C code")
        return b"ENC:" + body

    async def _connect_if_needed(self) -> None:
        return None

    async def login(self) -> None:
        self.login_calls += 1
        self._logged_in = True


@pytest.fixture
def bc() -> FakeBaichuan:
    return FakeBaichuan()


@pytest.fixture
def bc_modern() -> FakeBaichuanModern:
    return FakeBaichuanModern()
