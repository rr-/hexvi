import zope.event

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

    @cmd(names=['q', 'quit'])
    def cmd_exit(self):
        zope.event.notify(ProgramExitEvent())

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

    def exec(self, cmd_name, *args):
        for cmd in self._commands:
            if cmd_name in cmd.names:
                return cmd.func(self, *args)
        raise RuntimeError('Unknown command: ' + cmd_name)
