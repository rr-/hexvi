import sys
import re
from .command_processor import ProgramExitEvent
from .app_state import AppState, WindowSizeChangeEvent, ModeChangeEvent
from .file_state import PaneChangeEvent, OffsetChangeEvent
from .readline_edit import ReadlineEdit

try:
  import urwid
  import zope.event.classhandler
except ImportError as e:
  if e.name is None:
    raise
  print('Please install %s.' % e.name)
  sys.exit(1)

def trim_left(text, size):
  ellipsis = '(...)'
  if len(text) <= size:
    return text
  return ellipsis + text[len(ellipsis)+len(text)-size:]

def is_ascii(c):
  return c >= 32 and c < 127

def format_ascii(c):
  return '%c' % c if is_ascii(c) else '.'

class Dump(urwid.BoxWidget):
  def __init__(self, app_state, file_state):
    self._app_state = app_state
    self._file_state = file_state
    zope.event.classhandler.handler(
      PaneChangeEvent, lambda *args: self._invalidate())
    zope.event.classhandler.handler(
      OffsetChangeEvent, lambda *args: self._invalidate())

  def render(self, size, focus=False):
    self._app_state.window_size = size
    width, height = size
    vis_columns = self._file_state.visible_columns

    off_lines = []
    hex_lines = []
    asc_lines = []
    for i in range(height):
      row_offset = self._file_state.top_offset + i * vis_columns
      buffer = self._file_state.file_buffer.get_content_range(
        row_offset, vis_columns)
      off_lines.append(
        '%08x' % row_offset if row_offset - 1 < self._file_state.size else '')
      hex_lines.append(''.join('%02x ' % c for c in buffer))
      asc_lines.append(''.join(format_ascii(c) for c in buffer))

    off_lines = [l.encode('utf-8') for l in off_lines]
    hex_lines = [(l + ' ').encode('utf-8') for l in hex_lines]
    asc_lines = [(l + ' ').encode('utf-8') for l in asc_lines]

    rel_cur_offset = self._file_state.cur_offset - self._file_state.top_offset
    cursor_pos = (rel_cur_offset % vis_columns, rel_cur_offset // vis_columns)
    if self._file_state.pane == self._file_state.PANE_HEX:
      cursor_pos = (cursor_pos[0] * 3, cursor_pos[1])

    canvas_def = []
    Dump.pos = 0
    def append(widget, width, is_focused):
      canvas_def.append((widget, Dump.pos, False, width))
      Dump.pos += width
    append(urwid.TextCanvas(off_lines), 9, False)
    append(urwid.TextCanvas(hex_lines), vis_columns * 3, True)
    append(urwid.TextCanvas(asc_lines), vis_columns, False)

    if self._file_state.pane == self._file_state.PANE_ASC:
      canvas_def[2][0].cursor = cursor_pos
    else:
      canvas_def[1][0].cursor = cursor_pos

    multi_canvas = urwid.CanvasJoin(canvas_def)
    if multi_canvas.cols() < width:
      multi_canvas.pad_trim_left_right(0, width - multi_canvas.cols())
    return multi_canvas

  def keypress(self, pos, key):
    return key

class Console(ReadlineEdit):
  def __init__(self, app_state, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._app_state = app_state

  def keypress(self, pos, key):
    if (key == 'backspace' and not self.edit_text) or key == 'esc':
      self._app_state.mode = AppState.MODE_NORMAL
      return None
    if key == 'enter':
      self._app_state.accept_raw_input(self.edit_text)
    return super().keypress(pos, key)

  def get_prompt(self):
    return self.caption

  def set_prompt(self, value):
    self.set_caption(value)

  prompt = property(get_prompt, set_prompt)

class StatusBar(urwid.Widget):
  def __init__(self, app_state, *args, **kwargs):
    urwid.Widget.__init__(self, *args, **kwargs)
    self._app_state = app_state
    zope.event.classhandler.handler(
      OffsetChangeEvent, lambda *_: self._invalidate())
    zope.event.classhandler.handler(
      ModeChangeEvent, lambda *_: self._invalidate())

  def rows(self, size, focus=False):
    return 1

  def render(self, size, focus=False):
    right = '0x%X / 0x%X (%d%%)' % (
      self._app_state.cur_file.cur_offset,
      self._app_state.cur_file.size,
      self._app_state.cur_file.cur_offset * (
        100.0 / max(1, self._app_state.cur_file.size)))

    left = '[%s] ' % self._app_state.mode.upper()
    left += trim_left(
      self._app_state.cur_file.file_buffer.path,
      size[0] - (len(right) + len(left) + 3))

    left_canvas = urwid.TextCanvas([left.encode('utf-8')])
    right_canvas = urwid.TextCanvas([right.encode('utf-8')])
    composite_canvas = urwid.CanvasJoin([
      (left_canvas, None, False, size[0] - len(right)),
      (right_canvas, None, False, len(right))])
    return composite_canvas

class DumbPile(urwid.Pile):
  def keypress(self, pos, key):
    return self.focus.keypress(pos, key)

class MainWindow(urwid.Frame):
  def __init__(self, app_state):
    self._app_state = app_state

    self._header = self._make_header()
    self._dump = self._make_dump()
    self._status_bar = self._make_status_bar()
    self._console = self._make_console()

    urwid.Frame.__init__(
      self,
      DumbPile([
        self._dump,
        ('fixed', 1, urwid.Filler(urwid.AttrMap(self._status_bar, 'status'))),
        ('fixed', 1, urwid.Filler(self._console)),
      ]),
      urwid.AttrMap(self._header, 'header'))

    zope.event.classhandler.handler(ModeChangeEvent, self._mode_changed)

  def get_caption(self):
    return re.sub('^hexvi( - )?', '', self._header.base_widget.get_text()[0])

  def set_caption(self, value):
    self._header.base_widget.set_text(
      'hexvi' if not value else 'hexvi - ' + value)

  def _mode_changed(self, evt):
    self._console.edit_text = ''
    if evt.mode == AppState.MODE_NORMAL:
      self._console.prompt = ''
      self.focus.set_focus(0)
    else:
      self._console.prompt = \
        ''.join(evt.traversal.path) if evt.traversal else '>'
      self.focus.set_focus(2)

  def _make_header(self):
    return urwid.Text(u'hexvi')

  def _make_dump(self):
    return Dump(self._app_state, self._app_state.cur_file)

  def _make_status_bar(self):
    return StatusBar(self._app_state)

  def _make_console(self):
    return Console(self._app_state)

  caption = property(get_caption, set_caption)

class Ui(object):
  def __init__(self, app_state):
    self._app_state = app_state

  def run(self):
    self._main_window = MainWindow(self._app_state)
    self._app_state.mode = AppState.MODE_NORMAL

    zope.event.classhandler.handler(
      ProgramExitEvent, lambda *args: self._exit())

    # todo: subscribe to changes of app_sate.cur_file
    self._main_window.caption = self._app_state.cur_file.file_buffer.path

    urwid.MainLoop(
      self._main_window,
      palette=[
        ('selected', 'light red', ''),
        ('header', 'standout', ''),
        ('status', 'standout', ''),
      ],
      unhandled_input=self._key_pressed).run()

  def _exit(self):
    raise urwid.ExitMainLoop()

  def _key_pressed(self, key):
    self._app_state.normal_mode_mappings.keypress(key)
