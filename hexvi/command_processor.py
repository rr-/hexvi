import os
import regex
import shlex
import zope.event
from .events import ColorChangeEvent
from .events import PrintMessageEvent
from .events import ProgramExitEvent

class Command(object):
  def __init__(self, names, func, use_traversal):
    self.names = names
    self.func = func
    self.use_traversal = use_traversal

def cmd(names, use_traversal=False):
  def decorator(func):
    return Command(names, func, use_traversal)
  return decorator

class CommandProcessor(object):
  def __init__(self, app_state):
    self._app_state = app_state
    self._commands = []
    for x in dir(self):
      if x.startswith('cmd_'):
        self._commands.append(getattr(self, x))

  def exec(self, cmd_name, *args, traversal=None):
    try:
      for cmd in self._commands:
        if cmd_name in cmd.names:
          if cmd.use_traversal:
            return cmd.func(self, *args, traversal=traversal)
          else:
            return cmd.func(self, *args)
      raise RuntimeError('Unknown command: ' + cmd_name)
    except RuntimeError as ex:
      zope.event.notify(PrintMessageEvent(str(ex)))

  @cmd(names=['q', 'quit'])
  def cmd_exit(self):
    zope.event.notify(ProgramExitEvent())

  @cmd(names=['toggle_pane', 'toggle_panes'])
  def cmd_toggle_panes(self):
    if self._app_state.cur_file.pane == self._app_state.cur_file.PANE_HEX:
      self._app_state.cur_file.pane = self._app_state.cur_file.PANE_ASC
    else:
      self._app_state.cur_file.pane = self._app_state.cur_file.PANE_HEX

  @cmd(names=['set_pane'])
  def cmd_set_pane(self, pane):
    if pane == 'hex':
      self._app_state.cur_file.pane = self._app_state.cur_file.PANE_HEX
    elif pane in ['ascii', 'asc']:
      self._app_state.cur_file.pane = self._app_state.cur_file.PANE_ASC
    else:
      raise RuntimeError('Bad pane (try with "hex" or "ascii")')

  @cmd(names=['jump_to'])
  def cmd_jump_to(self, offset):
    offset = int(offset, 16)
    self._app_state.cur_file.cur_offset = offset

  @cmd(names=['jump_by_bytes'])
  def cmd_jump_by_bytes(self, offset='1'):
    offset = int(offset)
    self._app_state.cur_file.cur_offset += offset

  @cmd(names=['jump_by_lines'])
  def cmd_jump_by_lines(self, offset='1'):
    offset = int(offset)
    self._app_state.cur_file.cur_offset += (
      offset * self._app_state.cur_file.visible_columns)

  @cmd(names=['jump_to_start_of_line'])
  def cmd_jump_to_start_of_line(self):
    self._app_state.cur_file.cur_offset -= (
      self._app_state.cur_file.cur_offset %
      self._app_state.cur_file.visible_columns)

  @cmd(names=['jump_to_end_of_line'])
  def cmd_jump_to_end_of_line(self):
    self._app_state.cur_file.cur_offset += (
      self._app_state.cur_file.visible_columns
      - 1
      - self._app_state.cur_file.cur_offset
        % self._app_state.cur_file.visible_columns)

  @cmd(names=['jump_to_start_of_file'])
  def cmd_jump_to_start_of_file(self):
    self._app_state.cur_file.cur_offset = 0

  @cmd(names=['jump_to_end_of_file'])
  def cmd_jump_to_end_of_file(self):
    self._app_state.cur_file.cur_offset = self._app_state.cur_file.size

  @cmd(names=['nmap'])
  def cmd_map_for_normal_mode(self, key_sequence_str, binding):
    key_sequence = regex.findall('({[^}]*}|<[^>]*>|[^<>{}])', key_sequence_str)
    key_sequence = [regex.sub('[{}<>]', '', x) for x in key_sequence]
    if not binding:
      raise RuntimeError('Empty binding')
    if binding[0] != ':':
      raise RuntimeError('Only command-based bindings are supported')
    self._app_state.normal_mode_mappings.add(
      key_sequence,
      lambda traversal: self._exec_via_binding(binding, traversal))
    self._app_state.normal_mode_mappings.compile()

  @cmd(names=['search'])
  def cmd_search_forward(self, text='', repeat=1):
    repeat=int(repeat)
    for i in range(repeat):
      self._perform_search(self._app_state.search_state.DIR_FORWARD, text)

  @cmd(names=['rsearch'])
  def cmd_search_backward(self, text='', repeat=1):
    repeat=int(repeat)
    for i in range(repeat):
      self._perform_search(self._app_state.search_state.DIR_BACKWARD, text)

  @cmd(names=['so', 'source'])
  def cmd_source(self, path):
    for line in open(path, 'r'):
      line = regex.sub('(?<!\\\)#.*$', '', line)
      result = shlex.split(line)
      if result:
        command, *args = result
        self.exec(command, *args)

  @cmd(names=['colorscheme'])
  def cmd_colorscheme(self, path):
    search_paths = [path, os.path.splitext(path)[0]+'.hexvi']
    for full_path in search_paths[:]:
      search_paths.append(
        os.path.join(self._app_state.resources_dir, 'themes', full_path))
    for full_path in search_paths:
      if os.path.exists(full_path):
        return self.cmd_source.func(self, full_path)
    raise RuntimeError(path + ' not found (looked in %r)' % search_paths)

  @cmd(names=['mode'], use_traversal=True)
  def cmd_mode(self, mode, traversal):
    self._app_state.set_mode(mode, traversal)

  @cmd(names=['hi', 'highlight'])
  def cmd_highlight(self, target, bg_style, fg_style):
    zope.event.notify(ColorChangeEvent(target, bg_style, fg_style))

  def _perform_search(self, dir, text):
    if not text:
      text = self._app_state.search_state.text
      dir = self._app_state.search_state.dir ^ dir ^ 1
    else:
      self._app_state.search_state.dir = dir
      self._app_state.search_state.text = text
    if not text:
      raise RuntimeError('No text to search for')

    if dir == self._app_state.search_state.DIR_BACKWARD:
      match = regex.search(
        b'(?r)' + text.encode('utf-8'),
        self._app_state.cur_file.file_buffer.get_content(),
        endpos=self._app_state.cur_file.cur_offset)
    elif dir == self._app_state.search_state.DIR_FORWARD:
      match = regex.search(
        text.encode('utf-8'),
        self._app_state.cur_file.file_buffer.get_content(),
        pos=self._app_state.cur_file.cur_offset + 1)
    else:
      assert False, 'Bad search direction'

    if not match:
      #todo: if an option is enabled, show info and wrap around
      raise RuntimeError('Not found')
    self._app_state.cur_file.cur_offset = match.span()[0]

  def _exec_via_binding(self, binding, traversal):
    command, *args = shlex.split(binding[1:])
    for i in range(len(args)):
      args[i] = regex.sub(
        '\{arg(\d)\}', lambda m: traversal.args[int(m.groups()[0])], args[i])
    return self.exec(command, *args, traversal=traversal)
