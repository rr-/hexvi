import zope.event

class ProgramExitEvent(object):
    pass

class Command(object):
    def __init__(self, names, func):
        self.names = names
        self.func = func

def command(names):
    def decorator(func):
        return Command(names, func)
    return decorator

class CommandProcessor(object):
    def __init__(self, app_state):
        self._app_state = app_state
        self._commands = []
        for x in dir(self):
            if x.startswith('cmd_'):
                self._commands.append(getattr(self, x))

    @command(names=['q', 'quit'])
    def cmd_exit(self):
        zope.event.notify(ProgramExitEvent())

    def execute(self, command_name, *args):
        for command in self._commands:
            if command_name in command.names:
                return command.func(self, *args)
        raise RuntimeError('Unknown command: ' + command_name)
