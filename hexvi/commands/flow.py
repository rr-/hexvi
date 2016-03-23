''' Commands related to application workflow '''

import hexvi.events as events
from hexvi.command_registry import BaseCommand

class SetModeCommand(BaseCommand):
    ''' Changes current mode. '''
    names = ['mode', 'set_mode']
    def run(self, args):
        mode, = args
        self._app_state.set_mode(mode)

class QuitCommand(BaseCommand):
    ''' Quits the application. '''
    names = ['q', 'quit']

    def run(self, _args):
        events.notify(events.ProgramExit())

class TogglePaneCommand(BaseCommand):
    ''' Toggles the pane between hex and ascii dump. '''
    names = ['toggle_pane', 'toggle_panes']

    def run(self, args):
        if self._app_state.current_tab.pane == self._app_state.current_tab.PANE_HEX:
            self._app_state.current_tab.pane = self._app_state.current_tab.PANE_ASC
        else:
            self._app_state.current_tab.pane = self._app_state.current_tab.PANE_HEX

class SetPaneCommand(BaseCommand):
    ''' Sets the pane to either hex and ascii dump. '''
    names = ['set_pane', 'pane']

    def run(self, args):
        pane, = args
        if pane == 'hex':
            self._app_state.current_tab.pane = self._app_state.current_tab.PANE_HEX
        elif pane in ['ascii', 'asc']:
            self._app_state.current_tab.pane = self._app_state.current_tab.PANE_ASC
        else:
            raise RuntimeError('Bad pane (try with "hex" or "ascii")')

class EchoCommand(BaseCommand):
    ''' Prints a message near the command bar. '''
    names = ['echo']
    def run(self, args):
        message, = args[0]
        events.notify(events.PrintMessage(message, style='msg-info'))
