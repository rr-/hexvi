from typing import Type, TypeVar, Dict, Callable, List, cast, Any


class Event:
    pass


T = TypeVar('T', bound='Event')
_handlers = {}  # type: Dict[Event, List[Callable[[Event], None]]]


def add_event_listener(
        event_type: Type[T], handler: Callable[[T], None]) -> None:
    if event_type not in _handlers:
        _handlers[cast(Event, event_type)] = []
    _handlers[cast(Event, event_type)].append(cast(Any, handler))


def remove_event_listener(
        event_type: Type[T], handler: Callable[[T], None]) -> None:
    if event_type in _handlers:
        _handlers[cast(Event, event_type)].remove(cast(Any, handler))


def emit_event(event: T) -> None:
    for handler in cast(Any, _handlers.get(cast(Event, type(event)), [])):
        handler(event)
