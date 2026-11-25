"""Small dependency-free helpers for reolink_talk."""

from __future__ import annotations


LOCAL_MEDIA_SOURCE_PREFIX = "media-source://media_source/"


def parse_local_media_source_id(media_id: str) -> tuple[str, str] | None:
    """Parse a Home Assistant local-media URI into directory ID and path.

    Home Assistant encodes local media as
    ``media-source://media_source/<directory-id>/<relative-path>``.  The
    first ``local`` in the standard ``.../local/file.mp3`` form is therefore
    the directory ID, not part of the path.
    """
    if not media_id.startswith(LOCAL_MEDIA_SOURCE_PREFIX):
        return None

    identifier = media_id.removeprefix(LOCAL_MEDIA_SOURCE_PREFIX)
    directory_id, separator, relative_path = identifier.partition("/")
    if not directory_id or not separator or not relative_path:
        raise ValueError(f"Invalid local media-source ID: {media_id!r}")

    return directory_id, relative_path


def ensure_bytes(value: bytes | bytearray | memoryview | str, *, name: str = "value") -> bytes:
    """Return value as bytes.

    bytes are returned unchanged, bytearray/memoryview are copied to bytes and
    str is UTF-8 encoded. Anything else (including None) raises a TypeError
    with a clear message instead of the opaque Cryptodome error
    "Object type <class 'str'> cannot be passed to C code".
    """
    if isinstance(value, bytes):
        return value
    if isinstance(value, (bytearray, memoryview)):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    raise TypeError(f"{name} must be bytes, bytearray, or str; got {type(value).__name__}")
