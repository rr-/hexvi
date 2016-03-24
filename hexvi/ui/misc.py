''' Miscellaneous miniwidgets '''

import urwid
import urwid.util

class DumbPile(urwid.Pile):
    ''' A Pile that doesn't mess with keyboard '''

    def keypress(self, pos, key):
        return self.focus.keypress(pos, key)

class SelectableText(urwid.Edit):
    ''' A text that can be focused (e.g. selectable items in a list box) '''

    def valid_char(self, char):
        return False

class Button(urwid.WidgetWrap):
    '''
    Simplified variant of urwid button that doesn't add "< >" decoration.
    '''

    def sizing(self):
        return frozenset(['flow'])

    signals = ['click']

    def __init__(self, label, on_press=None, user_data=None):
        self._label = urwid.SelectableIcon('', 0)
        if on_press:
            urwid.connect_signal(self, 'click', on_press, user_data)
        self.set_label(label)
        super().__init__(self._label)

    def set_label(self, label):
        self._label.set_text(label)

    def get_label(self):
        return self._label.text

    label = property(get_label, set_label)

    def keypress(self, size, key):
        if self._command_map[key] != 'activate':
            return key
        self._emit('click')

    def mouse_event(self, size, event, button, x, y, focus):
        if button != 1 or not urwid.util.is_mouse_press(event):
            return False
        self._emit('click')
        return True
