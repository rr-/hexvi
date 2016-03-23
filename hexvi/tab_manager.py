'''
Tab manager - responsible for managing tab lifecycles.
'''

import hexvi.events as events
from hexvi.tab_state import TabState

class TabManager(object):
    ''' The tab manager. '''

    def __init__(self, app_state):
        self.tabs = []
        self._current_tab = None
        self._app_state = app_state

    def get_current_tab(self):
        ''' Returns the currently focused file state. '''
        return self._current_tab

    def set_current_tab(self, value):
        ''' Sets the currently focused file state. '''
        if value != self._current_tab:
            self._current_tab = value
            events.notify(events.FileBufferChange(value))

    def open_tab(self, path=None):
        if path:
            self.tabs.append(TabState(self._app_state, path))
        else:
            self.tabs.append(TabState(self._app_state))
        self.current_tab = self.tabs[-1]

    current_tab = property(get_current_tab, set_current_tab)
