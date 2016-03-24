''' Miscellaneous utilities '''

import os.path
from hexvi.app_state import SearchState

def scan_file(file_buffer, direction, start_pos, buffer_size, jump_size, functor):
    '''
    Scans the file incrementally, running given function on the content
    parts.

    direction -- whether to search forward or backward.
    start_pos -- where to start the scan at.
    bufer_size -- preferred content size to send to functor.
    jump_size -- how many bytes to advance after each iteration.
    functor -- the function to run. returning truthy value stops the scan.
    '''
    file_size = file_buffer.size
    try:
        if direction == SearchState.DIR_BACKWARD:
            end_pos = start_pos
            while end_pos > 0:
                start_pos = max(end_pos - buffer_size, 0)
                buffer = file_buffer.get(start_pos, end_pos - start_pos)
                if functor(buffer, start_pos, end_pos, direction):
                    return True
                end_pos -= jump_size
        elif direction == SearchState.DIR_FORWARD:
            while start_pos < file_size:
                buffer = file_buffer.get(
                    start_pos, min(buffer_size, file_size - start_pos))
                end_pos = start_pos + len(buffer)
                if functor(buffer, start_pos, end_pos, direction):
                    return True
                start_pos += jump_size
        else:
            assert False, 'Bad search direction'
    except (KeyboardInterrupt, SystemExit):
        raise RuntimeError('Aborted')
    return False

def trim_left(text, size):
    ''' Trims the text to given size, adding ellipsis if necessary '''
    ellipsis = '(...)'
    if len(text) <= size:
        return text
    return ellipsis + text[len(ellipsis)+len(text)-size:]

def filter_unique_paths(paths):
    result = []
    for i, path in enumerate(paths):
        same = False
        for j, other_path in enumerate(paths[i+1:]):
            if other_path and os.path.samefile(path, other_path):
                same = True
                break
        if not same:
            result.append(path)
    return result
