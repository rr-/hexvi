'''
Application state - the heart of all state in hexvi.
'''

import os
import hexvi.events as events
from hexvi.command_processor import CommandProcessor
from hexvi.file_state import FileState
from hexvi.mappings import MappingCollection

class SearchState(object):
    ''' Things related to last performed search. '''
    DIR_BACKWARD = 0
    DIR_FORWARD = 1
    def __init__(self):
        self.direction = self.DIR_FORWARD
        self.text = None

class AppState(object):
    ''' The main state. '''

    MODE_NORMAL = 'normal'
    MODE_COMMAND = 'command'
    MODE_SEARCH_FORWARD = 'search'
    MODE_SEARCH_BACKWARD = 'rsearch'
    MODE_REPLACE = 'replace'
    MODE_INSERT = 'insert'

    INPUT_MODES = [MODE_REPLACE, MODE_INSERT]
    COMMAND_MODES = [
        MODE_COMMAND,
        MODE_SEARCH_FORWARD,
        MODE_SEARCH_BACKWARD]
    NON_COMMAND_MODES = [MODE_NORMAL] + INPUT_MODES
    ALL_MODES = COMMAND_MODES + NON_COMMAND_MODES

    def __init__(self, settings, args):
        self._window_size = (0, 0)
        self._mode = AppState.MODE_COMMAND
        self.settings = settings
        self.cmd_processor = CommandProcessor(self)

        try:
            # TODO: manage this once we get multiple files support
            self._cur_file = FileState(self, args.file)
        except Exception as ex:
            self._cur_file = FileState(self)
            events.notify(events.PrintMessage(str(ex), style='msg-error'))

        self.search_state = SearchState()
        self.mappings = {key: MappingCollection() for key in self.ALL_MODES}
        self.hexvi_dir = os.path.dirname(__file__)
        self.resources_dir = os.path.join(self.hexvi_dir, 'share')

    def accept_command_input(self, text):
        ''' Fired when the user runs a command in the UI command bar. '''
        mode = self.mode
        self.mode = AppState.MODE_NORMAL
        if mode == self.MODE_COMMAND:
            self.cmd_processor.exec_raw(text)
        elif mode == self.MODE_SEARCH_FORWARD:
            self.cmd_processor.exec('search', text)
        elif mode == self.MODE_SEARCH_BACKWARD:
            self.cmd_processor.exec('rsearch', text)
        else:
            raise NotImplementedError(text)

    def accept_byte_input(self, byte):
        ''' Fired when the user enters a byte in either HEX or ASCII dump. '''
        if self.mode == self.MODE_REPLACE:
            self.cur_file.file_buffer.replace(self.cur_file.cur_offset, bytes([byte]))
            self.cur_file.cur_offset += 1
        elif self.mode == self.MODE_INSERT:
            self.cur_file.file_buffer.insert(self.cur_file.cur_offset, bytes([byte]))
            self.cur_file.cur_offset += 1
        else:
            raise NotImplementedError()

    def get_window_size(self):
        ''' Returns the window size. '''
        return self._window_size

    def set_window_size(self, value):
        ''' Sets the window size. '''
        if value != self._window_size:
            self._window_size = value
            events.notify(events.WindowSizeChange(value))

    def get_cur_file(self):
        ''' Returns the currently focused file state. '''
        return self._cur_file

    def set_cur_file(self, value):
        ''' Sets the currently focused file state. '''
        if value != self._cur_file:
            self._cur_file = value
            events.notify(events.FileBufferChange(value))

    def get_mode(self):
        ''' Gets the current mode. '''
        return self._mode

    def set_mode(self, value):
        ''' Sets the current mode. '''
        if value != self._mode:
            self._mode = value
            events.notify(events.ModeChange(value))

    cur_file = property(get_cur_file)
    mode = property(get_mode, set_mode)
    window_size = property(get_window_size, set_window_size)
