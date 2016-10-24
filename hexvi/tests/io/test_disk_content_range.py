from io import BytesIO
import pytest
from hexvi.io.disk_content_range import DiskContentRange


def test_read_bytes_returns_substrings() -> None:
    with BytesIO(b'abcd') as stream:
        range_ = DiskContentRange(0, 3, stream, 0)
        assert range_.read_bytes(0, 3) == b'abc'
        assert range_.read_bytes(1, 2) == b'bc'
        assert range_.read_bytes(2, 1) == b'c'
        assert range_.read_bytes(1, 1) == b'b'
        range_ = DiskContentRange(0, 3, stream, 1)
        assert range_.read_bytes(0, 3) == b'bcd'
        assert range_.read_bytes(1, 2) == b'cd'
        assert range_.read_bytes(2, 1) == b'd'
        assert range_.read_bytes(1, 1) == b'c'


def test_read_bytes_raises_for_invalid_offsets() -> None:
    with BytesIO(b'abcd') as stream:
        range_ = DiskContentRange(1, 4, stream, 0)
        with pytest.raises(AssertionError):
            range_.read_bytes(1, 5)
        with pytest.raises(AssertionError):
            range_.read_bytes(0, 1)
        with pytest.raises(AssertionError):
            range_.read_bytes(5, 1)
    with BytesIO(b'abcd') as stream:
        range_ = DiskContentRange(1, 4, stream, 1)
        with pytest.raises(AssertionError):
            range_.read_bytes(1, 5)
        with pytest.raises(AssertionError):
            range_.read_bytes(0, 1)
        with pytest.raises(AssertionError):
            range_.read_bytes(5, 1)


def test_get_narrowed_returns_subranges() -> None:
    with BytesIO(b'abcde') as stream:
        range1 = DiskContentRange(1, 4, stream, 0)
        range2 = range1.get_narrowed(2, 3)
        assert range2.start_offset == 2
        assert range2.end_offset == 5
        assert range2.size == 3
        assert range2.read_bytes(2, 3) == b'bcd'

        range1 = DiskContentRange(1, 4, stream, 1)
        range2 = range1.get_narrowed(2, 3)
        assert range2.start_offset == 2
        assert range2.end_offset == 5
        assert range2.size == 3
        assert range2.read_bytes(2, 3) == b'cde'


def test_get_narrowed_raises_for_invalid_offsets() -> None:
    with BytesIO(b'abcd') as stream:
        range_ = DiskContentRange(1, 4, stream, 0)
        with pytest.raises(AssertionError):
            range_.get_narrowed(1, 5)
        with pytest.raises(AssertionError):
            range_.get_narrowed(0, 1)
        with pytest.raises(AssertionError):
            range_.get_narrowed(5, 1)
