'''
Command registry, where all commands are registered in.
'''

class CommandRegistry(object):
    ''' The container for all commands. '''
    _registry = []

    @staticmethod
    def register(command_type):
        ''' Registers a new command type. '''
        CommandRegistry._registry.append(command_type)

    @staticmethod
    def create_commands(app_state, command_processor, tab_manager):
        ''' Instantiates all registered commands. '''
        return [command_type(app_state, command_processor, tab_manager) \
            for command_type in CommandRegistry._registry]

class BaseCommandMeta(type):
    '''
    Meta class for the BaseCommand that autoregisters the command in the
    registry.
    '''
    def __init__(cls, name, bases, properties):
        super().__init__(name, bases, properties)
        if name != 'BaseCommand':
            CommandRegistry.register(cls)

class BaseCommand(metaclass=BaseCommandMeta):
    '''
    Base command that all commands are supposed to derive from.
    Automatically registers given command in the registry.
    '''

    names = []

    def __init__(self, app_state, command_processor, tab_manager):
        self._app_state = app_state
        self._command_processor = command_processor
        self._tab_manager = tab_manager

    def run(self, args):
        ''' Executes the command. Parameters can be anything. '''
        raise NotImplementedError('...')

class BaseTabCommand(BaseCommand):
    ''' Offers a few utilities regarding tab management. '''
    @property
    def current_tab(self):
        return self._tab_manager.current_tab

    def run(self, args):
        raise NotImplementedError('...')
