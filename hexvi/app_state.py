import os
import shlex
import zope.event
from .file_state import FileState
from .events import WindowSizeChangeEvent
from .events import ModeChangeEvent
from .mappings import MappingCollection
from .command_processor import CommandProcessor

class SearchState(object):
  DIR_BACKWARD = 0
  DIR_FORWARD = 1
  def __init__(self):
    self.dir = self.DIR_FORWARD
    self.text = None

class AppState(object):
  MODE_NORMAL = 'normal'
  MODE_COMMAND = 'command'
  MODE_SEARCH_FORWARD = 'search'
  MODE_SEARCH_BACKWARD = 'rsearch'

  ALL_MODES = [
    MODE_NORMAL,
    MODE_COMMAND,
    MODE_SEARCH_FORWARD,
    MODE_SEARCH_BACKWARD]

  def __init__(self, args):
    self._window_size = (0, 0)
    self._mode = AppState.MODE_COMMAND
    self._command_processor = CommandProcessor(self)

    # todo: manage this once we get multiple files support
    self._cur_file = FileState(args.file)

    self.search_state = SearchState()
    self.normal_mode_mappings = MappingCollection()
    self._command_processor.exec(
      'source', os.path.join(os.path.dirname(__file__), 'share', 'hexvirc'))

  def accept_raw_input(self, text):
    mode = self.mode
    self.mode = AppState.MODE_NORMAL
    if mode == self.MODE_COMMAND:
      command, *args = shlex.split(text)
      self._command_processor.exec(command, *args)
    elif mode == self.MODE_SEARCH_FORWARD:
      self._command_processor.exec('search', text)
    elif mode == self.MODE_SEARCH_BACKWARD:
      self._command_processor.exec('rsearch', text)
    else:
      raise NotImplementedError(text)

  def get_window_size(self):
    return self._window_size

  def set_window_size(self, value):
    if value != self._window_size:
      self._window_size = value
      zope.event.notify(WindowSizeChangeEvent(value))

  def get_cur_file(self):
    return self._cur_file

  def set_cur_file(self, value):
    if value != self._cur_file:
      self._cur_file = value
      zope.event.notify(FileBufferChangeEvent(value))

  def get_mode(self):
    return self._mode

  def set_mode(self, value, traversal=None):
    if value != self._mode:
      self._mode = value
      zope.event.notify(ModeChangeEvent(value, traversal))

  cur_file = property(get_cur_file)
  mode = property(get_mode, set_mode)
  window_size = property(get_window_size, set_window_size)
