''' Commands related to content removal '''

from hexvi.command_registry import BaseTabCommand

class DeleteCommand(BaseTabCommand):
    ''' Deletes text content using a movement command from arguments. '''
    names = ['delete']

    def run(self, args):
        movement_command, *other_args = args
        old_offset = self.current_tab.current_offset
        self._command_processor.exec(movement_command, *other_args)
        new_offset = self.current_tab.current_offset
        if old_offset < new_offset:
            offset = old_offset
            size = new_offset - old_offset
        else:
            offset = new_offset
            size = old_offset - new_offset
        self.current_tab.file_buffer.delete(offset, size)
        self.current_tab.current_offset = offset
