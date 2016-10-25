import pytest
from hexvi.io.io_buffer import IOBuffer
from hexvi.io.range import Range
from hexvi.io.memory_content_range import MemoryContentRange
from typing import List


class Spec:
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
    def __init__(self, text: str) -> None:
        alphabet = b'abcdefghijklmnopqrstuvwxyz'

        k = 0
        all_mask = b''
        hash_mask = b''
        not_hash_mask = b''
        for char in text:
            if char in ['-', '#']:
                all_mask += alphabet[k:k+1]
                if char == '#':
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
        self.all_chunks = [x for x in all_mask.split(b'|') if x]
        self.hash_chunks = [x for x in hash_mask.split(b'|') if x]
        self.not_hash_chunks = [x for x in not_hash_mask.split(b'|') if x]

        try:
            offset = text.replace('|', '').index('#')
            size = text.replace('|', '').rindex('#') + 1 - offset
        except ValueError:
            offset = size = 0
        self.primary_range = Range(offset, size)


TESTS = [Spec(text) for text in [
    '####|##--',
    '####|#---',
    '####|----',
    '##|#|----',
    '###-|----',
    '##--|----',
    '#---|----',
    '#-|----',
    '#|----',
    '-##-|----',
    '-#--|----',
    '--#-|----',
    '--##|----',
    '---#|----',
    '--##|####',
    '---#|####',
    '----|####',
    '----|#|##',
    '----|-###',
    '----|--##',
    '----|---#',
    '----|-#',
    '----|#',
    '----|-##-',
    '----|--#-',
    '----|-#--',
    '----|##--',
    '----|#---',
    '----|####|----',
    '----|##|##|----',
    '--##|####|----',
    '----|####|##--',
    '--##|####|##--',
    '----|##--|----',
    '----|--##|----',
    '----|-##-|----',
    '----|#|----',
    '----|#|#|----',
    '---#|####|----',
    '----|####|#---',
    '---#|####|#---',
    '----|#---|----',
    '----|---#|----',
    '----|-#--|----',
    '#-',
    '-',
    '-|#-',
    '-|#',
    '#|-',
]]


class TestIOBufferInsertions:
    def test_simple_inserting(self) -> None:
        buffer = IOBuffer()
        buffer.insert(0, b'test')
        assert buffer._content_ranges == [MemoryContentRange(0, b'test')]

    def test_empty_insertions(self) -> None:
        buffer = IOBuffer()
        buffer.insert(0, b'')
        assert buffer._content_ranges == []

    def test_invalid_insertions(self) -> None:
        buffer = IOBuffer()
        buffer.insert(0, b'x')
        with pytest.raises(AssertionError):
            buffer.insert(2, b'whatever')
        with pytest.raises(AssertionError):
            buffer.insert(-1, b'w')

    def test_inserting_at_edges(self) -> None:
        buffer = IOBuffer()
        buffer.insert(0, b'4')
        buffer.insert(0, b'2')
        buffer.insert(1, b'3')
        buffer.insert(0, b'1')
        print(buffer._content_ranges)
        assert buffer._content_ranges == [
            MemoryContentRange(0, b'1'),
            MemoryContentRange(1, b'2'),
            MemoryContentRange(2, b'3'),
            MemoryContentRange(3, b'4'),
        ]

    def test_inserting_with_split(self) -> None:
        buffer = IOBuffer()
        buffer.insert(0, b'abcd')
        buffer.insert(4, b'efgh')
        buffer.insert(3, b'!')
        assert buffer._content_ranges == [
            MemoryContentRange(0, b'abc'),
            MemoryContentRange(3, b'!'),
            MemoryContentRange(4, b'd'),
            MemoryContentRange(5, b'efgh'),
        ]


@pytest.mark.parametrize('spec', TESTS)
def test_io_buffer_delete_produces_correct_content_ranges(spec: Spec) -> None:
    output_offset = 0
    expected_content_ranges = [
        MemoryContentRange(0, text) for text in spec.not_hash_chunks]
    for expected_range in expected_content_ranges:
        expected_range.start_offset = output_offset
        output_offset += expected_range.size

    buffer = IOBuffer()
    input_offset = 0
    for text in spec.all_chunks:
        buffer.insert(input_offset, text)
        input_offset += len(text)

    buffer.delete(spec.primary_range.start_offset, spec.primary_range.size)

    assert buffer._content_ranges == expected_content_ranges


@pytest.mark.parametrize('spec', TESTS)
def test_io_buffer_read_bytes_returns_correct_content(spec: Spec) -> None:
    buffer = IOBuffer()
    input_offset = 0
    for text in spec.all_chunks:
        buffer.insert(input_offset, text)
        input_offset += len(text)

    actual_output = buffer.read_bytes(
        spec.primary_range.start_offset, spec.primary_range.size)
    expected_output = b''.join(spec.hash_chunks)
    assert actual_output == expected_output
