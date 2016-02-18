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
from app_state import AppState
from readline_edit import ReadlineEdit

class Dump(urwid.BoxWidget):
    PANE_HEX = 'hex'
    PANE_ASC = 'asc'

    def __init__(self, main_window, file_buffer):

        self._pane = self.PANE_HEX
        self._file_buffer = file_buffer
        self._top_offset = 0
        self._cur_offset = 0
        self._size = (0, 0)

        b = BindingCollection()
        b.add(['tab'], self.toggle_panes)
        b.add(['h'], lambda: self.move_cur_offset_by_char(-1))
        b.add(['j'], lambda: self.move_cur_offset_by_line(1))
        b.add(['k'], lambda: self.move_cur_offset_by_line(-1))
        b.add(['l'], lambda: self.move_cur_offset_by_char(1))
        b.add(['<number>', 'h'], lambda i: self.move_cur_offset_by_char(-i))
        b.add(['<number>', 'j'], lambda i: self.move_cur_offset_by_line(i))
        b.add(['<number>', 'k'], lambda i: self.move_cur_offset_by_line(-i))
        b.add(['<number>', 'l'], lambda i: self.move_cur_offset_by_char(i))
        b.add(['left'], lambda: self.move_cur_offset_by_char(-1))
        b.add(['down'], lambda: self.move_cur_offset_by_line(1))
        b.add(['up'], lambda: self.move_cur_offset_by_line(-1))
        b.add(['right'], lambda: self.move_cur_offset_by_char(1))
        b.add(['<number>', 'left'], lambda i: self.move_cur_offset_by_char(-i))
        b.add(['<number>', 'down'], lambda i: self.move_cur_offset_by_line(i))
        b.add(['<number>', 'up'], lambda i: self.move_cur_offset_by_line(-i))
        b.add(['<number>', 'right'], lambda i: self.move_cur_offset_by_char(i))
        b.add(['g', 'g'], lambda: self.set_cur_offset(0))
        b.add(['<hex>', 'G'], lambda i: self.set_cur_offset(i))
        b.add(['G'], lambda: self.set_cur_offset(self._file_buffer.size))
        b.add(['^'], self.move_cur_offset_to_start_of_line)
        b.add(['$'], self.move_cur_offset_to_end_of_line)
        b.add([':'], lambda: main_window.set_mode(AppState.MODE_COMMAND))
        b.compile()
        self.bindings = b

    def keypress(self, pos, key):
        if self.bindings.keypress(key):
            return None
        return key

    def get_pane(self):
        return self._pane

    def set_pane(self, value):
        self._pane = value
        self._invalidate()

    def toggle_panes(self):
        self.pane = [self.PANE_HEX, self.PANE_ASC][self.pane == self.PANE_HEX]

    def get_cur_offset(self):
        return self._cur_offset

    def set_cur_offset(self, value):
        self._cur_offset = max(0, min(self._file_buffer.size, value))
        self._invalidate()

    def move_cur_offset_by_char(self, how_much):
        self.cur_offset += how_much

    def move_cur_offset_by_line(self, how_much):
        self.cur_offset += how_much * self.visible_columns

    def move_cur_offset_to_start_of_line(self):
        self.cur_offset -= self.cur_offset % self.visible_columns

    def move_cur_offset_to_end_of_line(self):
        self.cur_offset += self.visible_columns - 1 - self.cur_offset % self.visible_columns

    def get_top_offset(self):
        return self._top_offset

    def set_top_offset(self, value):
        self._top_offset = max(0, min(self._file_buffer.size, value))
        self._invalidate()

    def get_bottom_offset(self):
        return self.top_offset + self._size[1] * self.visible_columns

    def get_visible_columns(self):
        # todo: let user override this in the configuration
        return (self._size[0] - 8 - 1 - 1 - 1) // 4

    def render(self, size, focus=False):
        self._size = size
        width, height = size

        # todo: let user override this in the configuration
        scrolloff = 0
        scrolloff = max(0, scrolloff) + 1
        if self.top_offset + (scrolloff - 1) * self.visible_columns > self.cur_offset:
            self.top_offset -= self.visible_columns * ((self.top_offset - self.cur_offset - 1) // self.visible_columns + scrolloff)
        elif self.cur_offset >= self.bottom_offset - (scrolloff - 1) * self.visible_columns:
            self.top_offset += self.visible_columns * ((self.cur_offset - self.bottom_offset) // self.visible_columns + scrolloff)

        off_lines = []
        hex_lines = []
        asc_lines = []
        for i in range(height):
            row_offset = self.top_offset + i * self.visible_columns
            buffer = self._file_buffer.get_content_range(row_offset, self.visible_columns)
            off_lines.append((b'%08x' % row_offset))
            hex_lines.append(b''.join(b'%02x ' % c for c in buffer))
            asc_lines.append(b''.join(b'%c' % c if c >= 32 and c < 127 else b'.' for c in buffer))

        relative_cursor_offset = self.cur_offset - self.top_offset
        cursor_pos = (
            relative_cursor_offset % self.visible_columns,
            relative_cursor_offset // self.visible_columns)
        if self.pane == self.PANE_HEX:
            cursor_pos = (cursor_pos[0] * 3, cursor_pos[1])

        canvas_def = []
        Dump.pos = 0
        def append(widget, width, is_focused):
            canvas_def.append((widget, Dump.pos, False, width))
            Dump.pos += width
        append(urwid.TextCanvas(off_lines), 9, False)
        append(urwid.TextCanvas(hex_lines), self.visible_columns * 3, True)
        append(urwid.TextCanvas(asc_lines), self.visible_columns, False)

        canvas_def[[1, 2][self.pane == self.PANE_ASC]][0].cursor = cursor_pos

        multi_canvas = urwid.CanvasJoin(canvas_def)
        if multi_canvas.cols() < width:
            multi_canvas.pad_trim_left_right(0, width - multi_canvas.cols())
        return multi_canvas

    cur_offset = property(get_cur_offset, set_cur_offset)
    top_offset = property(get_top_offset, set_top_offset)
    pane = property(get_pane, set_pane)
    bottom_offset = property(get_bottom_offset)
    visible_columns = property(get_visible_columns)

class Console(ReadlineEdit):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._main_window = main_window

        b = BindingCollection()
        b.add(['esc'], lambda: main_window.set_mode(AppState.MODE_NORMAL))
        b.compile()
        self.bindings = b

    def keypress(self, pos, key):
        if key == 'backspace' and not self.edit_text:
            self._main_window.set_mode(AppState.MODE_NORMAL)
        if self.bindings.keypress(key):
            return None
        return super().keypress(pos, key)

    def get_prompt(self):
        return self.caption

    def set_prompt(self, value):
        self.set_caption(value)

    prompt = property(get_prompt, set_prompt)

class MainWindow(urwid.Frame):
    def __init__(self, app_state):
        self._app_state = app_state

        self._header = self._make_header()
        self._dump = self._make_dump()
        self._console = self._make_console()

        urwid.Frame.__init__(
            self,
            urwid.Pile([
                self._dump,
                ('fixed', 1, urwid.AttrMap(urwid.SolidFill(), 'header')),
                ('fixed', 1, urwid.Filler(self._console)),
            ]),
            urwid.AttrMap(self._header, 'header'))

        self.set_mode(AppState.MODE_NORMAL)

    def get_caption(self):
        return re.sub('^hexvi( - )?', '', self._header.base_widget.get_text()[0])

    def set_caption(self, value):
        self._header.base_widget.set_text('hexvi' if not value else 'hexvi - ' + value)

    def set_mode(self, new_mode):
        self._app_state.mode = new_mode
        if new_mode == AppState.MODE_COMMAND:
            self._console.prompt = ':'
            self.focus.set_focus(2)
        elif new_mode == AppState.MODE_NORMAL:
            self._console.edit_text = ''
            self._console.prompt = ''
            self.focus.set_focus(0)

    def _make_header(self):
        return urwid.Text(u'hexvi')

    def _make_dump(self):
        return Dump(self, self._app_state.file_buffer)

    def _make_console(self):
        return Console(self)

    caption = property(get_caption, set_caption)

class Ui(object):
    def run(self, args):
        app_state = AppState(args)
        self._main_window = MainWindow(app_state)
        self._main_window.caption = app_state.file_buffer.path
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
