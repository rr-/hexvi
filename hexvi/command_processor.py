import zope.event
import shlex
import re

class ProgramExitEvent(object):
    pass

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
        for x in dir(self):
            if x.startswith('cmd_'):
                self._commands.append(getattr(self, x))

    def exec(self, cmd_name, *args):
        for cmd in self._commands:
            if cmd_name in cmd.names:
                return cmd.func(self, *args)
        raise RuntimeError('Unknown command: ' + cmd_name)

    @cmd(names=['q', 'quit'])
    def cmd_exit(self):
        zope.event.notify(ProgramExitEvent())

    @cmd(names=['toggle_pane', 'toggle_panes'])
    def cmd_toggle_panes(self):
        panes = [
            self._app_state.cur_file.PANE_HEX,
            self._app_state.cur_file.PANE_ASC]
        self._app_state.cur_file.pane = (
            panes[self._app_state.cur_file.pane == panes[0]])

    @cmd(names=['jump_to'])
    def cmd_jump_to(self, offset):
        offset = int(offset, 16)
        self._app_state.cur_file.set_cur_offset(offset)

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
        self._app_state.cur_file.set_cur_offset(0)

    @cmd(names=['jump_to_end_of_file'])
    def cmd_jump_to_end_of_file(self):
        self._app_state.cur_file.set_cur_offset(self._app_state.cur_file.size)

    @cmd(names=['nmap'])
    def cmd_map_for_normal_mode(self, key_sequence_str, binding):
        key_sequence = re.findall('({[^}]*}|<[^>]*>|[^<>{}])', key_sequence_str)
        key_sequence = [re.sub('[{}<>]', '', x) for x in key_sequence]
        if not binding:
            raise RuntimeError('Empty binding')
        if binding[0] != ':':
            raise RuntimeError('Only command-based bindings are supported')
        self._app_state.normal_mode_mappings.add(
            key_sequence, lambda *args: self._exec_via_binding(binding, *args))

        self._app_state.normal_mode_mappings.compile()

    def _exec_via_binding(self, binding, *args_from_mapping):
        command, *args = shlex.split(binding[1:])
        for i in range(len(args)):
            args[i] = re.sub('{arg(\d)}', lambda m: args_from_mapping[int(m.groups()[0])], args[i])
        return self.exec(command, *args)
