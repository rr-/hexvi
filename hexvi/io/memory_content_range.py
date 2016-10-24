from hexvi.io.content_range import ContentRange
from typing import Any


class MemoryContentRange(ContentRange):
    def __init__(self, offset: int, buffer: bytes) -> None:
        super().__init__(offset, len(buffer))
        self.buffer = buffer

    def read_bytes(self, offset: int, size: int) -> bytes:
        assert offset in self
        assert offset + size in self
        buffer_start = offset - self.start_offset
        buffer_end = buffer_start + size
        return self.buffer[buffer_start:buffer_end]

    def get_narrowed(self, offset: int, size: int) -> 'MemoryContentRange':
        assert offset in self
        assert offset + size in self
        return MemoryContentRange(offset, self.read_bytes(offset, size))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, MemoryContentRange) \
            and self.start_offset == other.start_offset \
            and self.size == other.size \
            and self.buffer == other.buffer

    def __repr__(self) -> str:
        return '%s(%d,%r)' % (
            self.__class__.__name__, self.start_offset, self.buffer)
