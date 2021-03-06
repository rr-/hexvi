''' Exports Dump. '''

import math
import regex
import urwid
import hexvi.events as events

def is_hex(char):
    return char in [ord(char) for char in list('0123456789abcdefABCDEF')]

def is_ascii(char):
    return char >= 32 and char < 127

class Dump(urwid.BoxWidget):
    ''' Hex / ASCII dump. '''

    def __init__(self, app_state, cmd_processor, tab_state, ui):
        self.editing = False
        self.tab_state = tab_state
        self._ui = ui
        self._cmd_processor = cmd_processor
        self._app_state = app_state
        self._user_byte_input = ''
        events.register_handler(events.PaneChange, lambda *_: self._invalidate())
        events.register_handler(events.OffsetChange, lambda *_: self._invalidate())
        events.register_handler(events.TabChange, self._tab_changed)

    def _tab_changed(self, evt):
        self.tab_state = evt.tab_state
        self.tab_state.validate_offsets()
        self._invalidate()

    def get_offset_digits(self):
        actual_digits = math.ceil(math.log(max(1, self.tab_state.size), 16))
        return max(8, math.ceil(actual_digits / 4) * 4)

    def render(self, size, focus=False):
        if self.tab_state is None:
            return urwid.TextCanvas([('-' * size[0]).encode('utf-8')] * size[1])
        off_digits = self.get_offset_digits()
        self._app_state.window_size = size
        self.tab_state.offset_digits = off_digits

        cur_off = self.tab_state.current_offset
        top_off = self.tab_state.top_offset
        vis_col = self.tab_state.visible_columns
        vis_row = self.tab_state.visible_rows

        vis_bytes = min(vis_col * vis_row + top_off, self.tab_state.size) - top_off

        buffer = self.tab_state.file_buffer.get(top_off, vis_bytes)
        off_lines, hex_lines, asc_lines = self._render_lines(buffer)
        off_hilight, hex_hilight, asc_hilight = self._render_hilight(
            off_lines, hex_lines, asc_lines)

        rel_cur_off = cur_off - top_off
        cursor_pos = (rel_cur_off % vis_col, rel_cur_off // vis_col)
        if self.tab_state.pane == self.tab_state.PANE_HEX:
            cursor_pos = (cursor_pos[0] * 3, cursor_pos[1])

        if self._user_byte_input:
            assert self.tab_state.pane == self.tab_state.PANE_HEX
            cursor_pos = (cursor_pos[0] + len(self._user_byte_input), cursor_pos[1])
            pos_x, pos_y = cursor_pos
            hex_lines[pos_y] = hex_lines[pos_y][:pos_x-1] \
                + self._user_byte_input.encode('utf-8') \
                + hex_lines[pos_y][pos_x:]

        canvas_def = []
        Dump.pos = 0
        def append(widget, width):
            canvas_def.append((widget, Dump.pos, False, width))
            Dump.pos += width
        append(urwid.TextCanvas(off_lines, off_hilight), off_digits + 1)
        append(urwid.TextCanvas(hex_lines, hex_hilight), vis_col * 3)
        append(urwid.TextCanvas(asc_lines, asc_hilight), vis_col)

        if not self._ui.blocked:
            if self.tab_state.pane == self.tab_state.PANE_ASC:
                canvas_def[2][0].cursor = cursor_pos
            else:
                canvas_def[1][0].cursor = cursor_pos

        multi_canvas = urwid.CanvasJoin(canvas_def)
        multi_canvas.pad_trim_left_right(0, size[0] - multi_canvas.cols())
        return multi_canvas

    def _render_lines(self, buffer):
        off_lines = []
        hex_lines = []
        asc_lines = []
        top_off = self.tab_state.top_offset
        vis_col = self.tab_state.visible_columns
        for i in range(self.tab_state.visible_rows):
            row_offset = top_off + i * vis_col
            row_buffer = buffer[i*vis_col:(i+1)*vis_col]
            off_lines.append(self._format_offset_row(row_offset).encode('utf-8'))
            hex_lines.append(self._format_hex_row(row_buffer).encode('utf-8'))
            asc_lines.append(self._format_asc_row(row_buffer).encode('utf-8'))
        return off_lines, hex_lines, asc_lines

    def _render_hilight(self, off_lines, hex_lines, asc_lines):
        vis_row = self.tab_state.visible_rows
        vis_col = self.tab_state.visible_columns
        top_off = self.tab_state.top_offset

        off_hilight = [[] for l in off_lines]
        hex_hilight = [[('hex', 3) for i in range(vis_col)] for l in hex_lines]
        asc_hilight = [[('asc', 1) for i in range(vis_col)] for l in asc_lines]

        if self._app_state.search_state.text:
            pattern = self._app_state.search_state.text.encode('utf8')
            half_page = vis_col * vis_row // 2
            search_buffer_off = max(top_off - half_page, 0)
            search_buffer_shift = top_off - search_buffer_off
            search_buffer_size = search_buffer_shift + vis_col * vis_row + half_page
            search_buffer_size = min(
                search_buffer_size + search_buffer_off, self.tab_state.size) \
                - search_buffer_off
            search_buffer = self.tab_state.file_buffer.get(
                search_buffer_off, search_buffer_size)
            for match in regex.finditer(pattern, search_buffer):
                for i in range(len(match.group())):
                    rel_cur_off = match.start() + i - search_buffer_shift
                    pos_y = rel_cur_off // vis_col
                    pos_x = rel_cur_off % vis_col
                    if pos_y >= 0 and pos_y < vis_row:
                        asc_hilight[pos_y][pos_x] = ('hex-search', 1)
                        hex_hilight[pos_y][pos_x] = ('asc-search', 3)

        for pos_y in range(vis_row):
            off_hilight[pos_y] = [('off', 1) for i in range(len(off_lines[pos_y]))]
            for pos_x in range(len(off_lines[pos_y])):
                if off_lines[pos_y][pos_x:pos_x+1] != b'0':
                    break
                off_hilight[pos_y][pos_x] = ('off0', 1)

        return off_hilight, hex_hilight, asc_hilight

    def keypress(self, _, key):
        if self._ui.blocked:
            return None
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

            if self.tab_state.pane == self.tab_state.PANE_HEX:
                if is_hex(ord(key)):
                    self._user_byte_input += key
                    self._invalidate()
                    if len(self._user_byte_input) == 2:
                        self._cmd_processor.accept_raw_byte_input(
                            int(self._user_byte_input, 16))
                        self._user_byte_input = ''
            else:
                self._cmd_processor.accept_raw_byte_input(ord(key))
            return None
        return key

    def _format_offset_row(self, offset):
        if offset - 1 < self.tab_state.size:
            return '%0*X' % (self.get_offset_digits(), offset)
        return ''

    def _format_asc_row(self, buffer):
        return '{:<{vis_col}}'.format(
            ''.join('%c' % c if is_ascii(c) else '.' for c in buffer),
            vis_col=self.tab_state.visible_columns)

    def _format_hex_row(self, buffer):
        return '{:<{vis_col}}'.format(
            ''.join('%02X ' % c for c in buffer),
            vis_col=self.tab_state.visible_columns*3)
