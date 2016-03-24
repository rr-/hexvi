''' Exports MainWindow. '''

import regex
import urwid
import hexvi.events as events
from hexvi.app_state import AppState
from hexvi.ui.console import Console
from hexvi.ui.dump import Dump
from hexvi.ui.misc import DumbPile
from hexvi.ui.status_bar import StatusBar

class MainWindow(urwid.Frame):
    ''' One top level widget to rule them all! '''

    def __init__(self, app_state, cmd_processor, tab_manager, ui):
        self._app_state = app_state

        self._ui = ui
        self._header = urwid.Text(u'hexvi')
        self._dump = Dump(app_state, cmd_processor, tab_manager.current_tab, ui)
        self._status_bar = StatusBar(app_state, tab_manager)
        self._console = Console(ui, cmd_processor, app_state)

        urwid.Frame.__init__(
            self,
            DumbPile([
                self._dump,
                ('fixed', 1, urwid.Filler(urwid.AttrMap(self._status_bar, 'status'))),
                ('fixed', 1, urwid.Filler(self._console)),
            ]),
            urwid.AttrMap(self._header, 'header'))

    def started(self):
        events.register_handler(events.PrintMessage, self._message_requested)
        events.register_handler(events.ConfirmMessage, self._confirm_requested)
        events.register_handler(events.ModeChange, self._mode_changed)

    def get_caption(self):
        return regex.sub('^hexvi( - )?', '', self._header.base_widget.get_text()[0])

    def set_caption(self, value):
        self._header.base_widget.set_text(
            'hexvi' if not value else 'hexvi - ' + value)

    def _message_requested(self, evt):
        self._console.prompt = (evt.style, evt.message)
        self._console.edit_text = ''

    def _confirm_requested(self, evt):
        self._ui.show_confirmation_dialog(
            evt.message, evt.confirm_action, evt.cancel_action)

    def _mode_changed(self, evt):
        self._console.edit_text = ''
        if evt.mode in AppState.NON_COMMAND_MODES:
            self._dump.editing = evt.mode in AppState.INPUT_MODES
            self._console.prompt = ''
            self.focus.set_focus(0)
        else:
            self._console.prompt = self._app_state.settings.mode_chars[evt.mode]
            self.focus.set_focus(2)

    caption = property(get_caption, set_caption)
