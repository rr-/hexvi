''' Commands related to search '''

import regex
import hexvi.util
from hexvi.command_registry import BaseTabCommand
from hexvi.app_state import SearchState

class _BaseSearchCommand(BaseTabCommand):
    def perform_user_search(self, direction, text):
        ''' High-level facade for text search in given direction '''
        if not text:
            text = self._app_state.search_state.text
            direction = self._app_state.search_state.direction ^ direction ^ 1
        else:
            self._app_state.search_state.direction = direction
            self._app_state.search_state.text = text
        return self._perform_stateless_search(direction, text)

    def _perform_stateless_search(self, direction, pattern):
        ''' Implementation of incremental text search '''
        if not pattern:
            raise RuntimeError('No text to search for')
        max_match_size = self._app_state.settings.max_match_size
        if direction == SearchState.DIR_BACKWARD:
            start_pos = self.current_tab.current_offset
            pattern = '(?r)' + pattern
        else:
            start_pos = self.current_tab.current_offset + 1
        if not hexvi.util.scan_file(
                self.current_tab.file_buffer,
                direction,
                start_pos,
                max_match_size * 2,
                max_match_size,
                lambda buffer, start_pos, end_pos, direction: \
                    self._search_callback(pattern, buffer, start_pos)):
            # TODO: if an option is enabled, show info and wrap around
            raise RuntimeError('Not found')

    def _search_callback(self, pattern, buffer, start_pos):
        match = regex.search(pattern.encode('utf-8'), buffer)
        if match:
            self.current_tab.current_offset = start_pos + match.span()[0]
            return True
        return False

    def run(self, args):
        raise NotImplementedError()

class ForwardSearchCommand(_BaseSearchCommand):
    names = ['search']
    def run(self, args):
        text = '' if len(args) < 1 else args[0]
        repeat = 1 if len(args) < 2 else int(args[1])
        for _ in range(repeat):
            self.perform_user_search(SearchState.DIR_FORWARD, text)

class BackwardSearchCommand(_BaseSearchCommand):
    names = ['rsearch']
    def run(self, args):
        text = '' if len(args) < 1 else args[0]
        repeat = 1 if len(args) < 2 else int(args[1])
        for _ in range(repeat):
            self.perform_user_search(SearchState.DIR_BACKWARD, text)
