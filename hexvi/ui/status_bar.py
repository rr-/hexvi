''' Exports StatusBar. '''

import urwid
import hexvi.events as events
import hexvi.util as util

class StatusBar(urwid.Widget):
    ''' The thing that renders file size etc. at the bottom of the window. '''

    def __init__(self, app_state, tab_manager, *args, **kwargs):
        urwid.Widget.__init__(self, *args, **kwargs)
        self._app_state = app_state
        self._tab_manager = tab_manager
        events.register_handler(events.OffsetChange, lambda *_: self._invalidate())
        events.register_handler(events.ModeChange, lambda *_: self._invalidate())
        events.register_handler(events.TabChange, lambda *_: self._invalidate())

    def rows(self, size, focus=False):
        return 1

    def render(self, size, focus=False):
        right = '0x%X / 0x%X (%d%%)' % (
            self._tab_manager.current_tab.current_offset,
            self._tab_manager.current_tab.size,
            self._tab_manager.current_tab.current_offset * (
                100.0 / max(1, self._tab_manager.current_tab.size)))

        left = '[%s] ' % self._app_state.mode.upper()
        left += util.trim_left(
            self._tab_manager.current_tab.name,
            size[0] - (len(right) + len(left) + 3))

        left_canvas = urwid.TextCanvas([left.encode('utf-8')])
        right_canvas = urwid.TextCanvas([right.encode('utf-8')])
        composite_canvas = urwid.CanvasJoin([
            (left_canvas, None, False, size[0] - len(right)),
            (right_canvas, None, False, len(right))])
        return composite_canvas
