''' Exports TabState. '''

import os.path
import hexvi.events as events
from hexvi.file_buffer import FileBuffer

class TabState(object):
    '''
    Tab state, i.e. one widget for the file buffer.
    Contains visual information on the file (such as currently selected offset
    etc.), and link to the file buffer.
    '''

    PANE_HEX = 'hex'
    PANE_ASC = 'asc'

    def __init__(self, app_state, file_path=None):
        self.file_buffer = FileBuffer(file_path)
        self._app_state = app_state
        self._pane = self.PANE_HEX
        self._top_offset = 0
        self._cur_offset = 0
        self._window_size = app_state.window_size
        self._offset_digits = 0
        events.register_handler(events.WindowSizeChange, self.window_size_changed)

    def get_offset_digits(self):
        return self._offset_digits

    def set_offset_digits(self, value):
        if value != self._offset_digits:
            self._offset_digits = value
            self._validate_top_offset()

    def window_size_changed(self, event):
        self._window_size = event.size
        self._validate_top_offset()

    def get_visible_rows(self):
        return self._window_size[1]

    def get_visible_columns(self):
        # TODO: let user override this in the configuration
        return (self._window_size[0] - self._offset_digits - 1) // 4

    def get_pane(self):
        return self._pane

    def set_pane(self, value):
        self._pane = value
        events.notify(events.PaneChange(self))

    def set_top_offset(self, value):
        self._top_offset = max(0, min(self.size, value))
        events.notify(events.OffsetChange(self))

    def get_bottom_offset(self):
        return self.top_offset + self._window_size[1] * self.visible_columns

    def get_current_offset(self):
        return self._cur_offset

    def set_current_offset(self, value):
        self._cur_offset = max(0, min(self.size, value))
        self._validate_top_offset()
        events.notify(events.OffsetChange(self))

    def get_top_offset(self):
        return self._top_offset

    def _validate_top_offset(self):
        dis = self._app_state.settings.scrolloff
        dis = max(0, dis) + 1
        cur_off, vis_col = self.current_offset, self.visible_columns
        top_off, bot_off = self.top_offset, self.bottom_offset
        if top_off + (dis - 1) * vis_col > cur_off:
            top_off -= vis_col * ((top_off - cur_off - 1) // vis_col + dis)
        elif cur_off >= bot_off - (dis - 1) * vis_col:
            top_off += vis_col * ((cur_off - bot_off) // vis_col + dis)
        self.top_offset = top_off

    @property
    def long_name(self):
        return self.file_buffer.path or '[No Name]'

    @property
    def short_name(self):
        if not self.file_buffer.path:
            return '[No Name]'
        file_name = os.path.basename(self.file_buffer.path)
        if file_name != self.file_buffer.path:
            return '(..)' + file_name
        return file_name

    current_offset = property(get_current_offset, set_current_offset)
    top_offset = property(get_top_offset, set_top_offset)
    bottom_offset = property(get_bottom_offset)
    size = property(lambda self: self.file_buffer.size)
    pane = property(get_pane, set_pane)
    visible_rows = property(get_visible_rows)
    visible_columns = property(get_visible_columns)
    offset_digits = property(get_offset_digits, set_offset_digits)
