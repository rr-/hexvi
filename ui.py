import sys

try:
    import urwid
except ImportError as e:
    if e.name is None:
        raise
    print('Please install %s.' % e.name)
    sys.exit(1)

from file_buffer import FileBuffer
from readline_edit import ReadlineEdit

class MainWindow(urwid.Frame):
    def __init__(self, file_buffer):
        self._file_buffer = file_buffer
        self._columns = 8 # todo: autodetect
        self._offsets = self._make_offsets()
        self._hex_dump = self._make_hex_dump()
        self._ascii_dump = self._make_ascii_dump()
        self._console = self._make_console()
        self._header = self._make_header()

        urwid.Frame.__init__(
            self,
            urwid.Pile([
                urwid.Columns([
                    ('fixed', 8, urwid.Frame(self._offsets, urwid.Text('Offset'))),
                    ('fixed', 1, urwid.AttrMap(urwid.SolidFill(), 'filler')),
                    # todo: scaling
                    ('weight', 2, urwid.Frame(self._hex_dump, urwid.Text('Hex dump'))),
                    ('fixed', 1, urwid.AttrMap(urwid.SolidFill(), 'filler')),
                    ('weight', 1, urwid.Frame(self._ascii_dump, urwid.Text('ASCII dump'))),
                ]),
                ('fixed', 1, urwid.AttrMap(urwid.SolidFill(), 'header')),
                ('fixed', 1, urwid.Filler(self._console)),
            ]),
            urwid.AttrMap(self._header, 'header'))

        # focus the command line
        self.focus.set_focus(2)

    def get_caption(self):
        return self._header.text.replace('hexvi', '').replace(' - ', '')
    def set_caption(self, value):
        if not value:
            self._header.text = 'hexvi'
        else:
            self._header.text = 'hexvi - ' + value
    caption = property(get_caption, set_caption)

    def get_columns(self):
        return self._columns
    def set_columns(self, value):
        self._columns = value
    columns = property(get_columns, set_columns)

    def _make_offsets(self):
        # implement me
        body = [urwid.Text('%08x' % i) for i in range(0, 100 * self.columns, self.columns)]
        return urwid.ListBox(urwid.SimpleFocusListWalker(body))

    def _make_header(self):
        return urwid.Text(u'hexvi')

    def _make_hex_dump(self):
        # implement me
        body = [urwid.Text('TE ST ' * self.columns)]*100
        return urwid.ListBox(urwid.SimpleFocusListWalker(body))

    def _make_ascii_dump(self):
        # implement me
        body = [urwid.Text('test' * self.columns)]*100
        return urwid.ListBox(urwid.SimpleFocusListWalker(body))

    def _make_console(self):
        return ReadlineEdit()

class Ui(object):
    def run(self, args):
        file_buffer = FileBuffer(args.file)
        main_window = MainWindow(file_buffer)
        main_window.caption = 'bla'
        urwid.MainLoop(
            main_window,
            palette=[
                ('selected', 'light red', ''),
                ('header', 'standout', ''),
            ],
            unhandled_input=self._key_pressed).run()

    def _key_pressed(self, key):
        if key == 'ctrl q':
            raise urwid.ExitMainLoop()
