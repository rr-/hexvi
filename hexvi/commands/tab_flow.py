''' Commands related to tab management '''

import hexvi.events as events
from hexvi.command_registry import BaseTabCommand

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
