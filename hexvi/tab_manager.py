''' Exports TabManager. '''

import hexvi.events as events
from hexvi.app_state import SearchState
from hexvi.tab_state import TabState

class TabManager(object):
    ''' The class responsible for managing tab lifecycles. '''

    def __init__(self, app_state):
        self.tabs = []
        self._tab_idx = None
        self._app_state = app_state

    @property
    def current_tab(self):
        return None if self._tab_idx is None else self.tabs[self._tab_idx]

    def close_current_tab(self):
        ''' Closes currently focused tab. '''
        # TODO: check if the file was modified
        self._do_close_current_tab()

    def _do_close_current_tab(self):
        self.tabs = self.tabs[:self._tab_idx] + self.tabs[self._tab_idx+1:]
        if self._tab_idx >= len(self.tabs):
            self._tab_idx = len(self.tabs) - 1
        if not self.tabs:
            events.notify(events.ProgramExit())
        events.notify(events.TabChange(self.current_tab))

    def open_tab(self, path=None):
        ''' Opens a new tab and focuses it. '''
        if path:
            self.tabs.append(TabState(self._app_state, path))
        else:
            self.tabs.append(TabState(self._app_state))
        self._tab_idx = len(self.tabs) - 1
        events.notify(events.TabChange(self.current_tab))

    def cycle_tabs(self, direction):
        ''' Focuses next or previous tab. '''
        self._tab_idx += 1 if direction == SearchState.DIR_FORWARD else -1
        self._tab_idx %= len(self.tabs)
        events.notify(events.TabChange(self.current_tab))
