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
