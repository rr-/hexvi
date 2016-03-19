''' Commands related to buffer movement '''

from hexvi.command_registry import BaseCommand

class JumpToCommand(BaseCommand):
    names = ['jump_to', 'jump', 'jumpto', 'goto', 'go_to', 'g']
    def run(self, args):
        offset = int(args[0], 16)
        self._app_state.current_file.current_offset = offset

class JumpByBytesCommand(BaseCommand):
    names = ['jump_by_bytes']
    def run(self, args):
        offset = 1 if not args else int(args[0])
        self._app_state.current_file.current_offset += offset

class JumpByLinesCommand(BaseCommand):
    names = ['jump_by_lines']
    def run(self, args):
        offset = 1 if not args else int(args[0])
        self._app_state.current_file.current_offset += (
            offset * self._app_state.current_file.visible_columns)

class JumpByPagesCommand(BaseCommand):
    names = ['jump_by_pages']
    def run(self, args):
        pages = 1 if not args else int(args[0])
        self._app_state.current_file.current_offset += \
            pages \
                * self._app_state.current_file.visible_rows \
                * self._app_state.current_file.visible_columns

class JumpToFilePercentageCommand(BaseCommand):
    names = ['jump_to_percentage']
    def run(self, args):
        percentage = float(args[0])
        cur_file = self._app_state.current_file
        cur_offset = int(cur_file.size * percentage / 100.0)
        #while cur_offset % cur_file.visible_columns != 0:
        #    cur_offset -= 1
        cur_file.current_offset = cur_offset

class JumpToScreenTopCommand(BaseCommand):
    names = ['jump_to_screen_top']
    def run(self, _args):
        self._app_state.current_file.current_offset = \
            self._app_state.current_file.top_offset

class JumpToScreenBottomCommand(BaseCommand):
    names = ['jump_to_screen_bottom']
    def run(self, _args):
        self._app_state.current_file.current_offset = \
            self._app_state.current_file.bottom_offset \
                - self._app_state.current_file.visible_columns

class JumpToScreenMiddleCommand(BaseCommand):
    names = ['jump_to_screen_middle']
    def run(self, _args):
        bot_off = self._app_state.current_file.bottom_offset
        top_off = self._app_state.current_file.top_offset
        new_off = top_off + (bot_off - top_off) // 2
        new_off -= new_off % self._app_state.current_file.visible_columns
        self._app_state.current_file.current_offset = new_off

class JumpToStartOfLineCommand(BaseCommand):
    names = ['jump_to_start_of_line']
    def run(self, _args):
        self._app_state.current_file.current_offset -= (
            self._app_state.current_file.current_offset %
            self._app_state.current_file.visible_columns)

class JumpToEndOfLineCommand(BaseCommand):
    names = ['jump_to_end_of_line']
    def run(self, _args):
        self._app_state.current_file.current_offset += \
            self._app_state.current_file.visible_columns \
                - 1 \
                - self._app_state.current_file.current_offset \
                    % self._app_state.current_file.visible_columns

class JumpToStartOfFileCommand(BaseCommand):
    names = ['jump_to_start_of_file']
    def run(self, _args):
        self._app_state.current_file.current_offset = 0

class JumpToEndOfFileCommand(BaseCommand):
    names = ['jump_to_end_of_file']
    def run(self, _args):
        self._app_state.current_file.current_offset = \
            self._app_state.current_file.size
