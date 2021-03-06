''' Exports Settings. '''

from hexvi.app_state import AppState

class Settings(object):
    ''' A container for all the User settings. '''

    def __init__(self):
        self.scrolloff = 0
        self.max_match_size = 8192
        self.term_colors = 16

        self.mode_chars = {}
        for mode in AppState.NON_COMMAND_MODES:
            self.mode_chars[mode] = '>'
        self.mode_chars[AppState.MODE_COMMAND] = ':'
        self.mode_chars[AppState.MODE_SEARCH_FORWARD] = '/'
        self.mode_chars[AppState.MODE_SEARCH_BACKWARD] = '?'

        for mode in AppState.ALL_MODES:
            assert mode in self.mode_chars
