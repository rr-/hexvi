''' Commands related to movement by words '''

import regex
import hexvi.util
from hexvi.app_state import SearchState
from hexvi.command_registry import BaseCommand

WORD_CLASS_PATTERNS = ['[a-zA-Z]', '[0-9]', '[^a-zA-Z0-9]']

def _choose_word_class(char):
    for pattern in WORD_CLASS_PATTERNS:
        if regex.match(pattern.encode('utf-8'), char):
            return pattern
    assert False

def _forward_word_callback(
        app_state, pattern, buffer, start_pos, end_pos, direction):
    indices = range(len(buffer))
    if direction == SearchState.DIR_BACKWARD:
        indices = reversed(indices)
    for i in indices:
        char_under_cursor = buffer[i:i+1]
        if not regex.match(pattern.encode('utf-8'), char_under_cursor):
            app_state.current_tab.current_offset = start_pos + i
            return True
        if end_pos == app_state.current_tab.size:
            app_state.current_tab.current_offset = app_state.current_tab.size
    return False

def _backward_word_callback(app_state, pattern, buffer, start_pos):
    indices = reversed(range(len(buffer)))
    for i in indices:
        if i - 1 >= 0:
            char_under_cursor = buffer[i-1:i]
            if not regex.match(pattern.encode('utf-8'), char_under_cursor):
                app_state.current_tab.current_offset = start_pos + i
                return True
        if start_pos == 0:
            app_state.current_tab.current_offset = 0
    return False

class JumpToNextWordCommand(BaseCommand):
    names = ['jump_to_next_word']
    def run(self, args):
        repeat = 1 if not args else int(args[0])
        for _ in range(repeat):
            pattern = _choose_word_class(
                self._app_state.current_tab.file_buffer.get(
                    self._app_state.current_tab.current_offset, 1))
            hexvi.util.scan_file(
                self._app_state.current_tab.file_buffer,
                SearchState.DIR_FORWARD,
                self._app_state.current_tab.current_offset,
                1000,
                1000,
                lambda buffer, start_pos, end_pos, direction: \
                    _forward_word_callback(
                        self._app_state, pattern, buffer, start_pos, end_pos, direction))

class JumpToPrevWordCommand(BaseCommand):
    names = ['jump_to_prev_word']
    def run(self, args):
        repeat = 1 if not args else int(args[0])
        for _ in range(repeat):
            if self._app_state.current_tab.current_offset == 0:
                return
            pattern = _choose_word_class(
                self._app_state.current_tab.file_buffer.get(
                    self._app_state.current_tab.current_offset - 1, 1))
            hexvi.util.scan_file(
                self._app_state.current_tab.file_buffer,
                SearchState.DIR_BACKWARD,
                self._app_state.current_tab.current_offset,
                1000,
                1000,
                lambda buffer, start_pos, end_pos, direction: \
                    _backward_word_callback(
                        self._app_state, pattern, buffer, start_pos))
