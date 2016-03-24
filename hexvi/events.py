''' Definitions of events, and simple event handling / dispatching. '''

from collections import namedtuple

class _EventRegistry(object):
    ''' The container for registered event handlers. '''
    _registry = {}

    @staticmethod
    def get_handlers(event_class):
        return _EventRegistry._registry.get(event_class, ())

    @staticmethod
    def register(event_class, handler):
        if not event_class in _EventRegistry._registry:
            _EventRegistry._registry[event_class] = []
        _EventRegistry._registry[event_class].append(handler)

    @staticmethod
    def unregister(event_class, handler):
        try:
            _EventRegistry._registry[event_class].remove(handler)
        except IndexError:
            pass

def notify(event):
    ''' Dispatches an event to all registered handlers. '''
    for event_class in event.__class__.__mro__:
        for handler in _EventRegistry.get_handlers(event_class):
            handler(event)

def register_handler(event_class, handler):
    ''' Registers a handler that reacts to a given event. '''
    _EventRegistry.register(event_class, handler)

def unregister_handler(event_class, handler):
    ''' Stops dispatching given event to a given handler. '''
    _EventRegistry.unregister(event_class, handler)

PrintMessage = namedtuple('PrintMessage', ['message', 'style'])

ConfirmMessage = namedtuple('ConfirmMessage', ['message', 'confirm_action', 'cancel_action'])

ModeChange = namedtuple('ModeChange', ['mode'])

TabChange = namedtuple('TabChange', ['tab_state'])

WindowSizeChange = namedtuple('WindowSizeChange', ['size'])

OffsetChange = namedtuple('OffsetChange', ['tab_state'])

PaneChange = namedtuple('PaneChange', ['tab_state'])

ColorChange = namedtuple(
    'ColorChange',
    ['target', 'fg_style', 'bg_style', 'fg_style_high', 'bg_style_high'])

ProgramExit = namedtuple('ProgramExit', [])
