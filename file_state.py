from file_buffer import FileBuffer
import zope.event
import zope.event.classhandler

class WindowSizeChangeEvent(object):
    def __init__(self, size):
        self.size = size

class OffsetChangeEvent(object):
    def __init__(self, file_state):
        self.file_state = file_state

class PaneChangeEvent(object):
    def __init__(self, file_state):
        self.file_state = file_state

class FileState(object):
    PANE_HEX = 'hex'
    PANE_ASC = 'asc'

    def __init__(self, file):
        self.file_buffer = FileBuffer(file)
        self._pane = self.PANE_HEX
        self._top_offset = 0
        self._cur_offset = 0
        self._window_size = (0, 0)
        zope.event.classhandler.handler(WindowSizeChangeEvent, self.window_size_changed)

    def window_size_changed(self, event):
        self._window_size = event.size
        self._validate_top_offset()

    def toggle_panes(self):
        self.pane = [self.PANE_HEX, self.PANE_ASC][self.pane == self.PANE_HEX]

    def get_visible_columns(self):
        # todo: let user override this in the configuration
        return (self._window_size[0] - 8 - 1 - 1 - 1) // 4

    def get_pane(self):
        return self._pane

    def set_pane(self, value):
        self._pane = value
        zope.event.notify(PaneChangeEvent(self))

    def set_top_offset(self, value):
        self._top_offset = max(0, min(self.size, value))
        zope.event.notify(OffsetChangeEvent(self))

    def get_bottom_offset(self):
        return self.top_offset + self._window_size[1] * self.visible_columns

    def get_cur_offset(self):
        return self._cur_offset

    def set_cur_offset(self, value):
        self._cur_offset = max(0, min(self.size, value))
        self._validate_top_offset()
        zope.event.notify(OffsetChangeEvent(self))

    def get_top_offset(self):
        return self._top_offset

    def move_cur_offset_by_char(self, how_much):
        self.cur_offset += how_much

    def move_cur_offset_by_line(self, how_much):
        self.cur_offset += how_much * self.visible_columns

    def move_cur_offset_to_start_of_line(self):
        self.cur_offset -= self.cur_offset % self.visible_columns

    def move_cur_offset_to_end_of_line(self):
        self.cur_offset += self.visible_columns - 1 - self.cur_offset % self.visible_columns

    def _validate_top_offset(self):
        # todo: let user override this in the configuration
        scrolloff = 0
        scrolloff = max(0, scrolloff) + 1
        if self.top_offset + (scrolloff - 1) * self.visible_columns > self.cur_offset:
            self.top_offset -= self.visible_columns * ((self.top_offset - self.cur_offset - 1) // self.visible_columns + scrolloff)
        elif self.cur_offset >= self.bottom_offset - (scrolloff - 1) * self.visible_columns:
            self.top_offset += self.visible_columns * ((self.cur_offset - self.bottom_offset) // self.visible_columns + scrolloff)

    cur_offset = property(get_cur_offset, set_cur_offset)
    top_offset = property(get_top_offset, set_top_offset)
    pane = property(get_pane, set_pane)
    bottom_offset = property(get_bottom_offset)
    visible_columns = property(get_visible_columns)
    size = property(lambda self: self.file_buffer.size)
