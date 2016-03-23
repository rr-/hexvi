''' Main UI facade '''

import urwid
import hexvi.events as events
from hexvi.app_state import AppState
from hexvi.ui.dialogs import ConfirmationDialog
from hexvi.ui.main_window import MainWindow

class Ui(object):
    ''' The main UI facade. '''

    def __init__(self, tab_manager, cmd_processor, app_state):
        self.blocked = False
        self._app_state = app_state
        self._main_window = MainWindow(
            app_state, cmd_processor, tab_manager, self)
        self._app_state.mode = AppState.MODE_NORMAL

        events.register_handler(events.ProgramExit, lambda *args: self._exit())
        events.register_handler(events.ColorChange, self._color_changed)

        # TODO: subscribe to changes of app_state.current_tab
        self._main_window.caption = 'hexvi'

        self.loop = urwid.MainLoop(
            self._main_window, unhandled_input=self._key_pressed)

    def show_confirmation_dialog(self, message, confirm_action, cancel_action):
        ConfirmationDialog(self, message, confirm_action, cancel_action)

    def run(self):
        self._main_window.started()
        self.loop.screen.set_terminal_properties(
            self._app_state.settings.term_colors)
        self.loop.run()

    def _color_changed(self, evt):
        scr = self.loop.screen
        scr.register_palette_entry(
            evt.target,
            evt.fg_style,
            evt.bg_style,
            foreground_high=evt.fg_style_high,
            background_high=evt.bg_style_high)
        scr.clear()

    @staticmethod
    def _exit():
        raise urwid.ExitMainLoop()

    def _key_pressed(self, key):
        if not self.blocked:
            self._app_state.mappings[self._app_state.mode].keypress(key)
