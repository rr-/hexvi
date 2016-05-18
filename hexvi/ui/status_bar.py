''' Exports StatusBar. '''

import urwid
import hexvi.events as events
import hexvi.util as util

def _hilight(text):
    hilight = [('status-off', 1) for i in range(len(text))]
    for pos_x in range(len(text)):
        if text[pos_x:pos_x+1] != '0':
            break
        hilight[pos_x] = ('status-off0', 1)
    return hilight

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
        off_sep = ' / '
        off1 = util.fmt_hex(self._tab_manager.current_tab.current_offset)
        off2 = util.fmt_hex(self._tab_manager.current_tab.size)
        percent = ' (%d%%)' % (
            self._tab_manager.current_tab.current_offset * (
                100.0 / max(1, self._tab_manager.current_tab.size)))

        right_size = len(off1) + len(off2) + len(off_sep) + len(percent)
        left = '[%s] ' % self._app_state.mode.upper()
        left += util.trim_left(
            self._tab_manager.current_tab.long_name,
            size[0] - (right_size + len(left) + 3))

        composite_canvas = urwid.CanvasJoin([
            (
                urwid.TextCanvas([left.encode('utf-8')]),
                None, False, size[0] - right_size,
            ),
            (
                urwid.TextCanvas([off1.encode('utf-8')], [_hilight(off1)]),
                None, False, len(off1),
            ),
            (
                urwid.TextCanvas([off_sep.encode('utf-8')]),
                None, False, len(off_sep),
            ),
            (
                urwid.TextCanvas([off2.encode('utf-8')], [_hilight(off2)]),
                None, False, len(off2),
            ),
            (
                urwid.TextCanvas([percent.encode('utf-8')]),
                None, False, len(percent),
            )])
        return composite_canvas
