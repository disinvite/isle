import pytest
import sqlite3
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
    """Merging of records is not yet possible."""
    db.at_source(0x1234).set(test=100)
    with pytest.raises(sqlite3.IntegrityError):
        db.at_target(0x5555).set(source=0x1234, test=200)
    # Should fail and not update the non-unique values. source=0x1234 retains its "test" value of 100.
    assert db.get(source=0x1234).get("test") == 100


def test_anchor_param_override(db):
    """at() specifies the "anchor" param that will uniquely identify this entry if it is unset.
    What happens if we override that value in the call to set()?"""
    db.at_source(0x1234).set(source=0x5555)
    # The anchor value is preferred over the new value.
    # This is the same behavior as if we tried to reassign the source addr later.
    assert db.get(source=0x1234) is not None
    assert db.get(source=0x5555) is None


def test_get_param_precedence(db):
    """If multiple params are provided to get(), we check in this order: source, target, symbol."""
    # Set up three distinct entries
    db.at_source(1).set()
    db.at_target(2).set()
    db.at_symbol("test").set()

    # Source over target
    assert db.get(source=1, target=2).source == 1
    # Order of params does not matter
    assert db.get(target=2, source=1).source == 1
    # Source over any
    assert db.get(source=1, target=2, symbol="test").source == 1
    # Target over symbol
    assert db.get(target=2, symbol="test").target == 2
    # Symbol on its own
    assert db.get(symbol="test").symbol == "test"
