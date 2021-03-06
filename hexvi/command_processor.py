''' Exports CommandProcessor. '''

import shlex
import regex
import urwid
import hexvi.events as events
import hexvi.commands
from hexvi.command_registry import CommandRegistry
from hexvi.app_state import AppState

hexvi.commands.discover_commands()

def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except urwid.ExitMainLoop:
            raise
        except Exception as ex:
            events.notify(events.PrintMessage(str(ex), style='msg-error'))
    return wrapper

class CommandProcessor(object):
    '''
    Command processor - the thing that executes all the commands in hexvi.
    '''

    def __init__(self, app_state, tab_manager):
        self._tab_manager = tab_manager
        self._app_state = app_state
        self._commands = CommandRegistry.create_commands(
            app_state, self, tab_manager)

    @handle_errors
    def accept_raw_command_input(self, text):
        ''' Fired when the user runs a command in the UI command bar. '''
        mode = self._app_state.mode
        self._app_state.mode = AppState.MODE_NORMAL
        if mode == AppState.MODE_COMMAND:
            self.exec_raw(text)
        elif mode == AppState.MODE_SEARCH_FORWARD:
            self.exec('search', text)
        elif mode == AppState.MODE_SEARCH_BACKWARD:
            self.exec('rsearch', text)
        else:
            raise NotImplementedError(text)

    @handle_errors
    def accept_raw_byte_input(self, byte):
        ''' Fired when the user enters a byte in either HEX or ASCII dump. '''
        current_tab = self._tab_manager.current_tab
        if self._app_state.mode == AppState.MODE_REPLACE:
            current_tab.file_buffer.replace(
                current_tab.current_offset, bytes([byte]))
            current_tab.current_offset += 1
        elif self._app_state.mode == AppState.MODE_INSERT:
            current_tab.file_buffer.insert(
                current_tab.current_offset, bytes([byte]))
            current_tab.current_offset += 1
        else:
            raise NotImplementedError()

    @handle_errors
    def exec_raw(self, command_text):
        for chunk in regex.split(r'(?<!\\)\|', command_text):
            try:
                command, *args = shlex.split(chunk)
            except ValueError:
                raise RuntimeError('Malformed command')
            self.exec(command, *args)

    @handle_errors
    def exec(self, command_name, *args):
            for command in self._commands:
                if command_name in command.names:
                    return command.run(args)
            raise RuntimeError('Unknown command: ' + command_name)
