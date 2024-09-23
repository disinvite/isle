import pytest
from isledecomp.compare.dudu import DudyCore


@pytest.fixture(name="db")
def fixture_db() -> DudyCore:
    yield DudyCore()


def test_at_without_side_effect(db):
    """The at() methods will not cause a record to be inserted immediately,
    unless you call set() on the object. get() does not insert."""
    # Ensure that get() does not insert a record
    assert db.get(source=0x1234) is None
    assert db.get(source=0x1234) is None

    # Still no record after calling at()
    db.at_source(0x1234)
    assert db.get(source=0x1234) is None

    # Record saved if we call set()
    db.at_source(0x1234).set()
    assert db.get(source=0x1234) is not None


def test_collision(db):
    db.at_source(0x1234).set(test=100)
    db.at_target(0x5555).set(source=0x1234, test=200)
    assert db.get(source=0x1234).get("test") == 100
