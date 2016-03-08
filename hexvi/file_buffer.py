import os

def point_in(checkpoint, offset, size):
  return checkpoint >= offset and checkpoint < offset + size

class Window(object):
  def __init__(self, start_offset, size):
    self._start_offset = start_offset
    self._size = size

  def get_start_offset(self):
    return self._start_offset

  def set_start_offset(self, value):
    self._start_offset = value

  def get_end_offset(self):
    return self._start_offset + self._size

  def set_end_offset(self, value):
    self._start_offset = value - self._size

  def get_size(self):
    return self._size

  def set_size(self, value):
    self._size

  def __repr__(self):
    return 'Window(%d,%d)' % (self.start_offset, self._size)

  def __contains__(self, x):
    return x in range(self.start_offset, self.end_offset + 1)

  start_offset = property(get_start_offset, set_start_offset)
  end_offset = property(get_end_offset, set_end_offset)
  size = property(get_size, set_size)

class ContentWindow(Window):
  def get(self):
    raise NotImplementedError()

  def clone(self, offset, size):
    raise NotImplementedError()

class BufferContentWindow(ContentWindow):
  def __init__(self, offset, buffer):
    super().__init__(offset, len(buffer))
    self._buffer = buffer

  def get(self, offset, size):
    assert offset in self
    assert offset + size in self
    return self._buffer[offset-self.start_offset:offset-self.start_offset+size]

  def clone(self, offset, size):
    return BufferContentWindow(offset, self.get(offset, size))

  def __repr__(self):
    return 'BufferContentWindow(%d,%r)' % (self.start_offset, self._buffer)

  def __eq__(self, other):
    return (isinstance(other, BufferContentWindow)
      and self.start_offset == other.start_offset
      and self.size == other.size
      and self._buffer == other._buffer)

class FileContentWindow(ContentWindow):
  def __init__(self, offset, size, file_handle, file_offset):
    super().__init__(offset, size)
    self._file_offset = file_offset
    self._handle = file_handle

  def get(self, offset, size):
    assert offset in self
    assert offset + size in self
    self._handle.seek(
      self._file_offset + offset - self.start_offset, os.SEEK_SET)
    return self._handle.read(size)

  def clone(self, offset, size):
    return FileContentWindow(
      offset, size, self._handle, self._file_offset+offset-self.start_offset)

  def __repr__(self):
    return 'FileContentWindow(%d,%d,0x%x,%d)' % (
      self.start_offset, self._size, id(self._handle), self._file_offset)

class FileBuffer(object):
  def __init__(self, path=None):
    if not path:
      self._ranges = []
      self._path = None
      return
    self._handle = open(path, 'rb')
    self._path = path
    self._handle.seek(0, os.SEEK_END)
    size = self._handle.tell()
    self._handle.seek(0, os.SEEK_SET)
    self._ranges = [FileContentWindow(0, size, self._handle, 0)]

  def __destroy__(self):
    close(self._handle)

  def insert(self, offset, new_content):
    self._insert(offset, new_content)
    self._optimize_ranges()

  def _insert(self, offset, new_content):
    assert offset in Window(0, self.size)
    if not new_content:
      return
    for i, r in enumerate(self._ranges):
      if r.start_offset == offset:
        self._ranges.insert(i, BufferContentWindow(offset, new_content))
        for j in range(i+1, len(self._ranges)):
          self._ranges[j].start_offset += len(new_content)
        return
      if r.end_offset == offset:
        self._ranges.insert(i+1, BufferContentWindow(offset, new_content))
        for j in range(i+2, len(self._ranges)):
          self._ranges[j].start_offset += len(new_content)
        return
      if offset in r:
        self._ranges[i] = r.clone(r.start_offset, offset-r.start_offset)
        self._ranges.insert(i+1, BufferContentWindow(offset, new_content))
        self._ranges.insert(i+2, r.clone(offset, r.size-(offset-r.start_offset)))
        for j in range(i+2, len(self._ranges)):
          self._ranges[j].start_offset += len(new_content)
        return
    self._ranges.append(BufferContentWindow(offset, new_content))

  def delete(self, offset, size):
    self._delete(Window(offset, min(self.size - offset, size)))
    self._refresh_offsets()
    self._optimize_ranges()

  def _delete(self, window):
    assert window.start_offset in Window(0, self.size)
    assert window.end_offset in Window(0, self.size)
    if not window.size:
      return
    min_range_idx = None
    max_range_idx = None
    for i, r in enumerate(self._ranges):
      if window.start_offset in r and min_range_idx is None:
        min_range_idx = i
      if window.end_offset in r:
        max_range_idx = i

    if min_range_idx == max_range_idx:
      the_range = self._ranges[min_range_idx]
      left_range = the_range.clone(
        the_range.start_offset, window.start_offset - the_range.start_offset)
      right_range = the_range.clone(
        window.end_offset, the_range.end_offset - window.end_offset)
      self._ranges.pop(min_range_idx)
      self._ranges.insert(min_range_idx, left_range)
      self._ranges.insert(min_range_idx + 1, right_range)
      return

    if min_range_idx is not None:
      min_range = self._ranges[min_range_idx]
      min_range = min_range.clone(
        min_range.start_offset, window.start_offset - min_range.start_offset)
      self._ranges[min_range_idx] = min_range

    if max_range_idx is not None:
      max_range = self._ranges[max_range_idx]
      delta = window.start_offset + window.size - max_range.start_offset
      if delta != max_range.size:
        max_range = max_range.clone(
          max_range.start_offset + delta, max_range.size - delta)
      self._ranges[max_range_idx] = max_range

    self._ranges = [
      r for r in self._ranges
        if r.start_offset not in window
        or r.end_offset not in window]

  def _refresh_offsets(self):
    offset = 0
    for r in self._ranges:
      r.start_offset = offset
      offset += r.size

  def _optimize_ranges(self):
    self._ranges = [r for r in self._ranges if r.size > 0]

  def replace(self, offset, new_content):
    self.delete(offset, len(new_content))
    self.insert(offset, new_content)

  def get(self, offset, size):
    return self._get(Window(offset, size))

  def _get(self, window):
    buffer = b''
    left = window.size
    for r in self._ranges:
      if window.start_offset in r:
        to_get = min(r.size + r.start_offset - window.start_offset, left)
        buffer += r.get(window.start_offset, to_get)
        left -= to_get
      elif window.end_offset in r:
        to_get = min(r.size, left)
        buffer += r.get(r.start_offset, to_get)
        left -= to_get
      else:
        if r.start_offset in window and r.end_offset in window:
          buffer += r.get(r.start_offset, r.size)
          left -= r.size
      if not left:
        break
    assert len(buffer) == window.size
    return buffer

  def get_path(self):
    return self._path

  def get_size(self):
    return sum(r.size for r in self._ranges)

  size = property(get_size)
  path = property(get_path)


if __name__ == '__main__':
  import unittest

  def parse_spec(spec):
    alphabet = b'abcdefghijklmnopqrstuvwxyz'
    k = 0
    all_mask = b''
    hash_mask = b''
    not_hash_mask = b''
    for i in range(len(spec)):
      if spec[i] in ['-', '#']:
        all_mask += alphabet[k:k+1]
        if spec[i] == '-':
          hash_mask += alphabet[k:k+1]
          not_hash_mask += b'|'
        else:
          hash_mask += b'|'
          not_hash_mask += alphabet[k:k+1]
        k += 1
      else:
        assert spec[i] == '|'
        all_mask += b'|'
        hash_mask += b'|'
        not_hash_mask += b'|'
    all_texts = [x for x in all_mask.split(b'|') if x]
    hash_texts = [x for x in hash_mask.split(b'|') if x]
    not_hash_texts = [x for x in not_hash_mask.split(b'|') if x]
    try:
      offset = spec.replace('|', '').index('#')
      size = spec.replace('|', '').rindex('#') + 1 - offset
    except ValueError:
      offset = size = 0
    return Window(offset, size), all_texts, hash_texts, not_hash_texts

  class TestBufferContentWindow(unittest.TestCase):
    def test_zero_position(self):
      b = BufferContentWindow(0, b'xyyy')
      self.assertEqual(b.get(1, 3), b'yyy')

    def test_nonzero_position(self):
      b = BufferContentWindow(1, b'abc')
      self.assertEqual(b.get(1, 3), b'abc')
      self.assertEqual(b.get(2, 2), b'bc')

    def test_invalid_sizes_or_offsets(self):
      b = BufferContentWindow(1, b'abcd')
      with self.assertRaises(AssertionError): b.get(1, 5)
      with self.assertRaises(AssertionError): b.get(0, 1)
      with self.assertRaises(AssertionError): b.get(5, 1)

    def test_cloning(self):
      b1 = BufferContentWindow(1, b'abcd')
      b2 = b1.clone(2, 3)
      self.assertEqual(b2.get(2, 3), b'bcd')

    def test_invalid_cloning(self):
      b = BufferContentWindow(1, b'abcd')
      with self.assertRaises(AssertionError): b.clone(1, 5)
      with self.assertRaises(AssertionError): b.clone(0, 1)
      with self.assertRaises(AssertionError): b.clone(5, 1)

  class TestFileBufferInsertions(unittest.TestCase):
    def test_simple_inserting(self):
      fb = FileBuffer()
      fb.insert(0, b'test')
      self.assertEqual(fb._ranges, [BufferContentWindow(0, b'test')])

    def test_empty_insertions(self):
      fb = FileBuffer()
      fb.insert(0, b'')
      self.assertEqual(fb._ranges, [])

    def test_invalid_insertions(self):
      fb = FileBuffer()
      fb.insert(0, b'x')
      with self.assertRaises(AssertionError): fb.insert(2, b'whatever')
      with self.assertRaises(AssertionError): fb.insert(-1, b'w')

    def test_inserting_at_edges(self):
      fb = FileBuffer()
      fb.insert(0, b'4')
      fb.insert(0, b'2')
      fb.insert(1, b'3')
      fb.insert(0, b'1')
      self.assertEqual(fb._ranges, [
        BufferContentWindow(0, b'1'),
        BufferContentWindow(1, b'2'),
        BufferContentWindow(2, b'3'),
        BufferContentWindow(3, b'4'),
      ])

    def test_inserting_with_split(self):
      fb = FileBuffer()
      fb.insert(0, b'abcd')
      fb.insert(4, b'efgh')
      fb.insert(3, b'!')
      self.assertEqual(fb._ranges, [
        BufferContentWindow(0, b'abc'),
        BufferContentWindow(3, b'!'),
        BufferContentWindow(4, b'd'),
        BufferContentWindow(5, b'efgh'),
      ])

  class TestFileBufferRemovals(unittest.TestCase):
    def do_test(self, spec):
      window, input_texts, texts_wo_hash, _ = parse_spec(spec)
      fb = FileBuffer()
      input_offset = 0
      for text in input_texts:
        fb.insert(input_offset, text)
        input_offset += len(text)
      fb.delete(window.start_offset, window.size)
      output_offset = 0
      output_windows = [BufferContentWindow(0, text) for text in texts_wo_hash]
      for output_range in output_windows:
        output_range.start_offset = output_offset
        output_offset += output_range.size
      self.assertEqual(fb._ranges, output_windows)

    def test(self):
      self.do_test('####|##--')
      self.do_test('####|#---')
      self.do_test('####|----')
      self.do_test('##|#|----')
      self.do_test('###-|----')
      self.do_test('##--|----')
      self.do_test('#---|----')
      self.do_test('#-|----')
      self.do_test('#|----')
      self.do_test('-##-|----')
      self.do_test('-#--|----')
      self.do_test('--#-|----')
      self.do_test('--##|----')
      self.do_test('---#|----')

      self.do_test('--##|####')
      self.do_test('---#|####')
      self.do_test('----|####')
      self.do_test('----|#|##')
      self.do_test('----|-###')
      self.do_test('----|--##')
      self.do_test('----|---#')
      self.do_test('----|-#')
      self.do_test('----|#')
      self.do_test('----|-##-')
      self.do_test('----|--#-')
      self.do_test('----|-#--')
      self.do_test('----|##--')
      self.do_test('----|#---')

      self.do_test('----|####|----')
      self.do_test('----|##|##|----')
      self.do_test('--##|####|----')
      self.do_test('----|####|##--')
      self.do_test('--##|####|##--')
      self.do_test('----|##--|----')
      self.do_test('----|--##|----')
      self.do_test('----|-##-|----')
      self.do_test('----|#|----')
      self.do_test('----|#|#|----')
      self.do_test('---#|####|----')
      self.do_test('----|####|#---')
      self.do_test('---#|####|#---')
      self.do_test('----|#---|----')
      self.do_test('----|---#|----')
      self.do_test('----|-#--|----')

      self.do_test('#-')
      self.do_test('-')
      self.do_test('-|#-')
      self.do_test('-|#')
      self.do_test('#|-')

  class TestFileBufferRetrievals(unittest.TestCase):
    def do_test(self, spec):
      window, input_texts, _, texts_w_hash = parse_spec(spec)
      fb = FileBuffer()
      input_offset = 0
      for text in input_texts:
        fb.insert(input_offset, text)
        input_offset += len(text)
      self.assertEqual(
        fb.get(window.start_offset, window.size), b''.join(texts_w_hash))

    def test(self):
      self.do_test('####|##--')
      self.do_test('####|#---')
      self.do_test('####|----')
      self.do_test('##|#|----')
      self.do_test('###-|----')
      self.do_test('##--|----')
      self.do_test('#---|----')
      self.do_test('#-|----')
      self.do_test('#|----')
      self.do_test('-##-|----')
      self.do_test('-#--|----')
      self.do_test('--#-|----')
      self.do_test('--##|----')
      self.do_test('---#|----')

      self.do_test('--##|####')
      self.do_test('---#|####')
      self.do_test('----|####')
      self.do_test('----|#|##')
      self.do_test('----|-###')
      self.do_test('----|--##')
      self.do_test('----|---#')
      self.do_test('----|-#')
      self.do_test('----|#')
      self.do_test('----|-##-')
      self.do_test('----|--#-')
      self.do_test('----|-#--')
      self.do_test('----|##--')
      self.do_test('----|#---')

      self.do_test('----|####|----')
      self.do_test('----|##|##|----')
      self.do_test('--##|####|----')
      self.do_test('----|####|##--')
      self.do_test('--##|####|##--')
      self.do_test('----|##--|----')
      self.do_test('----|--##|----')
      self.do_test('----|-##-|----')
      self.do_test('----|#|----')
      self.do_test('----|#|#|----')
      self.do_test('---#|####|----')
      self.do_test('----|####|#---')
      self.do_test('---#|####|#---')
      self.do_test('----|#---|----')
      self.do_test('----|---#|----')
      self.do_test('----|-#--|----')

      self.do_test('#-')
      self.do_test('-')
      self.do_test('-|#-')
      self.do_test('-|#')
      self.do_test('#|-')

  unittest.main()
