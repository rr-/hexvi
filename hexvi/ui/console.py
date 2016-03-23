''' The console widget. '''

from hexvi.app_state import AppState
from hexvi.ui.readline_edit import ReadlineEdit

class Console(ReadlineEdit):
    ''' The widget where the user inputs command / search stuff. '''

    def __init__(self, ui, cmd_processor, app_state, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ui = ui
        self._cmd_processor = cmd_processor
        self._app_state = app_state

    def keypress(self, pos, key):
        if self._ui.blocked:
            return None
        if key == 'backspace' and not self.edit_text:
            self._app_state.mode = AppState.MODE_NORMAL
            return None
        if key == 'enter':
            self._cmd_processor.accept_raw_command_input(self.edit_text)
        return super().keypress(pos, key)

    def get_prompt(self):
        return self.caption

    def set_prompt(self, value):
        self.set_caption(value)

    prompt = property(get_prompt, set_prompt)
