''' Commands related to tab management '''

from hexvi.app_state import SearchState
from hexvi.command_registry import BaseCommand, BaseTabCommand

class OpenTabCommand(BaseTabCommand):
    ''' Opens a new tab. '''
    names = ['tabe', 'tabedit', 'tabnew']

    def run(self, args):
        self._tab_manager.open_tab()

class PrevTabCommand(BaseTabCommand):
    ''' Navigates to the previous tab. '''
    names = ['tabp', 'tabprev']

    def run(self, args):
        self._tab_manager.cycle_tabs(SearchState.DIR_BACKWARD)

class NextTabCommand(BaseTabCommand):
    ''' Navigates to the next tab. '''
    names = ['tabn', 'tabnext']

    def run(self, args):
        self._tab_manager.cycle_tabs(SearchState.DIR_FORWARD)

class CloseActiveTabCommand(BaseCommand):
    ''' Close active tab. '''
    names = ['q', 'quit']

    def run(self, _args):
        self._tab_manager.close_current_tab()

class TogglePaneCommand(BaseTabCommand):
    ''' Toggles the pane between hex and ascii dump. '''
    names = ['toggle_pane', 'toggle_panes']

    def run(self, args):
        if self.current_tab.pane == self.current_tab.PANE_HEX:
            self.current_tab.pane = self.current_tab.PANE_ASC
        else:
            self.current_tab.pane = self.current_tab.PANE_HEX

class SetPaneCommand(BaseTabCommand):
    ''' Sets the pane to either hex and ascii dump. '''
    names = ['set_pane', 'pane']

    def run(self, args):
        pane, = args
        if pane == 'hex':
            self.current_tab.pane = self.current_tab.PANE_HEX
        elif pane in ['ascii', 'asc']:
            self.current_tab.pane = self.current_tab.PANE_ASC
        else:
            raise RuntimeError('Bad pane (try with "hex" or "ascii")')
