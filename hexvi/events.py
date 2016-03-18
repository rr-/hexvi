registry = {}

def notify(event):
  for event_class in event.__class__.__mro__:
    for handler in registry.get(event_class, ()):
      handler(event)

def register_handler(event_class, handler):
  if not event_class in registry:
    registry[event_class] = []
  registry[event_class].append(handler)

def unregister_handler(event_class, handler):
  try:
    registry[event_class].remove(handler)
  except IndexError:
    pass

class Event(object):
  pass

class PrintMessage(Event):
  def __init__(self, message, style):
    self.message = message
    self.style = style

class FileBufferChange(Event):
  def __init__(self, file_buffer):
    self.file_buffer = file_buffer

class ModeChange(Event):
  def __init__(self, mode):
    self.mode = mode

class WindowSizeChange(Event):
  def __init__(self, size):
    self.size = size

class OffsetChange(Event):
  def __init__(self, file_state):
    self.file_state = file_state

class PaneChange(Event):
  def __init__(self, file_state):
    self.file_state = file_state

class ColorChange(Event):
  def __init__(self, target, fg_style, bg_style, fg_style_high, bg_style_high):
    self.target = target
    self.bg_style = bg_style
    self.fg_style = fg_style
    self.bg_style_high = bg_style_high
    self.fg_style_high = fg_style_high

class ProgramExit(Event):
  pass
