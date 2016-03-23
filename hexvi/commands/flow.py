''' Commands related to application workflow '''

import hexvi.events as events
from hexvi.command_registry import BaseCommand

class SetModeCommand(BaseCommand):
    ''' Changes current mode. '''
    names = ['mode', 'set_mode']
    def run(self, args):
        mode, = args
        self._app_state.set_mode(mode)

class EchoCommand(BaseCommand):
    ''' Prints a message near the command bar. '''
    names = ['echo']
    def run(self, args):
        message, = args[0]
        events.notify(events.PrintMessage(message, style='msg-info'))
