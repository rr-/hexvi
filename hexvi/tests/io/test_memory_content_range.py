import pytest
from hexvi.io.memory_content_range import MemoryContentRange


def test_read_bytes_returns_substrings() -> None:
    range_ = MemoryContentRange(0, b'abc')
    assert range_.read_bytes(0, 3) == b'abc'
    assert range_.read_bytes(1, 2) == b'bc'
    assert range_.read_bytes(2, 1) == b'c'
    assert range_.read_bytes(1, 1) == b'b'


def test_read_bytes_raises_for_invalid_offsets() -> None:
    range_ = MemoryContentRange(1, b'abcd')
    with pytest.raises(AssertionError):
        range_.read_bytes(1, 5)
    with pytest.raises(AssertionError):
        range_.read_bytes(0, 1)
    with pytest.raises(AssertionError):
        range_.read_bytes(5, 1)


def test_get_narrowed_returns_subranges() -> None:
    range1 = MemoryContentRange(1, b'abcd')
    range2 = range1.get_narrowed(2, 3)
    assert range2.start_offset == 2
    assert range2.end_offset == 5
    assert range2.size == 3
    assert range2.read_bytes(2, 3) == b'bcd'


def test_get_narrowed_raises_for_invalid_offsets() -> None:
    range_ = MemoryContentRange(1, b'abcd')
    with pytest.raises(AssertionError):
        range_.get_narrowed(1, 5)
    with pytest.raises(AssertionError):
        range_.get_narrowed(0, 1)
    with pytest.raises(AssertionError):
        range_.get_narrowed(5, 1)
