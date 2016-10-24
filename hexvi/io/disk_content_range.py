import os
import io
from typing import Any
from typing.io import IO
from hexvi.io.content_range import ContentRange


class DiskContentRange(ContentRange):
    def __init__(
            self,
            offset: int,
            size: int,
            file_handle: IO[Any],
            file_offset: int) -> None:
        super().__init__(offset, size)

        self._file_offset = file_offset
        self._handle = file_handle

    def read_bytes(self, offset: int, size: int) -> bytes:
        assert offset in self
        assert offset + size in self
        self._handle.seek(
            self._file_offset + offset - self.start_offset,
            os.SEEK_SET)
        return self._handle.read(size)

    def get_narrowed(self, offset: int, size: int) -> 'DiskContentRange':
        assert offset in self
        assert offset + size in self
        return DiskContentRange(
            offset,
            size,
            self._handle,
            self._file_offset + offset - self.start_offset)
