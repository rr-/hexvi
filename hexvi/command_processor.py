import os
import regex
import shlex
import urwid
import hexvi.events as events

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
    except urwid.ExitMainLoop:
      raise
    except Exception as ex:
      events.notify(events.PrintMessage(str(ex), style='msg-error'))

  @cmd(names=['q', 'quit'])
  def cmd_exit(self):
    events.notify(events.ProgramExit())

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
    self._map(key_sequence_str, binding, self._app_state.MODE_NORMAL)

  @cmd(names=['rmap'])
  def cmd_map_for_replace_mode(self, key_sequence_str, binding):
    self._map(key_sequence_str, binding, self._app_state.MODE_REPLACE)

  @cmd(names=['cmap'])
  def cmd_map_for_command_mode(self, key_sequence_str, binding):
    self._map(key_sequence_str, binding, self._app_state.MODE_COMMAND)
    self._map(key_sequence_str, binding, self._app_state.MODE_SEARCH_FORWARD)
    self._map(key_sequence_str, binding, self._app_state.MODE_SEARCH_BACKWARD)

  def _map(self, key_sequence_str, binding, mode):
    key_sequence = regex.findall('({[^}]*}|<[^>]*>|[^<>{}])', key_sequence_str)
    key_sequence = [regex.sub('[{}<>]', '', x) for x in key_sequence]
    if not binding:
      raise RuntimeError('Empty binding')
    if binding[0] != ':':
      raise RuntimeError('Only command-based bindings are supported')
    self._app_state.mappings[mode].add(
      key_sequence,
      lambda traversal: self._exec_via_binding(binding, traversal))

  @cmd(names=['jump_to_next_word'])
  def cmd_jump_to_next_word(self, repeat=1):
    for i in range(int(repeat)):
      pattern = self._choose_word_class(
        self._app_state.cur_file.file_buffer.get(
          self._app_state.cur_file.cur_offset, 1))
      self._scan(
        self._app_state.search_state.DIR_FORWARD,
        self._app_state.cur_file.cur_offset,
        1000,
        1000,
        lambda *args: self._forward_word_callback(pattern, *args))

  @cmd(names=['jump_to_prev_word'])
  def cmd_jump_to_prev_word(self, repeat=1):
    for i in range(int(repeat)):
      if self._app_state.cur_file.cur_offset == 0:
        return
      patterns = ['[a-zA-Z]', '[0-9]', '[^a-zA-Z0-9]']
      pattern = self._choose_word_class(
        self._app_state.cur_file.file_buffer.get(
          self._app_state.cur_file.cur_offset - 1, 1))
      self._scan(
        self._app_state.search_state.DIR_BACKWARD,
        self._app_state.cur_file.cur_offset,
        1000,
        1000,
        lambda *args: self._backward_word_callback(pattern, *args))

  def _forward_word_callback(self, pattern, buffer, start_pos, end_pos, dir):
    indices = range(len(buffer))
    if dir == self._app_state.search_state.DIR_BACKWARD:
      indices = reversed(indices)
    for i in indices:
      char_under_cursor = buffer[i:i+1]
      if not regex.match(pattern.encode('utf-8'), char_under_cursor):
        self._app_state.cur_file.cur_offset = start_pos + i
        return True
      if end_pos == self._app_state.cur_file.size:
        self._app_state.cur_file.cur_offset = self._app_state.cur_file.size
    return False

  def _backward_word_callback(self, pattern, buffer, start_pos, end_pos, dir):
    indices = reversed(range(len(buffer)))
    for i in indices:
      if i - 1 >= 0:
        char_under_cursor = buffer[i-1:i]
        if not regex.match(pattern.encode('utf-8'), char_under_cursor):
          self._app_state.cur_file.cur_offset = start_pos + i
          return True
      if start_pos == 0:
        self._app_state.cur_file.cur_offset = 0
    return False

  def _choose_word_class(self, char):
    patterns = ['[a-zA-Z]', '[0-9]', '[^a-zA-Z0-9]']
    chosen_pattern = None
    for pattern in patterns:
      if regex.match(pattern.encode('utf-8'), char):
        return pattern
    assert False

  @cmd(names=['search'])
  def cmd_search_forward(self, text='', repeat=1):
    repeat=int(repeat)
    for i in range(repeat):
      self._perform_user_search(self._app_state.search_state.DIR_FORWARD, text)

  @cmd(names=['rsearch'])
  def cmd_search_backward(self, text='', repeat=1):
    repeat=int(repeat)
    for i in range(repeat):
      self._perform_user_search(self._app_state.search_state.DIR_BACKWARD, text)

  @cmd(names=['so', 'source'])
  def cmd_source(self, path):
    for line in open(os.path.expanduser(path), 'r'):
      line = regex.sub('(?<!\\\)#.*$', '', line)
      line = regex.sub('\\\#', '#', line)
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
  def cmd_highlight(
      self, target, bg_style, fg_style, bg_style_high=None, fg_style_high=None):
    events.notify(events.ColorChange(
      target, bg_style, fg_style, bg_style_high, fg_style_high))

  @cmd(names=['echo'])
  def cmd_echo(self, message):
    events.notify(events.PrintMessage(message, style='msg-info'))

  @cmd(names=['set'])
  def cmd_manage_settings(self, key, value=None):
    if not hasattr(self._app_state.settings, key):
      raise RuntimeError('Option does not exist: ' + key)
    if not value:
      value = getattr(self._app_state.settings, key)
      events.notify(events.PrintMessage(
        '%s=%s' % (key, value), style='msg-info'))
    else:
      value_type = type(getattr(self._app_state.settings, key))
      setattr(self._app_state.settings, key, value_type(value))

  def _perform_user_search(self, dir, text):
    if not text:
      text = self._app_state.search_state.text
      dir = self._app_state.search_state.dir ^ dir ^ 1
    else:
      self._app_state.search_state.dir = dir
      self._app_state.search_state.text = text
    return self._perform_stateless_search(dir, text)

  def _perform_stateless_search(self, dir, pattern):
    if not pattern:
      raise RuntimeError('No text to search for')
    max_match_size = self._app_state.settings.max_match_size
    if dir == self._app_state.search_state.DIR_BACKWARD:
      start_pos = self._app_state.cur_file.cur_offset
      pattern = '(?r)' + pattern
    else:
      start_pos = self._app_state.cur_file.cur_offset + 1
    if not self._scan(
        dir,
        start_pos,
        max_match_size,
        max_match_size * 2,
        lambda *args: self._search_callback(pattern, *args)):
      # TODO: if an option is enabled, show info and wrap around
      raise RuntimeError('Not found')

  def _search_callback(self, pattern, buffer, start_pos, end_pos, dir):
    match = regex.search(pattern.encode('utf-8'), buffer)
    if match:
      self._app_state.cur_file.cur_offset = start_pos + match.span()[0]
      return True
    return False

  def _scan(self, dir, start_pos, buffer_size, jump_size, functor):
    try:
      cur_file = self._app_state.cur_file
      if dir == self._app_state.search_state.DIR_BACKWARD:
        end_pos = start_pos
        while end_pos > 0:
          start_pos = max(end_pos - buffer_size, 0)
          buffer = cur_file.file_buffer.get(start_pos, end_pos - start_pos)
          if functor(buffer, start_pos, end_pos, dir):
            return True
          end_pos -= jump_size
      elif dir == self._app_state.search_state.DIR_FORWARD:
        while start_pos < cur_file.size:
          buffer = cur_file.file_buffer.get(start_pos, buffer_size)
          end_pos = start_pos + len(buffer)
          if functor(buffer, start_pos, end_pos, dir):
            return True
          start_pos += jump_size
      else:
        assert False, 'Bad search direction'
    except (KeyboardInterrupt, SystemExit):
      raise RuntimeError('Aborted')
    return False

  def _exec_via_binding(self, binding, traversal):
    command, *args = shlex.split(binding[1:])
    for i in range(len(args)):
      args[i] = regex.sub(
        '\{arg(\d)\}', lambda m: traversal.args[int(m.groups()[0])], args[i])
    return self.exec(command, *args, traversal=traversal)
