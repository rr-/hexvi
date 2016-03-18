''' Tests the FileBuffer and content window management. '''

import unittest

from hexvi.file_buffer import BufferContentWindow
from hexvi.file_buffer import FileBuffer
from hexvi.file_buffer import Window

def parse_spec(spec):
    '''
    Takes the input of form
        ---##|##|#----
    and returns tuple containing information regarding positions and sizes of:
        - the continuous # range (ignoring chunk divisions)
        - chunks that contain either - or #
        - chunks that contain only #
        - chunks that contain only -
    This function assumes the hashes to be one continuous range.
    '''
    alphabet = b'abcdefghijklmnopqrstuvwxyz'
    k = 0
    all_mask = b''
    hash_mask = b''
    not_hash_mask = b''
    for char in spec:
        if char in ['-', '#']:
            all_mask += alphabet[k:k+1]
            if char == '-':
                hash_mask += alphabet[k:k+1]
                not_hash_mask += b'|'
            else:
                hash_mask += b'|'
                not_hash_mask += alphabet[k:k+1]
            k += 1
        else:
            assert char == '|'
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
        window = BufferContentWindow(0, b'xyyy')
        self.assertEqual(window.get(1, 3), b'yyy')

    def test_nonzero_position(self):
        window = BufferContentWindow(1, b'abc')
        self.assertEqual(window.get(1, 3), b'abc')
        self.assertEqual(window.get(2, 2), b'bc')

    def test_invalid_sizes_or_offsets(self):
        window = BufferContentWindow(1, b'abcd')
        with self.assertRaises(AssertionError):
            window.get(1, 5)
        with self.assertRaises(AssertionError):
            window.get(0, 1)
        with self.assertRaises(AssertionError):
            window.get(5, 1)

    def test_cloning(self):
        window1 = BufferContentWindow(1, b'abcd')
        window2 = window1.clone(2, 3)
        self.assertEqual(window2.get(2, 3), b'bcd')

    def test_invalid_cloning(self):
        window = BufferContentWindow(1, b'abcd')
        with self.assertRaises(AssertionError):
            window.clone(1, 5)
        with self.assertRaises(AssertionError):
            window.clone(0, 1)
        with self.assertRaises(AssertionError):
            window.clone(5, 1)

class TestFileBufferInsertions(unittest.TestCase):
    def test_simple_inserting(self):
        buffer = FileBuffer()
        buffer.insert(0, b'test')
        self.assertEqual(buffer.windows, [BufferContentWindow(0, b'test')])

    def test_empty_insertions(self):
        buffer = FileBuffer()
        buffer.insert(0, b'')
        self.assertEqual(buffer.windows, [])

    def test_invalid_insertions(self):
        buffer = FileBuffer()
        buffer.insert(0, b'x')
        with self.assertRaises(AssertionError):
            buffer.insert(2, b'whatever')
        with self.assertRaises(AssertionError):
            buffer.insert(-1, b'w')

    def test_inserting_at_edges(self):
        buffer = FileBuffer()
        buffer.insert(0, b'4')
        buffer.insert(0, b'2')
        buffer.insert(1, b'3')
        buffer.insert(0, b'1')
        self.assertEqual(buffer.windows, [
            BufferContentWindow(0, b'1'),
            BufferContentWindow(1, b'2'),
            BufferContentWindow(2, b'3'),
            BufferContentWindow(3, b'4'),
        ])

    def test_inserting_with_split(self):
        buffer = FileBuffer()
        buffer.insert(0, b'abcd')
        buffer.insert(4, b'efgh')
        buffer.insert(3, b'!')
        self.assertEqual(buffer.windows, [
            BufferContentWindow(0, b'abc'),
            BufferContentWindow(3, b'!'),
            BufferContentWindow(4, b'd'),
            BufferContentWindow(5, b'efgh'),
        ])

class TestFileBufferRemovals(unittest.TestCase):
    def do_test(self, spec):
        window, input_texts, texts_wo_hash, _ = parse_spec(spec)
        buffer = FileBuffer()
        input_offset = 0
        for text in input_texts:
            buffer.insert(input_offset, text)
            input_offset += len(text)
        buffer.delete(window.start_offset, window.size)
        output_offset = 0
        output_windows = [BufferContentWindow(0, text) for text in texts_wo_hash]
        for output_range in output_windows:
            output_range.start_offset = output_offset
            output_offset += output_range.size
        self.assertEqual(buffer.windows, output_windows)

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
        buffer = FileBuffer()
        input_offset = 0
        for text in input_texts:
            buffer.insert(input_offset, text)
            input_offset += len(text)
        self.assertEqual(
            buffer.get(window.start_offset, window.size), b''.join(texts_w_hash))

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
