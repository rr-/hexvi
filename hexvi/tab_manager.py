''' Exports TabManager. '''

import hexvi.events as events
from hexvi.app_state import SearchState
from hexvi.tab_state import TabState

class TabManager(object):
    ''' The class responsible for managing tab lifecycles. '''

    def __init__(self, app_state):
        self.tabs = []
        self._tab_index = None
        self._app_state = app_state
        self._old_tab_id = None

    @property
    def current_tab(self):
        return None if self._tab_index is None else self.tabs[self._tab_index]

    def close_current_tab(self):
        ''' Closes currently focused tab. '''
        # TODO: check if the file was modified
        self._do_close_current_tab()

    def _do_close_current_tab(self):
        events.notify(events.TabClose(self.current_tab))
        self.tabs = self.tabs[:self._tab_index] + self.tabs[self._tab_index+1:]
        if not self.tabs:
            events.notify(events.ProgramExit())
        elif self.tab_index >= len(self.tabs):
            self.tab_index = len(self.tabs) - 1
        else:
            events.notify(events.TabChange(self.current_tab))

    def open_tab(self, path=None):
        ''' Opens a new tab and focuses it. '''
        if path:
            new_tab = TabState(self._app_state, path)
        else:
            new_tab = TabState(self._app_state)
        self.tabs.append(new_tab)
        events.notify(events.TabOpen(new_tab))
        self.tab_index = len(self.tabs) - 1

    def open_in_current_tab(self, path):
        ''' Opens a file in an existing focused tab. '''
        new_tab = TabState(self._app_state, path)
        self.tabs[self.tab_index] = new_tab
        events.notify(events.TabChange(self.current_tab))

    def cycle_tabs(self, direction):
        ''' Focuses next or previous tab. '''
        self.tab_index += 1 if direction == SearchState.DIR_FORWARD else -1

    def get_tab_index(self):
        return self._tab_index

    def set_tab_index(self, new_tab_index):
        if new_tab_index != self._tab_index:
            self._tab_index = new_tab_index
            self._tab_index %= len(self.tabs)
        if self._old_tab_id != id(self.current_tab):
            events.notify(events.TabChange(self.current_tab))
            self._old_tab_id = id(self.current_tab)

    tab_index = property(get_tab_index, set_tab_index)
