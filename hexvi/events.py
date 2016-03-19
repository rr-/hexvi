'''
Definitions of events, and simple event handling / dispatching.
'''

from collections import namedtuple

class EventRegistry(object):
    _registry = {}

    @staticmethod
    def get_handlers(event_class):
        return EventRegistry._registry.get(event_class, ())

    @staticmethod
    def register(event_class, handler):
        if not event_class in EventRegistry._registry:
            EventRegistry._registry[event_class] = []
        EventRegistry._registry[event_class].append(handler)

    @staticmethod
    def unregister(event_class, handler):
        try:
            EventRegistry._registry[event_class].remove(handler)
        except IndexError:
            pass

def notify(event):
    ''' Dispatches an event to all registered handlers. '''
    for event_class in event.__class__.__mro__:
        for handler in EventRegistry.get_handlers(event_class):
            handler(event)

def register_handler(event_class, handler):
    ''' Registers a handler that reacts to a given event. '''
    EventRegistry.register(event_class, handler)

def unregister_handler(event_class, handler):
    ''' Stops dispatching given event to a given handler. '''
    EventRegistry.unregister(event_class, handler)

PrintMessage = namedtuple('PrintMessage', ['message', 'style'])

ModeChange = namedtuple('ModeChange', ['mode'])

FileBufferChange = namedtuple('FileBufferChange', ['file_buffer'])

WindowSizeChange = namedtuple('WindowSizeChange', ['size'])

OffsetChange = namedtuple('OffsetChange', ['file_state'])

PaneChange = namedtuple('PaneChange', ['file_state'])

ColorChange = namedtuple(
    'ColorChange',
    ['target', 'fg_style', 'bg_style', 'fg_style_high', 'bg_style_high'])

ProgramExit = namedtuple('ProgramExit', [])
