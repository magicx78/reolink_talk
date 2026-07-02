"""Small dependency-free helpers for reolink_talk."""

from __future__ import annotations


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
