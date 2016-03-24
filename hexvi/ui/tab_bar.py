''' Exports TabBar. '''

import urwid
import hexvi.events as events

class TabBar(urwid.Columns):
    ''' The thing that renders file tabs at the top of the window. '''

    def __init__(self, tab_manager):
        super().__init__([], dividechars=1)
        self._tab_manager = tab_manager
        events.register_handler(events.TabOpen, lambda *_: self._update())
        events.register_handler(events.TabClose, lambda *_: self._update())
        events.register_handler(events.TabChange, lambda *_: self._update())

    def _update(self):
        self.contents.clear()
        if not self._tab_manager.tabs or self._tab_manager.tab_index is None:
            return
        for i, tab in enumerate(self._tab_manager.tabs):
            class_name = 'tab'
            if i == self._tab_manager.tab_index:
                class_name += '-focused'
            button = urwid.AttrWrap(
                urwid.Button(
                    tab.name, on_press=self._button_clicked, user_data=i),
                class_name)
            options = self.options('given', len(tab.name) + 4)
            self.contents.append((button, options))
        self.focus_position = self._tab_manager.tab_index

    def _button_clicked(self, _, user_data):
        self._tab_manager.tab_index = user_data
