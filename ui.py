import sys
import re

try:
    import urwid
except ImportError as e:
    if e.name is None:
        raise
    print('Please install %s.' % e.name)
    sys.exit(1)

from bindings import BindingCollection
from file_buffer import FileBuffer
from readline_edit import ReadlineEdit

class Dump(urwid.BoxWidget):
    HEX = 'hex'
    ASC = 'asc'

    def __init__(self, file_buffer):

        self.pane = self.HEX
        self._file_buffer = file_buffer
        self._top_offset = 0
        self._cur_offset = 0
        self._size = (0, 0)

        b = BindingCollection()
        b.add(['tab'], self.toggle_panes)
        b.add(['h'], lambda: self.advance_offset_by_char(-1))
        b.add(['j'], lambda: self.advance_offset_by_line(1))
        b.add(['k'], lambda: self.advance_offset_by_line(-1))
        b.add(['l'], lambda: self.advance_offset_by_char(1))
        b.add(['<number>', 'h'], lambda i: self.advance_offset_by_char(-i))
        b.add(['<number>', 'j'], lambda i: self.advance_offset_by_line(i))
        b.add(['<number>', 'k'], lambda i: self.advance_offset_by_line(-i))
        b.add(['<number>', 'l'], lambda i: self.advance_offset_by_char(i))
        b.add(['left'], lambda: self.advance_offset_by_char(-1))
        b.add(['down'], lambda: self.advance_offset_by_line(1))
        b.add(['up'], lambda: self.advance_offset_by_line(-1))
        b.add(['right'], lambda: self.advance_offset_by_char(1))
        b.add(['<number>', 'left'], lambda i: self.advance_offset_by_char(-i))
        b.add(['<number>', 'down'], lambda i: self.advance_offset_by_line(i))
        b.add(['<number>', 'up'], lambda i: self.advance_offset_by_line(-i))
        b.add(['<number>', 'right'], lambda i: self.advance_offset_by_char(i))
        b.add(['g', 'g'], lambda: self.go_to_offset(0))
        b.add(['<hex>', 'G'], lambda i: self.go_to_offset(i))
        b.add(['G'], lambda: self.go_to_offset(self._file_buffer.size))
        b.compile()
        self.binding_collection = b

    def keypress(self, pos, key):
        return self.binding_collection.keypress(key)

    def get_cur_offset(self):
        return self._cur_offset

    def set_cur_offset(self, value):
        self._cur_offset = max(0, min(self._file_buffer.size, value))

    def get_top_offset(self):
        return self._top_offset

    def set_top_offset(self, value):
        self._top_offset = max(0, min(self._file_buffer.size, value))

    def get_bottom_offset(self):
        return self.top_offset + self._size[1] * self.visible_columns

    def get_visible_columns(self):
        # todo: let user override this in the configuration
        return (self._size[0] - 8 - 1 - 1 - 1) // 4

    def render(self, size, focus=False):
        self._size = size
        width, height = size

        # todo: add "scrolloff" configuration variable
        if self.cur_offset < self.top_offset:
            self.top_offset -= self.visible_columns * (self.top_offset - self.cur_offset) // self.visible_columns
        elif self.cur_offset >= self.bottom_offset:
            self.top_offset += self.visible_columns * ((self.cur_offset - self.bottom_offset) // self.visible_columns + 1)

        offset_canvas = []
        hex_canvas = []
        asc_canvas = []
        for i in range(height):
            row_offset = self.top_offset + i * self.visible_columns
            buffer = self._file_buffer.get_content_range(row_offset, self.visible_columns)
            offset_canvas.append(('%08x' % row_offset).encode('utf8'))
            hex_canvas.append(''.join('%02x ' % c for c in buffer).encode('utf8'))
            asc_canvas.append(''.join('%c' % c if c >= 32 and c < 127 else '.' for c in buffer).encode('utf8'))

        relative_cursor_offset = self.cur_offset - self.top_offset

        canvas_def = []
        Dump.pos = 0
        def append(widget, width, is_focused):
            canvas_def.append((widget, Dump.pos, False, width))
            Dump.pos += width

        append(urwid.TextCanvas(offset_canvas), 9, False)

        if self.pane == self.HEX:
            cursor_pos = (
                (relative_cursor_offset % self.visible_columns) * 3,
                relative_cursor_offset // self.visible_columns)
            append(urwid.TextCanvas(hex_canvas, cursor=cursor_pos), self.visible_columns * 3, True)
            append(urwid.TextCanvas(asc_canvas), self.visible_columns, False)
        else:
            cursor_pos = (
                relative_cursor_offset % self.visible_columns,
                relative_cursor_offset // self.visible_columns)
            append(urwid.TextCanvas(hex_canvas), self.visible_columns * 3, False)
            append(urwid.TextCanvas(asc_canvas, cursor=cursor_pos), self.visible_columns, True)

        multi_canvas = urwid.CanvasJoin(canvas_def)
        if multi_canvas.cols() < width:
            multi_canvas.pad_trim_left_right(0, width - multi_canvas.cols())
        return multi_canvas

    def keypress(self, pos, key):
        return self.binding_collection.keypress(key)

    def advance_offset_by_char(self, how_much):
        self.cur_offset += how_much
        self._invalidate()

    def advance_offset_by_line(self, how_much):
        self.cur_offset += how_much * self.visible_columns
        self._invalidate()

    def go_to_offset(self, offset):
        self.cur_offset = offset
        self._invalidate()

    def toggle_panes(self):
        self.pane = self.HEX if self.pane == self.ASC else self.ASC
        self._invalidate()

    cur_offset = property(get_cur_offset, set_cur_offset)
    top_offset = property(get_top_offset, set_top_offset)
    bottom_offset = property(get_bottom_offset)
    visible_columns = property(get_visible_columns)

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
        self._header.base_widget.set_text('hexvi' if not value else 'hexvi - ' + value)

    def _make_header(self):
        return urwid.Text(u'hexvi')

    def _make_dump(self):
        return Dump(self._file_buffer)

    def _make_console(self):
        return ReadlineEdit()

    caption = property(get_caption, set_caption)

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
