'''
Exports FileBuffer.
The extra Window classes should be considered implementation details.
'''

import os

class Window(object):
    ''' Represents a range, which has size and offset. '''

    def __init__(self, start_offset, size):
        self._start_offset = start_offset
        self._size = size

    def get_start_offset(self):
        ''' Gets the start offset. '''
        return self._start_offset

    def set_start_offset(self, value):
        ''' Sets the start offset. '''
        self._start_offset = value

    def get_end_offset(self):
        ''' Gets the end offset. '''
        return self._start_offset + self._size

    def set_end_offset(self, value):
        ''' Sets the end offset. '''
        self._start_offset = value - self._size

    def get_size(self):
        ''' Gets the window size. '''
        return self._size

    def set_size(self, value):
        ''' Sets the window size. '''
        self._size = value

    def __repr__(self):
        return 'Window(%d,%d)' % (self.start_offset, self._size)

    def __contains__(self, offset):
        return offset in range(self.start_offset, self.end_offset + 1)

    start_offset = property(get_start_offset, set_start_offset)
    end_offset = property(get_end_offset, set_end_offset)
    size = property(get_size, set_size)

class ContentWindow(Window):
    ''' A Window that has some content. '''

    def get(self, offset, size):
        ''' Retrieves content chunk of given size at a given offset. '''
        raise NotImplementedError()

    def clone(self, offset, size):
        ''' Returns "substring" ContentWindow. '''
        raise NotImplementedError()

class BufferContentWindow(ContentWindow):
    ''' A Window that has content placed in the memory. '''

    def __init__(self, offset, buffer):
        super().__init__(offset, len(buffer))
        self._buffer = buffer

    def get(self, offset, size):
        ''' Retrieves content chunk of given size at a given offset. '''
        assert offset in self
        assert offset + size in self
        return self._buffer[offset-self.start_offset:offset-self.start_offset+size]

    def clone(self, offset, size):
        ''' Returns "substring" BufferContentWindow. '''
        return BufferContentWindow(offset, self.get(offset, size))

    def __repr__(self):
        return 'BufferContentWindow(%d,%r)' % (self.start_offset, self._buffer)

    def __eq__(self, other):
        return isinstance(other, BufferContentWindow) \
            and self.start_offset == other.start_offset \
            and self.size == other.size \
            and self._buffer == other.buffer

    buffer = property(lambda self: self._buffer)

class FileContentWindow(ContentWindow):
    ''' A Window that has content placed within a physical file. '''

    def __init__(self, offset, size, file_handle, file_offset):
        super().__init__(offset, size)
        self._file_offset = file_offset
        self._handle = file_handle

    def get(self, offset, size):
        ''' Retrieves content chunk of given size at a given offset. '''
        assert offset in self
        assert offset + size in self
        self._handle.seek(
            self._file_offset + offset - self.start_offset, os.SEEK_SET)
        return self._handle.read(size)

    def clone(self, offset, size):
        ''' Returns "substring" FileContentWindow. '''
        return FileContentWindow(
            offset,
            size,
            self._handle,
            self._file_offset + offset - self.start_offset)

    def __repr__(self):
        return 'FileContentWindow(%d,%d,0x%x,%d)' % (
            self.start_offset, self._size, id(self._handle), self._file_offset)

class FileBuffer(object):
    '''
    The file buffer class.

    It implements large file support by dividing the file into dynamic ranges
    (windows). By default, the whole file is represented by one big content window
    that uses the underlying file to look up things.

    Editing the file, rather than operating on the HDD or placing the whole thing
    into the RAM, manipulates those content windows. When the user enters a text,
    the buffer splits existing content windows and introduces a new window that
    holds the text supplied by the user in the RAM.

    When the UI requests the file buffer to provide content at specific offset and
    of specific size, the file buffer "compiles" the final output by iterating over
    the relevant windows.
    '''

    def __init__(self, path=None):
        if not path:
            self._windows = []
            self._path = None
            return
        self._handle = open(path, 'rb')
        self._path = path
        self._handle.seek(0, os.SEEK_END)
        size = self._handle.tell()
        self._handle.seek(0, os.SEEK_SET)
        self._windows = [FileContentWindow(0, size, self._handle, 0)]

    def __destroy__(self):
        self._handle.close()

    def insert(self, offset, new_content):
        ''' Inserts new content at a specified position. '''
        self._insert(offset, new_content)
        self._optimize_windows()

    def _insert(self, offset, new_content):
        assert offset in Window(0, self.size)
        if not new_content:
            return
        for i, window in enumerate(self._windows):
            if window.start_offset == offset:
                self._windows.insert(i, BufferContentWindow(offset, new_content))
                for j in range(i+1, len(self._windows)):
                    self._windows[j].start_offset += len(new_content)
                return
            if window.end_offset == offset:
                self._windows.insert(i+1, BufferContentWindow(offset, new_content))
                for j in range(i+2, len(self._windows)):
                    self._windows[j].start_offset += len(new_content)
                return
            if offset in window:
                self._windows[i] = window.clone(
                    window.start_offset, offset - window.start_offset)
                self._windows.insert(
                    i + 1, BufferContentWindow(offset, new_content))
                self._windows.insert(
                    i + 2, window.clone(
                        offset, window.size - (offset - window.start_offset)))
                for j in range(i+2, len(self._windows)):
                    self._windows[j].start_offset += len(new_content)
                return
        self._windows.append(BufferContentWindow(offset, new_content))

    def delete(self, offset, size):
        ''' Deletes a part of content at a specified position. '''
        self._delete(Window(offset, min(self.size - offset, size)))
        self._refresh_offsets()
        self._optimize_windows()

    def _delete(self, window):
        assert window.start_offset in Window(0, self.size)
        assert window.end_offset in Window(0, self.size)
        if not window.size:
            return
        min_range_idx = None
        max_range_idx = None
        for i, other_window in enumerate(self._windows):
            if window.start_offset in other_window and min_range_idx is None:
                min_range_idx = i
            if window.end_offset in other_window:
                max_range_idx = i

        if min_range_idx == max_range_idx:
            chosen_window = self._windows[min_range_idx]
            left_range = chosen_window.clone(
                chosen_window.start_offset,
                window.start_offset - chosen_window.start_offset)
            right_range = chosen_window.clone(
                window.end_offset,
                chosen_window.end_offset - window.end_offset)
            self._windows.pop(min_range_idx)
            self._windows.insert(min_range_idx, left_range)
            self._windows.insert(min_range_idx + 1, right_range)
            return

        if min_range_idx is not None:
            min_range = self._windows[min_range_idx]
            min_range = min_range.clone(
                min_range.start_offset, window.start_offset - min_range.start_offset)
            self._windows[min_range_idx] = min_range

        if max_range_idx is not None:
            max_range = self._windows[max_range_idx]
            delta = window.start_offset + window.size - max_range.start_offset
            if delta != max_range.size:
                max_range = max_range.clone(
                    max_range.start_offset + delta, max_range.size - delta)
            self._windows[max_range_idx] = max_range

        self._windows = [
            other_window for other_window in self._windows \
                if other_window.start_offset not in window \
                or other_window.end_offset not in window]

    def _refresh_offsets(self):
        offset = 0
        for window in self._windows:
            window.start_offset = offset
            offset += window.size

    def _optimize_windows(self):
        self._windows = [window for window in self._windows if window.size > 0]

    def replace(self, offset, new_content):
        ''' Overrides content with new content at a specified position. '''
        self.delete(offset, len(new_content))
        self.insert(offset, new_content)

    def get(self, offset, size):
        ''' Retrieves content at specified position and size. '''
        return self._get(Window(offset, size))

    def _get(self, window):
        buffer = b''
        left = window.size
        for other_window in self._windows:
            if window.start_offset in other_window:
                to_get = min(
                    other_window.size \
                        + other_window.start_offset \
                        - window.start_offset,
                    left)
                buffer += other_window.get(window.start_offset, to_get)
                left -= to_get
            elif window.end_offset in other_window:
                to_get = min(other_window.size, left)
                buffer += other_window.get(other_window.start_offset, to_get)
                left -= to_get
            else:
                if other_window.start_offset in window \
                        and other_window.end_offset in window:
                    buffer += other_window.get(
                        other_window.start_offset, other_window.size)
                    left -= other_window.size
            if not left:
                break
        assert len(buffer) == window.size
        return buffer

    def get_path(self):
        ''' Returns the path to the file. '''
        return self._path

    def get_size(self):
        ''' Returns the file size. '''
        return sum(window.size for window in self._windows)

    size = property(get_size)
    path = property(get_path)
    windows = property(lambda self: self._windows)
