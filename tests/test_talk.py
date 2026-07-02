"""Tests for talk.py payload preparation and Baichuan frame sending.

Includes the regression test for upstream issue #6:
https://github.com/joeblack2k/reolink_talk/issues/6
(TypeError: Object type <class 'str'> cannot be passed to C code, caused by
passing the Extension XML as str to Baichuan._aes_encrypt).
"""

from __future__ import annotations

from reolink_aio.baichuan import util as bc_util

from custom_components.reolink_talk.talk import (
    BC_MESSAGE_CLASS_1464,
    bcmedia_adpcm_packet,
    send_talk_binary,
    talk_binary_payload,
)

HEADER_LEN = 24  # magic(4) + cmd_id(4) + mess_len(4) + ch_id(1) + mess_id(3) + class(4) + payload_offset(4)


async def test_send_talk_binary_passes_bytes_to_aes_encrypt(bc):
    """Regression for issue #6: ext must reach _aes_encrypt as bytes.

    The FakeBaichuan raises the same TypeError as Cryptodome when it sees a
    str, so this test failing loudly means the str leak is back.
    """
    payload = b"\x00" * 40
    await send_talk_binary(bc, 0, payload, enc_type=bc_util.EncType.AES)

    assert len(bc.aes_calls) == 1
    ext_arg = bc.aes_calls[0]
    assert isinstance(ext_arg, bytes)
    assert b"<binaryData>1</binaryData>" in ext_arg
    assert b"<channelId>0</channelId>" in ext_arg


async def test_send_talk_binary_packet_layout(bc):
    payload = b"\xaa" * 32
    await send_talk_binary(bc, 0, payload, enc_type=bc_util.EncType.AES)

    assert len(bc._transport.written) == 1
    packet = bc._transport.written[0]
    assert isinstance(packet, bytes)

    enc_ext = b"ENC:" + bc.aes_calls[0]  # what the fake _aes_encrypt returned

    magic = bytes.fromhex(bc_util.HEADER_MAGIC)
    assert packet[: len(magic)] == magic
    cmd_id = int.from_bytes(packet[4:8], "little")
    mess_len = int.from_bytes(packet[8:12], "little")
    ch_id = packet[12]
    mess_id = int.from_bytes(packet[13:16], "little")
    mess_class = packet[16:20]
    payload_offset = int.from_bytes(packet[20:24], "little")

    assert cmd_id == 202
    assert ch_id == 1  # channel 0 -> ch_id 1
    assert mess_id == 1  # incremented from 0
    assert bc._mess_id == 1
    assert mess_class == BC_MESSAGE_CLASS_1464
    assert payload_offset == len(enc_ext)
    assert mess_len == len(enc_ext) + len(payload)
    assert packet[HEADER_LEN : HEADER_LEN + len(enc_ext)] == enc_ext
    assert packet[HEADER_LEN + len(enc_ext) :] == payload
    assert len(packet) == HEADER_LEN + mess_len


async def test_send_talk_binary_explicit_mess_id(bc):
    await send_talk_binary(bc, 0, b"\x00" * 8, mess_id=42, enc_type=bc_util.EncType.AES)
    packet = bc._transport.written[0]
    assert int.from_bytes(packet[13:16], "little") == 42
    assert bc._mess_id == 42


async def test_send_talk_binary_bc_enctype_uses_encrypt_baichuan(bc):
    """The BC path goes through reolink_aio's encrypt_baichuan (str-safe)."""
    payload = b"\x55" * 16
    await send_talk_binary(bc, 0, payload, enc_type=bc_util.EncType.BC)

    assert bc.aes_calls == []  # _aes_encrypt must not be involved
    assert len(bc._transport.written) == 1
    packet = bc._transport.written[0]
    assert isinstance(packet, bytes)
    assert packet.endswith(payload)


async def test_send_talk_binary_logs_in_when_needed(bc):
    bc._logged_in = False
    await send_talk_binary(bc, 0, b"\x00" * 8, enc_type=bc_util.EncType.AES)
    assert bc.login_calls == 1


async def test_send_talk_binary_modern_connection_layer(bc_modern):
    """Regression: reolink_aio >= 0.21 has no _mutex/_transport on Baichuan.

    The plumbing moved into bc._connection; send_talk_binary must use its
    send() instead of the old attributes ('Baichuan' object has no attribute
    '_mutex' on current Home Assistant otherwise).
    """
    payload = b"\xaa" * 32
    await send_talk_binary(bc_modern, 0, payload, enc_type=bc_util.EncType.AES)

    assert len(bc_modern._connection.sent) == 1
    data, cmd_id, full_mess_id, channel = bc_modern._connection.sent[0]
    assert cmd_id == 202
    assert channel == 0
    # full_mess_id = ch_id byte + 3 mess_id bytes, little-endian
    assert full_mess_id == int.from_bytes(bytes([1]) + (1).to_bytes(3, "little"), "little")
    assert isinstance(bc_modern.aes_calls[0], bytes)
    assert data.endswith(payload)


async def test_send_talk_binary_same_packet_on_both_layouts(bc, bc_modern):
    """Old-layout and new-layout Baichuan must produce identical wire bytes."""
    payload = b"\x42" * 24
    await send_talk_binary(bc, 3, payload, enc_type=bc_util.EncType.AES)
    await send_talk_binary(bc_modern, 3, payload, enc_type=bc_util.EncType.AES)

    legacy_packet = bc._transport.written[0]
    modern_packet = bc_modern._connection.sent[0][0]
    assert legacy_packet == modern_packet


async def test_send_talk_binary_against_real_baichuan_class():
    """Drive send_talk_binary through the REAL reolink_aio Baichuan class.

    Only the network layer is replaced. Catches drift in reolink_aio's
    private attribute layout (like the 0.21 connection refactor) that pure
    fakes cannot see.
    """
    from reolink_aio.baichuan.baichuan import Baichuan

    class RecordingConnection:
        def __init__(self):
            self.sent = []

        async def send(self, data, cmd_id, full_mess_id, channel=None, log_mess=""):
            self.sent.append((data, cmd_id, full_mess_id, channel))
            return (b"", 0, b"")

    bc = Baichuan("127.0.0.1", "user", "pass", None)
    bc._aes_key = b"0123456789abcdef"  # 128-bit key for the real _aes_encrypt
    bc._logged_in = True
    conn = RecordingConnection()
    bc._connection = conn

    async def _no_connect():
        return None

    bc._connect_if_needed = _no_connect

    payload = b"\x00" * 16
    await send_talk_binary(bc, 0, payload, enc_type=bc_util.EncType.AES)

    assert len(conn.sent) == 1
    data, cmd_id, _full_mess_id, channel = conn.sent[0]
    assert cmd_id == 202
    assert channel == 0
    assert data.endswith(payload)


def test_talk_binary_payload_grouping():
    """AES payload prep: 9 blocks are grouped [4, 4, 1], all bytes."""
    full_block_size = 8
    adpcm = bytes(range(256))[: full_block_size * 9]

    payloads = talk_binary_payload(adpcm, full_block_size, blocks_per_payload=4)

    assert [count for _, count in payloads] == [4, 4, 1]
    for payload, count in payloads:
        assert isinstance(payload, bytes)
        # each block is wrapped: 12-byte BcMedia header + block (+ padding to 8)
        expected_packet = len(bcmedia_adpcm_packet(adpcm[:full_block_size]))
        assert len(payload) == expected_packet * count


def test_talk_binary_payload_drops_incomplete_trailing_block():
    full_block_size = 8
    adpcm = b"\x01" * (full_block_size * 2 + 3)  # 2 full blocks + 3 stray bytes
    payloads = talk_binary_payload(adpcm, full_block_size)
    assert [count for _, count in payloads] == [2]
