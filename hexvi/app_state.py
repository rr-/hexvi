from .file_state import FileState, WindowSizeChangeEvent
from .mappings import MappingCollection
from .command_processor import CommandProcessor
import zope.event
import shlex

class FileBufferChangeEvent(object):
    def __init__(self, file_buffer):
        self.file_buffer = file_buffer

class ModeChangeEvent(object):
    def __init__(self, mode, char=None):
        self.mode = mode
        self.char = char

class AppState(object):
    MODE_NORMAL = 'normal'
    MODE_COMMAND = 'command'
    MODE_SEARCH_FORWARD = 'search'
    MODE_SEARCH_BACKWARD = 'rev-search'

    MODE_KEY_MAP = {
        ':': MODE_COMMAND,
        '/': MODE_SEARCH_FORWARD,
        '?': MODE_SEARCH_BACKWARD,
    }

    def __init__(self, args):
        self._window_size = (0, 0)
        self._mode = AppState.MODE_COMMAND
        self._command_processor = CommandProcessor(self)

        # todo: manage this once we get multiple files support
        self._cur_file = FileState(args.file)

        self.normal_mode_mappings = MappingCollection()

        self.exec('nmap', 'h',              ':jump_by_bytes -1')
        self.exec('nmap', 'j',              ':jump_by_lines 1')
        self.exec('nmap', 'k',              ':jump_by_lines -1')
        self.exec('nmap', 'l',              ':jump_by_bytes 1')
        self.exec('nmap', '<left>',         ':jump_by_bytes -1')
        self.exec('nmap', '<down>',         ':jump_by_lines 1')
        self.exec('nmap', '<up>',           ':jump_by_lines -1')
        self.exec('nmap', '<right>',        ':jump_by_bytes 1')
        self.exec('nmap', '{dec}h',         ':jump_by_bytes -{arg0}')
        self.exec('nmap', '{dec}j',         ':jump_by_lines {arg0}')
        self.exec('nmap', '{dec}k',         ':jump_by_lines -{arg0}')
        self.exec('nmap', '{dec}l',         ':jump_by_bytes {arg0}')
        self.exec('nmap', '{dec}<left>',    ':jump_by_bytes -{arg0}')
        self.exec('nmap', '{dec}<down>',    ':jump_by_lines {arg0}')
        self.exec('nmap', '{dec}<up>',      ':jump_by_lines -{arg0}')
        self.exec('nmap', '{dec}<right>',   ':jump_by_bytes {arg0}')
        self.exec('nmap', '{hex}G',         ':jump_to {arg0}')
        self.exec('nmap', 'gg',             ':jump_to_start_of_file')
        self.exec('nmap', 'G',              ':jump_to_end_of_file')
        self.exec('nmap', '^',              ':jump_to_start_of_line')
        self.exec('nmap', '$',              ':jump_to_end_of_line')
        self.exec('nmap', '{tab}',          ':toggle_pane')
        self.exec('nmap', '<ctrl q>',       ':quit')
        self.exec('nmap', 'n',              ':search')
        self.exec('nmap', 'N',              ':rsearch')

        for key, mode in self.MODE_KEY_MAP.items():
            self.nmap([key], (lambda m, k: lambda: self.set_mode(m, k))(mode, key))

    def keypress(self, key):
        return self.normal_mode_mappings.keypress(key)

    def nmap(self, key_sequence, command):
        self.normal_mode_mappings.add(key_sequence, command)

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

    def set_mode(self, value, char=None):
        if value != self._mode:
            self._mode = value
            zope.event.notify(ModeChangeEvent(value, char))

    cur_file = property(get_cur_file)
    mode = property(get_mode, set_mode)
    window_size = property(get_window_size, set_window_size)
