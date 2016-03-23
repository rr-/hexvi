''' Commands related to tab management '''

import hexvi.events as events
from hexvi.command_registry import BaseCommand

class QuitCommand(BaseCommand):
    ''' Quits the application. '''
    names = ['q', 'quit']

    def run(self, _args):
        events.notify(events.ProgramExit())

class TogglePaneCommand(BaseCommand):
    ''' Toggles the pane between hex and ascii dump. '''
    names = ['toggle_pane', 'toggle_panes']

    def run(self, args):
        cur_tab = self._app_state.current_tab
        if cur_tab.pane == cur_tab.PANE_HEX:
            cur_tab.pane = cur_tab.PANE_ASC
        else:
            cur_tab.pane = cur_tab.PANE_HEX

class SetPaneCommand(BaseCommand):
    ''' Sets the pane to either hex and ascii dump. '''
    names = ['set_pane', 'pane']

    def run(self, args):
        pane, = args
        cur_tab = self._app_state.current_tab
        if pane == 'hex':
            cur_tab.pane = cur_tab.PANE_HEX
        elif pane in ['ascii', 'asc']:
            cur_tab.pane = cur_tab.PANE_ASC
        else:
            raise RuntimeError('Bad pane (try with "hex" or "ascii")')
