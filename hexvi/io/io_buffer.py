import os
import shutil
from hexvi.io.range import Range
from hexvi.io.content_range import ContentRange
from hexvi.io.memory_content_range import MemoryContentRange
from hexvi.io.disk_content_range import DiskContentRange
from typing import Optional, List, Any


'''
The class maintains continuous sequence of ContentRanges to describe
the file content.
'''
class IOBuffer:
    def __init__(self, path: Optional[str]=None) -> None:
        if not path:
            self._content_ranges = []  # type: List[ContentRange]
            self._handle = None  # type: Optional[Any]
            self._path = None  # type: Optional[str]
            return
        self._handle = open(path, 'rb')
        self._path = path
        self._handle.seek(0, os.SEEK_END)
        size = self._handle.tell()
        self._handle.seek(0, os.SEEK_SET)
        self._content_ranges = [DiskContentRange(0, size, self._handle, 0)]

    def __destroy__(self) -> None:
        if self._handle:
            self._handle.close()

    @property
    def size(self) -> int:
        return sum(range_.size for range_ in self._content_ranges)

    @property
    def path(self) -> Optional[str]:
        return self._path

    def insert(self, offset: int, new_content: bytes) -> None:
        assert offset in range(0, self.size + 1)
        if not new_content:
            return

        for i, content_range in enumerate(self._content_ranges):
            if offset in content_range:
                left_size = offset - content_range.start_offset
                right_size = content_range.size - left_size

                left_range = content_range.get_narrowed(
                    content_range.start_offset, left_size)
                right_range = content_range.get_narrowed(
                    offset, right_size)
                middle_range = MemoryContentRange(offset, new_content)

                self._content_ranges[i:i+1] = [
                    left_range, middle_range, right_range]
                for range_ in self._content_ranges[i+2:]:
                    range_.start_offset += len(new_content)
                break
        else:
            self._content_ranges.append(
                MemoryContentRange(offset, new_content))

        self._optimize()

    def delete(self, offset: int, size: int) -> None:
        assert offset in range(0, self.size + 1)
        assert offset + size in range(0, self.size + 1)
        if not size:
            return

        min_range_idx = None
        max_range_idx = None
        for i, other_range in enumerate(self._content_ranges):
            if offset in other_range and min_range_idx is None:
                min_range_idx = i
            if offset + size in other_range:
                max_range_idx = i

        assert min_range_idx is not None
        assert max_range_idx is not None

        min_range = self._content_ranges[min_range_idx]
        max_range = self._content_ranges[max_range_idx]

        left_range = min_range.get_narrowed(
            min_range.start_offset, offset - min_range.start_offset)
        right_range = max_range.get_narrowed(
            offset + size, max_range.end_offset - (offset + size))

        self._content_ranges[min_range_idx:max_range_idx+1] = [
            left_range, right_range]

        offset = 0
        for content_range in self._content_ranges:
            content_range.start_offset = offset
            offset += content_range.size
        self._optimize()

    def replace(self, offset: int, new_content: bytes) -> None:
        self.delete(offset, len(new_content))
        self.insert(offset, new_content)

    def read_bytes(self, offset: int, size: int) -> bytes:
        buffer = b''
        left = size
        current_offset = offset
        for other_range in self._content_ranges:
            if current_offset in other_range \
                    or current_offset + size in other_range:
                to_get = min(
                    other_range.size
                    + other_range.start_offset
                    - current_offset,
                    left)
                buffer += other_range.read_bytes(current_offset, to_get)
                current_offset += to_get
                left -= to_get
            if not left:
                break
        assert len(buffer) == size
        return buffer

    def save_to_file(self, target_path: str, overwrite: bool) -> None:
        assert target_path
        buffer_size = 8192
        size = self.size
        saving_to_itself = os.path.exists(target_path) \
            and self.path \
            and os.path.samefile(target_path, self.path)
        if not overwrite and os.path.exists(target_path) \
                and not saving_to_itself:
            raise RuntimeError('File %r already exists' % target_path)
        temporary_path = target_path + '.hexvi-tmp'
        with open(temporary_path, 'wb') as handle:
            for offset in range(0, size, buffer_size):
                handle.write(
                    self.read_bytes(
                        offset, min(buffer_size, size - offset)))
        if saving_to_itself:
            self._handle.close()
        shutil.move(temporary_path, target_path)
        if saving_to_itself:
            self._handle = open(target_path, 'rb')

    def _optimize(self) -> None:
        self._content_ranges = [
            cr for cr in self._content_ranges if cr.size > 0]
