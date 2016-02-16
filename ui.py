import sys
import re

try:
    import urwid
except ImportError as e:
    if e.name is None:
        raise
    print('Please install %s.' % e.name)
    sys.exit(1)

from bindings import BindingMixin
from file_buffer import FileBuffer
from readline_edit import ReadlineEdit

class Dump(BindingMixin, urwid.BoxWidget):
    HEX = 'hex'
    ASC = 'asc'

    def __init__(self, file_buffer):
        BindingMixin.__init__(self)

        self.pane = self.HEX
        self._file_buffer = file_buffer
        self._top_offset = 0
        self._cur_offset = 0
        self._visible_columns = 0

        self.bind(['tab'], self.toggle_panes)
        self.bind(['h'], lambda: self.advance_offset_by_char(-1))
        self.bind(['j'], lambda: self.advance_offset_by_line(1))
        self.bind(['k'], lambda: self.advance_offset_by_line(-1))
        self.bind(['l'], lambda: self.advance_offset_by_char(1))
        self.bind(['<number>', 'h'], lambda i: self.advance_offset_by_char(-i))
        self.bind(['<number>', 'j'], lambda i: self.advance_offset_by_line(i))
        self.bind(['<number>', 'k'], lambda i: self.advance_offset_by_line(-i))
        self.bind(['<number>', 'l'], lambda i: self.advance_offset_by_char(i))
        self.bind(['left'], lambda: self.advance_offset_by_char(-1))
        self.bind(['down'], lambda: self.advance_offset_by_line(1))
        self.bind(['up'], lambda: self.advance_offset_by_line(-1))
        self.bind(['right'], lambda: self.advance_offset_by_char(1))
        self.bind(['<number>', 'left'], lambda i: self.advance_offset_by_char(-i))
        self.bind(['<number>', 'down'], lambda i: self.advance_offset_by_line(i))
        self.bind(['<number>', 'up'], lambda i: self.advance_offset_by_line(-i))
        self.bind(['<number>', 'right'], lambda i: self.advance_offset_by_char(i))

    def get_offset(self):
        return self._cur_offset

    def set_offset(self, value):
        if value < 0:
            self._cur_offset = 0
        elif value > self._file_buffer.size:
            self._cur_offset = self._file_buffer.size
        else:
            self._cur_offset = value

    def render(self, size, focus=False):
        maxcol, maxrow = size
        offset_canvas = []
        hex_canvas = []
        asc_canvas = []

        # todo: let user configure this
        self._visible_columns = (maxcol - 8 - 1 - 1 - 1) // 4

        # todo: if cursor_offset is outside view bounds, adjust _top_offset
        # todo: add "scrolloff" configuration variable

        for i in range(maxrow):
            row_offset = self._top_offset + i * self._visible_columns
            buffer = self._file_buffer.get_content_range(row_offset, self._visible_columns)
            offset_canvas.append(('%08x' % row_offset).encode('utf8'))
            hex_canvas.append(''.join('%02x ' % c for c in buffer).encode('utf8'))
            asc_canvas.append(''.join('%c' % c if c >= 32 and c < 127 else '.' for c in buffer).encode('utf8'))

        relative_cursor_offset = self.offset - self._top_offset

        canvas_def = []
        Dump.pos = 0
        def append(widget, width, is_focused):
            canvas_def.append((widget, Dump.pos, False, width))
            Dump.pos += width
        append(urwid.TextCanvas(offset_canvas), 9, False)
        if self.pane == self.HEX:
            cursor_pos = (
                (relative_cursor_offset % self._visible_columns) * 3,
                relative_cursor_offset // self._visible_columns)
            append(urwid.TextCanvas(hex_canvas, cursor=cursor_pos), self._visible_columns * 3, True)
            append(urwid.TextCanvas(asc_canvas), self._visible_columns, False)
        else:
            cursor_pos = (
                relative_cursor_offset % self._visible_columns,
                relative_cursor_offset // self._visible_columns)
            append(urwid.TextCanvas(hex_canvas), self._visible_columns * 3, False)
            append(urwid.TextCanvas(asc_canvas, cursor=cursor_pos), self._visible_columns, True)

        multi_canvas = urwid.CanvasJoin(canvas_def)
        if multi_canvas.cols() < maxcol:
            multi_canvas.pad_trim_left_right(0, maxcol - multi_canvas.cols())
        return multi_canvas

    def advance_offset_by_char(self, how_much):
        self.offset += how_much
        self._invalidate()

    def advance_offset_by_line(self, how_much):
        self.offset += how_much * self._visible_columns
        self._invalidate()

    def toggle_panes(self):
        self.pane = self.HEX if self.pane == self.ASC else self.ASC
        self._invalidate()

    offset = property(get_offset, set_offset)

class MainWindow(urwid.Frame):
    def __init__(self, file_buffer):
        self._file_buffer = file_buffer

        self._dump = self._make_dump()
        self._console = self._make_console()
        self._header = self._make_header()

        urwid.Frame.__init__(
            self,
            urwid.Pile([
                self._dump,
                ('fixed', 1, urwid.AttrMap(urwid.SolidFill(), 'header')),
                ('fixed', 1, urwid.Filler(self._console)),
            ]),
            urwid.AttrMap(self._header, 'header'))

        # focus the command line
        self.focus.set_focus(2)

    def get_caption(self):
        return re.sub('^hexvi( - )?', '', self._header.base_widget.get_text()[0])
    def set_caption(self, value):
        if not value:
            self._header.base_widget.set_text('hexvi')
        else:
            self._header.base_widget.set_text('hexvi - ' + value)
    caption = property(get_caption, set_caption)

    def _make_header(self):
        return urwid.Text(u'hexvi')

    def _make_dump(self):
        return Dump(self._file_buffer)

    def _make_console(self):
        return ReadlineEdit()

class Ui(object):
    def run(self, args):
        file_buffer = FileBuffer(args.file)
        self._main_window = MainWindow(file_buffer)
        self._main_window.caption = file_buffer.path
        urwid.MainLoop(
            self._main_window,
            palette=[
                ('selected', 'light red', ''),
                ('header', 'standout', ''),
            ],
            unhandled_input=self._key_pressed).run()

    def _key_pressed(self, key):
        if key == 'ctrl q':
            raise urwid.ExitMainLoop()
