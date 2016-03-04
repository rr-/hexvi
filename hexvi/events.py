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
