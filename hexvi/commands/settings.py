''' Commands related to runtime settings '''

import os
import shlex
import regex
import hexvi.events as events
from hexvi.command_registry import BaseCommand

class ManipulateUserSettingCommand(BaseCommand):
    names = ['set']
    def run(self, args):
        key = args[0]
        value = args[1] if len(args) > 1 else None

        if not hasattr(self._app_state.settings, key):
            raise RuntimeError('Option does not exist: ' + key)
        if not value:
            value = getattr(self._app_state.settings, key)
            events.notify(events.PrintMessage(
                '%s=%s' % (key, value), style='msg-info'))
        else:
            value_type = type(getattr(self._app_state.settings, key))
            setattr(self._app_state.settings, key, value_type(value))

class ManipulateColorSettingCommand(BaseCommand):
    names = ['hi', 'highlight']
    def run(self, args):
        target, bg_style, fg_style, bg_style_high, fg_style_high, *_ = \
            args + (None, None, None, None, None)

        events.notify(events.ColorChange(
            target, bg_style, fg_style, bg_style_high, fg_style_high))

class SourceFileCommand(BaseCommand):
    names = ['so', 'source']
    def run(self, args):
        for line in open(os.path.expanduser(args[0]), 'r'):
            line = regex.sub(r'(?<!\\)#.*$', '', line)
            line = regex.sub(r'\\#', '#', line)
            result = shlex.split(line)
            if result:
                command, *args = result
                self._command_processor.exec(command, *args)

class SourceThemeCommand(BaseCommand):
    names = ['colorscheme']
    def run(self, args):
        path, = args
        search_paths = [path, os.path.splitext(path)[0] + '.hexvi']
        for full_path in search_paths[:]:
            search_paths.append(
                os.path.join(self._app_state.resources_dir, 'themes', full_path))
        for full_path in search_paths:
            if os.path.exists(full_path):
                return self._command_processor.exec('source', full_path)
        raise RuntimeError(path + ' not found (looked in %r)' % search_paths)
