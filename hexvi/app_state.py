from .file_state import FileState, WindowSizeChangeEvent
from .mappings import MappingCollection
from .command_processor import CommandProcessor
import zope.event
import shlex
import os

class FileBufferChangeEvent(object):
    def __init__(self, file_buffer):
        self.file_buffer = file_buffer

class ModeChangeEvent(object):
    def __init__(self, mode, traversal):
        self.traversal = traversal
        self.mode = mode

class AppState(object):
    MODE_NORMAL = 'normal'
    MODE_COMMAND = 'command'
    MODE_SEARCH_FORWARD = 'search'
    MODE_SEARCH_BACKWARD = 'rsearch'

    ALL_MODES = [
        MODE_NORMAL,
        MODE_COMMAND,
        MODE_SEARCH_FORWARD,
        MODE_SEARCH_BACKWARD]

    def __init__(self, args):
        self._window_size = (0, 0)
        self._mode = AppState.MODE_COMMAND
        self._command_processor = CommandProcessor(self)

        # todo: manage this once we get multiple files support
        self._cur_file = FileState(args.file)

        self.normal_mode_mappings = MappingCollection()
        self.exec('source', os.path.join(os.path.dirname(__file__), 'share', 'hexvirc'))

    def keypress(self, key):
        return self.normal_mode_mappings.keypress(key)

    def accept_raw_input(self, text):
        if self.mode == self.MODE_COMMAND:
            command, *args = shlex.split(text)
            self.exec(command, *args)
        elif self.mode == self.MODE_SEARCH_FORWARD:
            self.exec('search', text)
        elif self.mode == self.MODE_SEARCH_BACKWARD:
            self.exec('rsearch', text)
        else:
            raise NotImplementedError(text)

    def exec(self, command, *args):
        self._command_processor.exec(command, *args)

    def get_window_size(self):
        return self._window_size

    def set_window_size(self, value):
        if value != self._window_size:
            self._window_size = value
            zope.event.notify(WindowSizeChangeEvent(value))

    def get_cur_file(self):
        return self._cur_file

    def set_cur_file(self, value):
        if value != self._cur_file:
            self._cur_file = value
            zope.event.notify(FileBufferChangeEvent(value))

    def get_mode(self):
        return self._mode

    def set_mode(self, value, traversal=None):
        if value != self._mode:
            self._mode = value
            zope.event.notify(ModeChangeEvent(value, traversal))

    cur_file = property(get_cur_file)
    mode = property(get_mode, set_mode)
    window_size = property(get_window_size, set_window_size)
