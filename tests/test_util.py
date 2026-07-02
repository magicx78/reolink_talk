"""Tests for the ensure_bytes helper."""

from __future__ import annotations

import pytest

from custom_components.reolink_talk.util import ensure_bytes


def test_ensure_bytes_bytes_passthrough():
    value = b"\x00\x01payload"
    assert ensure_bytes(value) is value


def test_ensure_bytes_bytearray_and_memoryview():
    assert ensure_bytes(bytearray(b"abc")) == b"abc"
    assert ensure_bytes(memoryview(b"abc")) == b"abc"
    assert isinstance(ensure_bytes(bytearray(b"abc")), bytes)
    assert isinstance(ensure_bytes(memoryview(b"abc")), bytes)


def test_ensure_bytes_str_utf8():
    assert ensure_bytes("äöü") == "äöü".encode("utf-8")
    assert ensure_bytes("<Extension/>") == b"<Extension/>"


@pytest.mark.parametrize("bad", [None, 123, 1.5, ["a"], {"a": 1}])
def test_ensure_bytes_rejects_unexpected_types(bad):
    with pytest.raises(TypeError, match="must be bytes"):
        ensure_bytes(bad)


def test_ensure_bytes_error_message_includes_name():
    with pytest.raises(TypeError, match="extension XML"):
        ensure_bytes(None, name="extension XML")
