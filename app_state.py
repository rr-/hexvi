from file_buffer import FileBuffer

class AppState(object):
    MODE_NORMAL = 'normal'
    MODE_COMMAND = 'command'

    def __init__(self, args):
        self.file_buffer = FileBuffer(args.file)
        self.mode = AppState.MODE_COMMAND
