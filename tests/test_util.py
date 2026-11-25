"""Tests for the ensure_bytes helper."""

from __future__ import annotations

import pytest

from custom_components.reolink_talk.util import ensure_bytes, parse_local_media_source_id


def test_parse_local_media_source_id_uses_first_path_element_as_directory_id():
    """The standard README URI must resolve to the configured `local` dir."""
    assert parse_local_media_source_id("media-source://media_source/local/doorbell_absent.mp3") == (
        "local",
        "doorbell_absent.mp3",
    )
    assert parse_local_media_source_id("media-source://media_source/nas/doorbells/front.mp3") == (
        "nas",
        "doorbells/front.mp3",
    )
    assert parse_local_media_source_id("https://example.invalid/chime.mp3") is None


@pytest.mark.parametrize(
    "media_id",
    (
        "media-source://media_source/",
        "media-source://media_source/local",
        "media-source://media_source//doorbell.mp3",
    ),
)
def test_parse_local_media_source_id_rejects_missing_directory_or_path(media_id):
    with pytest.raises(ValueError, match="Invalid local media-source ID"):
        parse_local_media_source_id(media_id)


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
