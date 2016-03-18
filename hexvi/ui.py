import math
import regex
import urwid
import hexvi.events as events
from hexvi.app_state import AppState
from hexvi.readline_edit import ReadlineEdit

def trim_left(text, size):
    ellipsis = '(...)'
    if len(text) <= size:
        return text
    return ellipsis + text[len(ellipsis)+len(text)-size:]

def is_hex(c):
    return c in [ord(c) for c in list('0123456789abcdefABCDEF')]

def is_ascii(c):
    return c >= 32 and c < 127

class Dump(urwid.BoxWidget):
    def __init__(self, app_state, file_state):
        self.editing = False
        self._app_state = app_state
        self._file_state = file_state
        self._user_byte_input = ''
        events.register_handler(events.PaneChange, lambda *_: self._invalidate())
        events.register_handler(events.OffsetChange, lambda *_: self._invalidate())

    def get_offset_digits(self):
        return max(4, math.ceil(math.log(max(1, self._file_state.size), 16)))

    def render(self, size, focus=False):
        off_digits = self.get_offset_digits()
        self._app_state.window_size = size
        self._file_state.offset_digits = off_digits

        cur_off = self._file_state.cur_offset
        top_off = self._file_state.top_offset
        vis_col = self._file_state.visible_columns
        vis_row = self._file_state.visible_rows

        vis_bytes = min(vis_col * vis_row + top_off, self._file_state.size) - top_off

        buffer = self._file_state.file_buffer.get(top_off, vis_bytes)
        off_lines = []
        hex_lines = []
        asc_lines = []
        for i in range(vis_row):
            row_offset = top_off + i * vis_col
            row_buffer = buffer[i*vis_col:(i+1)*vis_col]
            off_lines.append(self._format_offset_row(row_offset))
            hex_lines.append(self._format_hex_row(row_buffer))
            asc_lines.append(self._format_asc_row(row_buffer))

        off_lines = [l.encode('utf-8') for l in off_lines]
        hex_lines = [(l + ' ').encode('utf-8') for l in hex_lines]
        asc_lines = [(l + ' ').encode('utf-8') for l in asc_lines]

        off_hilight = [[] for l in off_lines]
        hex_hilight = [[('hex', 3) for i in range(vis_col)] for l in hex_lines]
        asc_hilight = [[('asc', 1) for i in range(vis_col)] for l in asc_lines]

        if self._app_state.search_state.text:
            half_page = vis_col * vis_row // 2
            search_buffer_off = max(top_off - half_page, 0)
            search_buffer_shift = top_off - search_buffer_off
            search_buffer_size = search_buffer_shift + vis_col * vis_row + half_page
            search_buffer_size = min(
                search_buffer_size + search_buffer_off,
                self._file_state.size) - search_buffer_off
            search_buffer = self._file_state.file_buffer.get(
                search_buffer_off, search_buffer_size)
            pattern = self._app_state.search_state.text.encode('utf8')
            for m in regex.finditer(pattern, search_buffer):
                for i in range(len(m.group())):
                    rel_cur_off = m.start() + i - search_buffer_shift
                    y = rel_cur_off // vis_col
                    x = rel_cur_off % vis_col
                    if y >= 0    and y < vis_row:
                        asc_hilight[y][x] = ('hex-search', 1)
                        hex_hilight[y][x] = ('asc-search', 3)

        for y in range(vis_row):
            off_hilight[y] = [('off', 1) for i in range(len(off_lines[y]))]
            for x in range(len(off_lines[y])):
                if off_lines[y][x:x+1] != b'0':
                    break
                off_hilight[y][x] = ('off0', 1)

        rel_cur_off = cur_off - top_off
        cursor_pos = (rel_cur_off % vis_col, rel_cur_off // vis_col)
        if self._file_state.pane == self._file_state.PANE_HEX:
            cursor_pos = (cursor_pos[0] * 3, cursor_pos[1])

        if self._user_byte_input:
            assert self._file_state.pane == self._file_state.PANE_HEX
            cursor_pos = (cursor_pos[0] + len(self._user_byte_input), cursor_pos[1])
            x, y = cursor_pos
            hex_lines[y] = hex_lines[y][:x-1] \
                + self._user_byte_input.encode('utf-8') \
                + hex_lines[y][x:]

        canvas_def = []
        Dump.pos = 0
        def append(widget, width):
            canvas_def.append((widget, Dump.pos, False, width))
            Dump.pos += width
        append(urwid.TextCanvas(off_lines, off_hilight), off_digits + 1)
        append(urwid.TextCanvas(hex_lines, hex_hilight), vis_col * 3)
        append(urwid.TextCanvas(asc_lines, asc_hilight), vis_col)

        if self._file_state.pane == self._file_state.PANE_ASC:
            canvas_def[2][0].cursor = cursor_pos
        else:
            canvas_def[1][0].cursor = cursor_pos

        multi_canvas = urwid.CanvasJoin(canvas_def)
        multi_canvas.pad_trim_left_right(0, size[0] - multi_canvas.cols())
        return multi_canvas

    def keypress(self, _, key):
        if self.editing:
            # if we're dealing with nontrivial keypress such as ctrl+something or tab
            if len(key) != 1:
                if self._user_byte_input:
                    # cancel editing on escape
                    if key == 'esc':
                        self._user_byte_input = ''
                        self._invalidate()
                        return key
                    # otherwise disallow running any bindings
                    return None
                else:
                    return key

            if self._file_state.pane == self._file_state.PANE_HEX:
                if is_hex(ord(key)):
                    self._user_byte_input += key
                    self._invalidate()
                    if len(self._user_byte_input) == 2:
                        self._app_state.accept_byte_input(int(self._user_byte_input, 16))
                        self._user_byte_input = ''
            else:
                self._app_state.accept_byte_input(ord(key))
            return None
        return key

    def _format_offset_row(self, offset):
        if offset - 1 < self._file_state.size:
            return '%0*X' % (self.get_offset_digits(), offset)
        return ''

    @staticmethod
    def _format_asc_row(buffer):
        return ''.join('%c' % c if is_ascii(c) else '.' for c in buffer)

    @staticmethod
    def _format_hex_row(buffer):
        return ''.join('%02X ' % c for c in buffer)

class Console(ReadlineEdit):
    def __init__(self, app_state, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app_state = app_state

    def keypress(self, pos, key):
        if key == 'backspace' and not self.edit_text:
            self._app_state.mode = AppState.MODE_NORMAL
            return None
        if key == 'enter':
            self._app_state.accept_command_input(self.edit_text)
        return super().keypress(pos, key)

    def get_prompt(self):
        return self.caption

    def set_prompt(self, value):
        self.set_caption(value)

    prompt = property(get_prompt, set_prompt)

class StatusBar(urwid.Widget):
    def __init__(self, app_state, *args, **kwargs):
        urwid.Widget.__init__(self, *args, **kwargs)
        self._app_state = app_state
        events.register_handler(events.OffsetChange, lambda *_: self._invalidate())
        events.register_handler(events.ModeChange, lambda *_: self._invalidate())

    def rows(self, size, focus=False):
        return 1

    def render(self, size, focus=False):
        right = '0x%X / 0x%X (%d%%)' % (
            self._app_state.cur_file.cur_offset,
            self._app_state.cur_file.size,
            self._app_state.cur_file.cur_offset * (
                100.0 / max(1, self._app_state.cur_file.size)))

        left = '[%s] ' % self._app_state.mode.upper()
        left += trim_left(
            self._app_state.cur_file.file_buffer.path or '[No Name]',
            size[0] - (len(right) + len(left) + 3))

        left_canvas = urwid.TextCanvas([left.encode('utf-8')])
        right_canvas = urwid.TextCanvas([right.encode('utf-8')])
        composite_canvas = urwid.CanvasJoin([
            (left_canvas, None, False, size[0] - len(right)),
            (right_canvas, None, False, len(right))])
        return composite_canvas

class DumbPile(urwid.Pile):
    def keypress(self, pos, key):
        return self.focus.keypress(pos, key)

class MainWindow(urwid.Frame):
    def __init__(self, app_state):
        self._app_state = app_state

        self._header = urwid.Text(u'hexvi')
        self._dump = Dump(self._app_state, self._app_state.cur_file)
        self._status_bar = StatusBar(self._app_state)
        self._console = Console(self._app_state)

        urwid.Frame.__init__(
            self,
            DumbPile([
                self._dump,
                ('fixed', 1, urwid.Filler(urwid.AttrMap(self._status_bar, 'status'))),
                ('fixed', 1, urwid.Filler(self._console)),
            ]),
            urwid.AttrMap(self._header, 'header'))

    def started(self):
        events.register_handler(events.PrintMessage, self._message_requested)
        events.register_handler(events.ModeChange, self._mode_changed)

    def get_caption(self):
        return regex.sub('^hexvi( - )?', '', self._header.base_widget.get_text()[0])

    def set_caption(self, value):
        self._header.base_widget.set_text(
            'hexvi' if not value else 'hexvi - ' + value)

    def _message_requested(self, evt):
        self._console.prompt = (evt.style, evt.message)
        self._console.edit_text = ''

    def _mode_changed(self, evt):
        self._console.edit_text = ''
        if evt.mode in AppState.NON_COMMAND_MODES:
            self._dump.editing = evt.mode in AppState.INPUT_MODES
            self._console.prompt = ''
            self.focus.set_focus(0)
        else:
            self._console.prompt = self._app_state.settings.mode_chars[evt.mode]
            self.focus.set_focus(2)

    caption = property(get_caption, set_caption)

class Ui(object):
    def __init__(self, app_state):
        self._app_state = app_state
        self._main_window = MainWindow(self._app_state)
        self._app_state.mode = AppState.MODE_NORMAL

        events.register_handler(events.ProgramExit, lambda *args: self._exit())
        events.register_handler(events.ColorChange, self._color_changed)

        # TODO: subscribe to changes of app_state.cur_file
        self._main_window.caption = self._app_state.cur_file.file_buffer.path

        self._loop = urwid.MainLoop(
            self._main_window, unhandled_input=self._key_pressed)
        self._loop.screen.set_terminal_properties(
            self._app_state.settings.term_colors)

    def run(self):
        self._main_window.started()
        self._loop.run()

    def _color_changed(self, evt):
        scr = self._loop.screen
        scr.register_palette_entry(
            evt.target,
            evt.fg_style,
            evt.bg_style,
            foreground_high=evt.fg_style_high,
            background_high=evt.bg_style_high)
        scr.clear()

    @staticmethod
    def _exit():
        raise urwid.ExitMainLoop()

    def _key_pressed(self, key):
        self._app_state.mappings[self._app_state.mode].keypress(key)
