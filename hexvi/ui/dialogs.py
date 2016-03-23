''' A place for all the dialogs / pop-ups. '''

import urwid

class ConfirmationDialog(urwid.Overlay):
    ''' Creates a dialog that can be used to confirm things. '''

    def __init__(self, ui, message, confirm_action, cancel_action):
        message = ' %s ' % message
        ui.blocked = True
        self._ui = ui
        self._old_widget = ui.loop.widget
        self._confirm_action = confirm_action
        self._cancel_action = cancel_action

        column_items = []
        for label, action in (('Yes', self.confirm), ('No', self.cancel)):
            button = urwid.Button(
                label, on_press=self._button_clicked, user_data=action)
            column_items.append(urwid.Filler(
                urwid.AttrMap(button, 'button', 'button-focused')))

        widget = urwid.AttrMap(
            urwid.LineBox(
                urwid.Pile([
                    urwid.Filler(urwid.Text(message)),
                    urwid.Columns(column_items)
                ])),
            'window')

        width = len(message) + 2
        height = 5
        super().__init__(
            widget, ui.loop.widget, 'center', width, 'middle', height)

        self._ui.loop.widget = self

    def confirm(self):
        self._confirm_action()
        self.close()

    def cancel(self):
        self._cancel_action()
        self.close()

    def close(self):
        self._ui.blocked = False
        self._ui.loop.widget = self._old_widget

    def keypress(self, pos, key):
        if key in ['y', 'Y']:
            self.confirm()
        elif key in ['n', 'N', 'esc']:
            self.cancel()
        else:
            return super().keypress(pos, key)

    def _button_clicked(self, _, user_data):
        user_data()
