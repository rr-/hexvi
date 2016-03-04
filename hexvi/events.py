class PrintMessageEvent(object):
  def __init__(self, message, style):
    self.message = message
    self.style = style

class FileBufferChangeEvent(object):
  def __init__(self, file_buffer):
    self.file_buffer = file_buffer

class ModeChangeEvent(object):
  def __init__(self, mode, traversal):
    self.traversal = traversal
    self.mode = mode

class WindowSizeChangeEvent(object):
  def __init__(self, size):
    self.size = size

class OffsetChangeEvent(object):
  def __init__(self, file_state):
    self.file_state = file_state

class PaneChangeEvent(object):
  def __init__(self, file_state):
    self.file_state = file_state

class ColorChangeEvent(object):
  def __init__(self, target, fg_style, bg_style, fg_style_high, bg_style_high):
    self.target = target
    self.bg_style = bg_style
    self.fg_style = fg_style
    self.bg_style_high = bg_style_high
    self.fg_style_high = fg_style_high

class ProgramExitEvent(object):
  pass
