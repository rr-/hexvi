''' Miscellaneous utilities '''

from hexvi.app_state import SearchState

def scan_file(file_buffer, direction, start_pos, buffer_size, jump_size, functor):
    '''
    Scans the file incrementally, running given function on the content
    parts.

    @param functor: the function to run. returning truthy value stops the scan.
    @param direction: whether to search forward or backward.
    @param start_pos: where to start the scan at.
    @param bufer_size: preferred content size to send to functor.
    #param jump_size: how many bytes to advance after each iteration.
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
