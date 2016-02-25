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

        self.nmap(['tab'], lambda: self.cur_file.toggle_panes())
        for k in ['h', 'right']: self.nmap([k], lambda: self.exec('jump_by_bytes', '-1'))
        for k in ['j', 'down']:  self.nmap([k], lambda: self.exec('jump_by_lines', '1'))
        for k in ['k', 'up']:    self.nmap([k], lambda: self.exec('jump_by_lines', '-1'))
        for k in ['l', 'right']: self.nmap([k], lambda: self.exec('jump_by_bytes', '1'))
        for k in ['h', 'right']: self.nmap(['<dec>', k], lambda i: self.exec('jump_by_bytes', '-'+i))
        for k in ['j', 'down']:  self.nmap(['<dec>', k], lambda i: self.exec('jump_by_lines', i))
        for k in ['k', 'up']:    self.nmap(['<dec>', k], lambda i: self.exec('jump_by_lines', '-'+i))
        for k in ['l', 'right']: self.nmap(['<dec>', k], lambda i: self.exec('jump_by_bytes', i))
        self.nmap(['<hex>', 'G'], lambda i: self.exec('jump_to', i))
        self.nmap(['g', 'g'],     lambda: self.exec('jump_to_start_of_file'))
        self.nmap(['G'],          lambda: self.exec('jump_to_end_of_file'))
        self.nmap(['^'],          lambda: self.exec('jump_to_start_of_line'))
        self.nmap(['$'],          lambda: self.exec('jump_to_end_of_line'))
        self.nmap(['ctrl q'],     lambda: self.exec('quit'))

        for key, mode in self.MODE_KEY_MAP.items():
            self.nmap([key], (lambda m, k: lambda: self.set_mode(m, k))(mode, key))

        self.normal_mode_mappings.compile()

    def keypress(self, key):
        return self.normal_mode_mappings.keypress(key)

    def nmap(self, key_sequence, command):
        self.normal_mode_mappings.add(key_sequence, command)

    def accept_raw_input(self, text):
        if self.mode == self.MODE_COMMAND:
            command, *args = shlex.shlex(text)
            self.exec(command, *args)
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
