from file_state import FileState, WindowSizeChangeEvent
from mappings import MappingCollection
import zope.event

class FileBufferChangeEvent(object):
    def __init__(self, file_buffer):
        self.file_buffer = file_buffer

class ModeChangeEvent(object):
    def __init__(self, mode):
        self.mode = mode

class AppState(object):
    MODE_NORMAL = 'normal'
    MODE_COMMAND = 'command'

    def __init__(self, args):
        self._window_size = (0, 0)
        self._mode = AppState.MODE_COMMAND

        # todo: manage this once we get multiple files support
        self._cur_file = FileState(args.file)

        self.normal_mode_mappings = MappingCollection()

        self.nmap(['tab'], lambda: self.cur_file.toggle_panes())
        for k in ['h', 'right']: self.nmap([k], lambda: self.cur_file.move_cur_offset_by_char(-1))
        for k in ['j', 'down']:  self.nmap([k], lambda: self.cur_file.move_cur_offset_by_line(1))
        for k in ['k', 'up']:    self.nmap([k], lambda: self.cur_file.move_cur_offset_by_line(-1))
        for k in ['l', 'right']: self.nmap([k], lambda: self.cur_file.move_cur_offset_by_char(1))
        for k in ['h', 'right']: self.nmap(['<dec>', k], lambda i: self.cur_file.move_cur_offset_by_char(-i))
        for k in ['j', 'down']:  self.nmap(['<dec>', k], lambda i: self.cur_file.move_cur_offset_by_line(i))
        for k in ['k', 'up']:    self.nmap(['<dec>', k], lambda i: self.cur_file.move_cur_offset_by_line(-i))
        for k in ['l', 'right']: self.nmap(['<dec>', k], lambda i: self.cur_file.move_cur_offset_by_char(i))
        self.nmap(['<hex>', 'G'], lambda i: self.cur_file.set_cur_offset(i))
        self.nmap(['g', 'g'],     lambda: self.cur_file.set_cur_offset(0))
        self.nmap(['G'],          lambda: self.cur_file.set_cur_offset(self.cur_file.size))
        self.nmap(['^'],          lambda: self.cur_file.move_cur_offset_to_start_of_line())
        self.nmap(['$'],          lambda: self.cur_file.move_cur_offset_to_end_of_line())
        self.nmap([':'],          lambda: self.set_mode(AppState.MODE_COMMAND))

        self.normal_mode_mappings.compile()

    def keypress(self, key):
        return self.normal_mode_mappings.keypress(key)

    def nmap(self, key_sequence, command):
        self.normal_mode_mappings.add(key_sequence, command)

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

    def set_mode(self, value):
        if value != self._mode:
            self._mode = value
            zope.event.notify(ModeChangeEvent(value))

    cur_file = property(get_cur_file)
    mode = property(get_mode, set_mode)
    window_size = property(get_window_size, set_window_size)
