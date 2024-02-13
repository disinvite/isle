import os
import pytest
from isledecomp.compare.asm.parse import ParseAsm
from isledecomp.compare.asm.partition import Partition, PartType


@pytest.fixture(name="part")
def fixture_part():
    return Partition(0, 1000)


def test_partition_basic(part):
    """Cuts of the same type should merge together."""
    assert list(part.get_all()) == [(0, 1000, PartType.CODE)]
    part.cut_code(500)
    assert list(part.get_all()) == [(0, 1000, PartType.CODE)]


def test_partition_cut(part):
    part.cut_jump(500)
    assert list(part.get_all()) == [(0, 500, PartType.CODE), (500, 500, PartType.JUMP)]


def test_partition_clobber(part):
    part.cut_jump(500)
    part.cut_data(500)
    assert list(part.get_all()) == [(0, 500, PartType.CODE), (500, 500, PartType.DATA)]


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
        (0x10001410, 196, PartType.CODE),
        (0x100014D4, 24, PartType.JUMP),
        (0x100014EC, 36, PartType.DATA),
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
        (0x1000, 26, PartType.CODE),
        (0x101A, 12, PartType.JUMP),
    ]

    assert 0x100B in p.labels
    assert 0x100E in p.labels
    assert 0x1014 in p.labels
    assert 0x101A in p.labels


def test_simple_case_output():
    p = ParseAsm()
    lines = p.parse_asm(SIMPLE_CASE, 0x1000)

    assert "case" in lines[2]
    assert "case" in lines[5]
    assert "case" in lines[8]
    assert "table" in lines[11]


# TODO: 2 jump tables in one function
# TODO: hypothetical case where we have CODE JUMP CODE
# can detect code start by looking at jump addresses.
