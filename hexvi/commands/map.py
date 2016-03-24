''' Commands related to keyboard mappings '''

import regex
from hexvi.app_state import AppState
from hexvi.command_registry import BaseCommand

class _BaseMapCommand(BaseCommand):
    def _exec_via_binding(self, command_text, traversal):
        for i in range(len(traversal.args)):
            command_text = regex.sub(
                r'\{arg\[%d\]\}' % i, traversal.args[i], command_text)
        command_text = regex.sub(r'\{arg\[(\d)\]\}', '', command_text)
        return self._command_processor.exec_raw(command_text)

    def _map(self, key_sequence_str, command_text, mode):
        key_sequence = regex.findall('({[^}]*}|<[^>]*>|[^<>{}])', key_sequence_str)
        key_sequence = [regex.sub('[{}<>]', '', x) for x in key_sequence]
        if not command_text:
            raise RuntimeError('Empty binding')
        self._app_state.mappings[mode].add(
            key_sequence,
            lambda traversal: self._exec_via_binding(command_text, traversal))

    def run(self, args):
        raise NotImplementedError()

class NormalModeMapCommand(_BaseMapCommand):
    names = ['nmap']
    def run(self, args):
        key_sequence_text, command_text = args
        self._map(key_sequence_text, command_text, AppState.MODE_NORMAL)

class InsertModeMapCommand(_BaseMapCommand):
    names = ['imap']
    def run(self, args):
        key_sequence_text, command_text = args
        self._map(key_sequence_text, command_text, AppState.MODE_INSERT)

class ReplaceModeMapCommand(_BaseMapCommand):
    names = ['rmap']
    def run(self, args):
        key_sequence_text, command_text = args
        self._map(key_sequence_text, command_text, AppState.MODE_REPLACE)

class CommandModeMapCommand(_BaseMapCommand):
    names = ['cmap']
    def run(self, args):
        key_sequence_text, command_text = args
        for mode in AppState.COMMAND_MODES:
            self._map(key_sequence_text, command_text, mode)
