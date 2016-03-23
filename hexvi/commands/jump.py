''' Commands related to buffer movement '''

from hexvi.command_registry import BaseTabCommand

class JumpToCommand(BaseTabCommand):
    names = ['jump_to', 'jump', 'jumpto', 'goto', 'go_to', 'g']
    def run(self, args):
        offset = int(args[0], 16)
        self.current_tab.current_offset = offset

class JumpByBytesCommand(BaseTabCommand):
    names = ['jump_by_bytes']
    def run(self, args):
        offset = 1 if not args else int(args[0])
        self.current_tab.current_offset += offset

class JumpByLinesCommand(BaseTabCommand):
    names = ['jump_by_lines']
    def run(self, args):
        offset = 1 if not args else int(args[0])
        self.current_tab.current_offset += (
            offset * self.current_tab.visible_columns)

class JumpByPagesCommand(BaseTabCommand):
    names = ['jump_by_pages']
    def run(self, args):
        pages = 1 if not args else int(args[0])
        self.current_tab.current_offset += \
            pages \
                * self.current_tab.visible_rows \
                * self.current_tab.visible_columns

class JumpToFilePercentageCommand(BaseTabCommand):
    names = ['jump_to_percentage']
    def run(self, args):
        percentage = float(args[0])
        cur_offset = int(self.current_tab.size * percentage / 100.0)
        #while cur_offset % self.current_tab.visible_columns != 0:
        #    cur_offset -= 1
        self._app_state.current_tab.current_offset = cur_offset

class JumpToScreenTopCommand(BaseTabCommand):
    names = ['jump_to_screen_top']
    def run(self, _args):
        self.current_tab.current_offset = self.current_tab.top_offset

class JumpToScreenBottomCommand(BaseTabCommand):
    names = ['jump_to_screen_bottom']
    def run(self, _args):
        self.current_tab.current_offset = \
            self.current_tab.bottom_offset - self.current_tab.visible_columns

class JumpToScreenMiddleCommand(BaseTabCommand):
    names = ['jump_to_screen_middle']
    def run(self, _args):
        bot_off = self.current_tab.bottom_offset
        top_off = self.current_tab.top_offset
        new_off = top_off + (bot_off - top_off) // 2
        new_off -= new_off % self.current_tab.visible_columns
        self.current_tab.current_offset = new_off

class JumpToStartOfLineCommand(BaseTabCommand):
    names = ['jump_to_start_of_line']
    def run(self, _args):
        self.current_tab.current_offset -= (
            self.current_tab.current_offset %
            self.current_tab.visible_columns)

class JumpToEndOfLineCommand(BaseTabCommand):
    names = ['jump_to_end_of_line']
    def run(self, _args):
        self.current_tab.current_offset += \
            self.current_tab.visible_columns \
                - 1 \
                - self.current_tab.current_offset \
                    % self.current_tab.visible_columns

class JumpToStartOfFileCommand(BaseTabCommand):
    names = ['jump_to_start_of_file']
    def run(self, _args):
        self.current_tab.current_offset = 0

class JumpToEndOfFileCommand(BaseTabCommand):
    names = ['jump_to_end_of_file']
    def run(self, _args):
        self.current_tab.current_offset = self.current_tab.size
