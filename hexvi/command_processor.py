'''
Application state - the heart of all commands in hexvi.
TODO: this is growing too big. Make this modular.
'''

import os
import shlex
import regex
import urwid
import hexvi.events as events

class Command(object):
    def __init__(self, names, func):
        self.names = names
        self.func = func

def cmd(names):
    def decorator(func):
        return Command(names, func)
    return decorator

class CommandProcessor(object):
    def __init__(self, app_state):
        self._app_state = app_state
        self._commands = []
        for prop in dir(self):
            if prop.startswith('cmd_'):
                self._commands.append(getattr(self, prop))

    def exec_raw(self, command_text):
        for chunk in regex.split(r'(?<!\\)\|', command_text):
            command, *args = shlex.split(chunk)
            self.exec(command, *args)

    def exec(self, command_name, *args):
        try:
            for command in self._commands:
                if command_name in command.names:
                    return command.func(self, *args)
            raise RuntimeError('Unknown command: ' + command_name)
        except urwid.ExitMainLoop:
            raise
        except Exception as ex:
            events.notify(events.PrintMessage(str(ex), style='msg-error'))

    @cmd(names=['q', 'quit'])
    def cmd_exit(self):
        events.notify(events.ProgramExit())

    @cmd(names=['toggle_pane', 'toggle_panes'])
    def cmd_toggle_panes(self):
        cur_file = self._app_state.current_file
        if cur_file.pane == cur_file.PANE_HEX:
            cur_file.pane = cur_file.PANE_ASC
        else:
            cur_file.pane = cur_file.PANE_HEX

    @cmd(names=['set_pane', 'pane'])
    def cmd_set_pane(self, pane):
        cur_file = self._app_state.current_file
        if pane == 'hex':
            cur_file.pane = cur_file.PANE_HEX
        elif pane in ['ascii', 'asc']:
            cur_file.pane = cur_file.PANE_ASC
        else:
            raise RuntimeError('Bad pane (try with "hex" or "ascii")')

    @cmd(names=['jump_to', 'jump', 'jumpto', 'goto', 'go_to', 'g'])
    def cmd_jump_to(self, offset):
        offset = int(offset, 16)
        self._app_state.current_file.current_offset = offset

    @cmd(names=['jump_by_bytes'])
    def cmd_jump_by_bytes(self, offset='1'):
        offset = int(offset)
        self._app_state.current_file.current_offset += offset

    @cmd(names=['jump_by_lines'])
    def cmd_jump_by_lines(self, offset='1'):
        offset = int(offset)
        self._app_state.current_file.current_offset += (
            offset * self._app_state.current_file.visible_columns)

    @cmd(names=['jump_by_pages'])
    def cmd_jump_by_pages(self, pages='1'):
        pages = int(pages)
        self._app_state.current_file.current_offset += \
            pages \
                * self._app_state.current_file.visible_rows \
                * self._app_state.current_file.visible_columns

    @cmd(names=['jump_to_percentage'])
    def cmd_jump_to_percentage(self, percentage):
        percentage = float(percentage)
        cur_file = self._app_state.current_file
        cur_offset = int(current_file.size * percentage / 100.0)
        #while cur_offset % cur_file.visible_columns != 0:
        #    cur_offset -= 1
        cur_file.current_offset = cur_offset

    @cmd(names=['jump_to_screen_top'])
    def cmd_jump_to_screen_top(self):
        self._app_state.current_file.current_offset = self._app_state.current_file.top_offset

    @cmd(names=['jump_to_screen_bottom'])
    def cmd_jump_to_screen_bottom(self):
        self._app_state.current_file.current_offset = \
            self._app_state.current_file.bottom_offset \
                - self._app_state.current_file.visible_columns

    @cmd(names=['jump_to_screen_middle'])
    def cmd_jump_to_screen_middle(self):
        bot_off = self._app_state.current_file.bottom_offset
        top_off = self._app_state.current_file.top_offset
        self._app_state.current_file.current_offset = top_off + (bot_off - top_off) // 2

    @cmd(names=['jump_to_start_of_line'])
    def cmd_jump_to_start_of_line(self):
        self._app_state.current_file.current_offset -= (
            self._app_state.current_file.current_offset %
            self._app_state.current_file.visible_columns)

    @cmd(names=['jump_to_end_of_line'])
    def cmd_jump_to_end_of_line(self):
        self._app_state.current_file.current_offset += \
            self._app_state.current_file.visible_columns \
                - 1 \
                - self._app_state.current_file.current_offset \
                    % self._app_state.current_file.visible_columns

    @cmd(names=['jump_to_start_of_file'])
    def cmd_jump_to_start_of_file(self):
        self._app_state.current_file.current_offset = 0

    @cmd(names=['jump_to_end_of_file'])
    def cmd_jump_to_end_of_file(self):
        self._app_state.current_file.current_offset = self._app_state.current_file.size

    @cmd(names=['nmap'])
    def cmd_map_for_normal_mode(self, key_sequence_text, command_text):
        self._map(key_sequence_text, command_text, self._app_state.MODE_NORMAL)

    @cmd(names=['imap'])
    def cmd_map_for_insert_mode(self, key_sequence_text, command_text):
        self._map(key_sequence_text, command_text, self._app_state.MODE_INSERT)

    @cmd(names=['rmap'])
    def cmd_map_for_replace_mode(self, key_sequence_text, command_text):
        self._map(key_sequence_text, command_text, self._app_state.MODE_REPLACE)

    @cmd(names=['cmap'])
    def cmd_map_for_command_mode(self, key_sequence_text, command_text):
        for mode in self._app_state.COMMAND_MODES:
            self._map(key_sequence_text, command_text, mode)

    def _map(self, key_sequence_str, command_text, mode):
        key_sequence = regex.findall('({[^}]*}|<[^>]*>|[^<>{}])', key_sequence_str)
        key_sequence = [regex.sub('[{}<>]', '', x) for x in key_sequence]
        if not command_text:
            raise RuntimeError('Empty binding')
        self._app_state.mappings[mode].add(
            key_sequence,
            lambda traversal: self._exec_via_binding(command_text, traversal))

    @cmd(names=['jump_to_next_word'])
    def cmd_jump_to_next_word(self, repeat=1):
        for _ in range(int(repeat)):
            pattern = self._choose_word_class(
                self._app_state.current_file.file_buffer.get(
                    self._app_state.current_file.current_offset, 1))
            self._scan(
                self._app_state.search_state.DIR_FORWARD,
                self._app_state.current_file.current_offset,
                1000,
                1000,
                lambda buffer, start_pos, end_pos, direction: \
                    self._forward_word_callback(
                        pattern, buffer, start_pos, end_pos, direction))

    @cmd(names=['jump_to_prev_word'])
    def cmd_jump_to_prev_word(self, repeat=1):
        for _ in range(int(repeat)):
            if self._app_state.current_file.current_offset == 0:
                return
            pattern = self._choose_word_class(
                self._app_state.current_file.file_buffer.get(
                    self._app_state.current_file.current_offset - 1, 1))
            self._scan(
                self._app_state.search_state.DIR_BACKWARD,
                self._app_state.current_file.current_offset,
                1000,
                1000,
                lambda buffer, start_pos, end_pos, direction: \
                    self._backward_word_callback(pattern, buffer, start_pos))

    def _forward_word_callback(self, pattern, buffer, start_pos, end_pos, direction):
        indices = range(len(buffer))
        if direction == self._app_state.search_state.DIR_BACKWARD:
            indices = reversed(indices)
        for i in indices:
            char_under_cursor = buffer[i:i+1]
            if not regex.match(pattern.encode('utf-8'), char_under_cursor):
                self._app_state.current_file.current_offset = start_pos + i
                return True
            if end_pos == self._app_state.current_file.size:
                self._app_state.current_file.current_offset = self._app_state.current_file.size
        return False

    def _backward_word_callback(self, pattern, buffer, start_pos):
        indices = reversed(range(len(buffer)))
        for i in indices:
            if i - 1 >= 0:
                char_under_cursor = buffer[i-1:i]
                if not regex.match(pattern.encode('utf-8'), char_under_cursor):
                    self._app_state.current_file.current_offset = start_pos + i
                    return True
            if start_pos == 0:
                self._app_state.current_file.current_offset = 0
        return False

    def _choose_word_class(self, char):
        patterns = ['[a-zA-Z]', '[0-9]', '[^a-zA-Z0-9]']
        for pattern in patterns:
            if regex.match(pattern.encode('utf-8'), char):
                return pattern
        assert False

    @cmd(names=['delete'])
    def cmd_delete(self, movement_command, *args):
        old_offset = self._app_state.current_file.current_offset
        self.exec(movement_command, *args)
        new_offset = self._app_state.current_file.current_offset
        if old_offset < new_offset:
            offset = old_offset
            size = new_offset - old_offset
        else:
            offset = new_offset
            size = old_offset - new_offset
        self._app_state.current_file.file_buffer.delete(offset, size)
        self._app_state.current_file.current_offset = offset

    @cmd(names=['search'])
    def cmd_search_forward(self, text='', repeat=1):
        repeat = int(repeat)
        for _ in range(repeat):
            self._perform_user_search(self._app_state.search_state.DIR_FORWARD, text)

    @cmd(names=['rsearch'])
    def cmd_search_backward(self, text='', repeat=1):
        repeat = int(repeat)
        for _ in range(repeat):
            self._perform_user_search(self._app_state.search_state.DIR_BACKWARD, text)

    @cmd(names=['so', 'source'])
    def cmd_source(self, path):
        for line in open(os.path.expanduser(path), 'r'):
            line = regex.sub(r'(?<!\\)#.*$', '', line)
            line = regex.sub(r'\\#', '#', line)
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
                return self.exec('source', full_path)
        raise RuntimeError(path + ' not found (looked in %r)' % search_paths)

    @cmd(names=['mode'])
    def cmd_mode(self, mode):
        self._app_state.set_mode(mode)

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

    def _perform_user_search(self, direction, text):
        if not text:
            text = self._app_state.search_state.text
            direction = self._app_state.search_state.direction ^ direction ^ 1
        else:
            self._app_state.search_state.direction = direction
            self._app_state.search_state.text = text
        return self._perform_stateless_search(direction, text)

    def _perform_stateless_search(self, direction, pattern):
        if not pattern:
            raise RuntimeError('No text to search for')
        max_match_size = self._app_state.settings.max_match_size
        if direction == self._app_state.search_state.DIR_BACKWARD:
            start_pos = self._app_state.current_file.current_offset
            pattern = '(?r)' + pattern
        else:
            start_pos = self._app_state.current_file.current_offset + 1
        if not self._scan(
                direction,
                start_pos,
                max_match_size,
                max_match_size * 2,
                lambda buffer, start_pos, end_pos, direction: \
                    self._search_callback(pattern, buffer, start_pos)):
            # TODO: if an option is enabled, show info and wrap around
            raise RuntimeError('Not found')

    def _search_callback(self, pattern, buffer, start_pos):
        match = regex.search(pattern.encode('utf-8'), buffer)
        if match:
            self._app_state.current_file.current_offset = start_pos + match.span()[0]
            return True
        return False

    def _scan(self, direction, start_pos, buffer_size, jump_size, functor):
        try:
            cur_file = self._app_state.current_file
            if direction == self._app_state.search_state.DIR_BACKWARD:
                end_pos = start_pos
                while end_pos > 0:
                    start_pos = max(end_pos - buffer_size, 0)
                    buffer = cur_file.file_buffer.get(start_pos, end_pos - start_pos)
                    if functor(buffer, start_pos, end_pos, direction):
                        return True
                    end_pos -= jump_size
            elif direction == self._app_state.search_state.DIR_FORWARD:
                while start_pos < cur_file.size:
                    buffer = cur_file.file_buffer.get(
                        start_pos, min(buffer_size, cur_file.size - start_pos))
                    end_pos = start_pos + len(buffer)
                    if functor(buffer, start_pos, end_pos, direction):
                        return True
                    start_pos += jump_size
            else:
                assert False, 'Bad search direction'
        except (KeyboardInterrupt, SystemExit):
            raise RuntimeError('Aborted')
        return False

    def _exec_via_binding(self, command_text, traversal):
        for i in range(len(traversal.args)):
            command_text = regex.sub(
                r'\{arg\[%d\]\}' % i, traversal.args[i], command_text)
        command_text = regex.sub(r'\{arg\[(\d)\]\}', '', command_text)
        return self.exec_raw(command_text)
