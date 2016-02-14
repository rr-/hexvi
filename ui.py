import sys
import re

try:
    import urwid
except ImportError as e:
    if e.name is None:
        raise
    print('Please install %s.' % e.name)
    sys.exit(1)

from file_buffer import FileBuffer
from readline_edit import ReadlineEdit

class BaseLineWalker(urwid.ListWalker):
    def __init__(self, file_buffer, column_count_getter, offset_getter):
        self._file_buffer = file_buffer
        self._column_count_getter = column_count_getter
        self._offset_getter = offset_getter
        self._focus = 0

    def get_focus(self):
        return self._get_at_pos(self._focus)

    def set_focus(self, focus):
        self._focus = focus
        self._modified()

    def get_next(self, start_from):
        return self._get_at_pos(start_from + 1)

    def get_prev(self, start_from):
        return self._get_at_pos(start_from - 1)

    def _get_at_pos(self, pos):
        if pos < 0:
            return None, None
        if self._file_buffer is None:
            return None, None
        return urwid.Edit(self._get_line_text(pos)), pos

    def _get_line_text(self, pos):
        raise RuntimeError('Implement me')

# todo: these three classes almost certainly need to be merged into one custom widget
# to make scroll synchronization etc. sane
class OffsetLineWalker(BaseLineWalker):
    def _get_line_text(self, pos):
        offset = pos * self._column_count_getter()
        return '%08x' % offset if offset < self._file_buffer.size else ''
class HexDumpLineWalker(BaseLineWalker):
    def _get_line_text(self, pos):
        column_count = self._column_count_getter()
        offset_start = pos * column_count
        buffer = self._file_buffer.get_content_range(offset_start, column_count)
        return ''.join('%02x ' % c for c in buffer)
class AsciiDumpLineWalker(BaseLineWalker):
    def _get_line_text(self, pos):
        column_count = self._column_count_getter()
        offset_start = pos * column_count
        buffer = self._file_buffer.get_content_range(offset_start, column_count)
        return ''.join('%c' % c if c >= 32 and c < 127 else '.' for c in buffer)

class MainWindow(urwid.Frame):
    def __init__(self, file_buffer):
        self._file_buffer = file_buffer
        self._column_count = 8 # todo: autodetect
        self._offset = 0

        self._offsets = self._make_offsets()
        self._hex_dump = urwid.Frame(self._make_hex_dump(), urwid.Text('Hex dump'))
        self._ascii_dump = self._make_ascii_dump()
        self._console = self._make_console()
        self._header = self._make_header()

        self._main_view = urwid.Columns([
            ('fixed', 8, urwid.Frame(self._offsets, urwid.Text('Offset'))),
            ('fixed', 1, urwid.AttrMap(urwid.SolidFill(), 'filler')),
            ('fixed', 1337, self._hex_dump),
            ('fixed', 1, urwid.AttrMap(urwid.SolidFill(), 'filler')),
            ('fixed', 1337, urwid.Frame(self._ascii_dump, urwid.Text('ASCII dump'))),
        ])

        urwid.Frame.__init__(
            self,
            urwid.Pile([
                self._main_view,
                ('fixed', 1, urwid.AttrMap(urwid.SolidFill(), 'header')),
                ('fixed', 1, urwid.Filler(self._console)),
            ]),
            urwid.AttrMap(self._header, 'header'))

        # focus the command line
        self.focus.set_focus(2)

    def resize(self, new_term_size):
        self.column_count = (new_term_size[0] - 12) // 4
        self._main_view.contents[2] = (self._hex_dump, ('given', self.column_count * 3, 0))
        self._main_view.contents[4] = (self._ascii_dump, ('given', self.column_count, 0))
        self.render(new_term_size)

    def get_caption(self):
        return re.sub('^hexvi( - )?', '', self._header.base_widget.get_text()[0])
    def set_caption(self, value):
        if not value:
            self._header.base_widget.set_text('hexvi')
        else:
            self._header.base_widget.set_text('hexvi - ' + value)
    caption = property(get_caption, set_caption)

    def get_offset(self):
        return self._offset
    def set_offset(self, value):
        self._offset = value
    offset = property(get_offset, set_offset)

    def get_column_count(self):
        return self._column_count
    def set_column_count(self, value):
        self._column_count = value
    column_count = property(get_column_count, set_column_count)

    def _make_header(self):
        return urwid.Text(u'hexvi')

    def _make_offsets(self):
        return urwid.ListBox(OffsetLineWalker(
            self._file_buffer,
            lambda: self.column_count,
            lambda: self.offset))

    def _make_hex_dump(self):
        return urwid.ListBox(HexDumpLineWalker(
            self._file_buffer,
            lambda: self.column_count,
            lambda: self.offset))

    def _make_ascii_dump(self):
        return urwid.ListBox(AsciiDumpLineWalker(
            self._file_buffer,
            lambda: self.column_count,
            lambda: self.offset))

    def _make_console(self):
        return ReadlineEdit()

class CustomMainLoop(urwid.MainLoop):
    def process_input(self, keys):
        for k in keys:
            if k == 'window resize':
                return self.unhandled_input(k)
        return super().process_input(keys)

class Ui(object):
    def run(self, args):
        file_buffer = FileBuffer(args.file)
        self._main_window = MainWindow(file_buffer)
        self._main_loop = CustomMainLoop(
            self._main_window,
            palette=[
                ('selected', 'light red', ''),
                ('header', 'standout', ''),
            ],
            unhandled_input=self._key_pressed)
        self._main_window.caption = file_buffer.path
        self._main_window.resize(self._main_loop.screen.get_cols_rows())
        self._main_loop.run()

    def _key_pressed(self, key):
        if key == 'ctrl q':
            raise urwid.ExitMainLoop()
        if key == 'window resize':
            self._main_window.resize(self._main_loop.screen.get_cols_rows())
