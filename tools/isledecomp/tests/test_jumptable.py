import os
import pytest
from isledecomp.compare.asm.parse import ParseAsm
from isledecomp.compare.asm.partition import Partition, PartType


@pytest.fixture(name="part")
def fixture_part():
    return Partition(0, 1000)


def test_partition_merge(part):
    """CODE cuts should merge together, but not JUMP or DATA."""
    assert list(part.get_all()) == [(0, 1000, PartType.CODE, 0)]
    part.cut_code(500)
    assert list(part.get_all()) == [(0, 1000, PartType.CODE, 0)]

    part.cut_jump(700)
    part.cut_jump(900)
    assert list(part.get_all()) == [
        (0, 700, PartType.CODE, 0),
        (700, 200, PartType.JUMP, 0),
        (900, 100, PartType.JUMP, 1),
    ]


def test_partition_cut(part):
    part.cut_jump(500)
    assert list(part.get_all()) == [
        (0, 500, PartType.CODE, 0),
        (500, 500, PartType.JUMP, 0),
    ]


def test_partition_clobber(part):
    part.cut_jump(500)
    part.cut_data(500)
    assert list(part.get_all()) == [
        (0, 500, PartType.CODE, 0),
        (500, 500, PartType.DATA, 0),
    ]


def test_partition_labels(part):
    """Should correctly pair up jump tables and switch data.
    By nature switch data comes before any jump, so we can increment our index
    if we read one, then remember not to increment again on the jump table."""

    # These are paired up according to the order they are read, not the address
    # order of the items.
    part.cut_jump(500)  # 0
    part.cut_data(900)  # 1
    part.cut_jump(700)  # 1
    part.cut_jump(800)  # 2

    assert list(part.get_all()) == [
        (0, 500, PartType.CODE, 0),
        (500, 200, PartType.JUMP, 0),
        (700, 100, PartType.JUMP, 1),
        (800, 100, PartType.JUMP, 2),
        (900, 100, PartType.DATA, 1),
    ]


####


@pytest.fixture(name="score_notify")
def fixture_score_notify():
    """Read the function Score::Notify from v.addr 0x10001410.
    This is a sample function that includes a jump table and switch data."""
    path = os.path.join(os.path.dirname(__file__), "score_notify.bin")
    with open(path, "rb") as f:
        data = f.read()

    return data


def test_score_partition(score_notify):
    p = ParseAsm()
    p.parse_asm(score_notify, 0x10001410)
    parts = list(p.partition.get_all())

    # TODO: DATA part will include the 0xcc padding bytes
    assert parts == [
        (0x10001410, 196, PartType.CODE, 0),
        (0x100014D4, 24, PartType.JUMP, 0),
        (0x100014EC, 36, PartType.DATA, 0),
    ]


# fmt: off
SIMPLE_CASE = b"".join([
#start (0x1000)
    b"\x8b\x74\x24\x04",                # mov esi, dword ptr [esp + 4]
    b"\xff\x24\xb5\x1a\x10\x00\x00",    # jmp dword ptr [esi*0x4 + 0x101a]
#case (0x100b)
    b"\x31\xc0",                        # xor eax,eax
    b"\xc3",                            # ret
#case (0x100e)
    b"\xb8\x01\x00\x00\x00",            # mov eax, 0x1
    b"\xc3",                            # ret
#case (0x1014)
    b"\xb8\x02\x00\x00\x00",            # mov eax, 0x2
    b"\xc3",                            # ret
#table (0x101a)
    b"\x0b\x10\x00\x00",
    b"\x0e\x10\x00\x00",
    b"\x14\x10\x00\x00",
])
# fmt: on


def test_simple_case_internals():
    p = ParseAsm()
    p.parse_asm(SIMPLE_CASE, 0x1000)
    assert list(p.partition.get_all()) == [
        (0x1000, 26, PartType.CODE, 0),
        (0x101A, 12, PartType.JUMP, 0),
    ]

    assert 0x100B in p.labels
    assert 0x100E in p.labels
    assert 0x1014 in p.labels
    assert 0x101A in p.labels


def test_simple_case_output():
    p = ParseAsm()
    lines = [line for (_, line) in p.parse_asm(SIMPLE_CASE, 0x1000)]

    assert "case" in lines[2]
    assert "case" in lines[5]
    assert "case" in lines[8]
    assert "table" in lines[11]


# TODO: hypothetical case where we have CODE JUMP CODE
# can detect code start by looking at jump addresses.

# Test case: 3 jump tables
# 0x1006f080  Infocenter::HandleEndAction

# TODO: jump table and data table index matchup.
