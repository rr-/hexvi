''' Miscellaneous miniwidgets '''

import urwid

class DumbPile(urwid.Pile):
    ''' A Pile that doesn't mess with keyboard '''

    def keypress(self, pos, key):
        return self.focus.keypress(pos, key)

class SelectableText(urwid.Edit):
    ''' A text that can be focused (e.g. selectable items in a list box) '''

    def valid_char(self, char):
        return False
