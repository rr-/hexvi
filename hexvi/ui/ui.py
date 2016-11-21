import argparse
import math
import curses
import re
from hexvi.ui.window import Window
from hexvi.io.io_buffer import IOBuffer
from hexvi.event import Event, add_event_listener, emit_event
from hexvi.keyboard import binding_list
from typing import Any, List
import logging


def _parse_args() -> Any:
    parser = argparse.ArgumentParser(description='hex editor inspired by vim')
    parser.add_argument('path', help='file to edit')
    parser.add_argument(
        '-d', '--debug', help='enable debug logs', action='store_true')
    return parser.parse_args()


class StopProgram(RuntimeError):
    pass


class ResizeEvent(Event):
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height


def get_offset_size(max_offset: int) -> int:
    size = 0
    align = 4
    while max_offset:
        max_offset >>= 4 * align
        size += align
    return max(align, size)


class UI:
    def __init__(self) -> None:
        args = _parse_args()
        super().__init__()

        if args.debug:
            logging.basicConfig(filename='debug.log', level=logging.DEBUG)

        self.windows = []  # type: List[Window]
        if args.path:
            self.windows.append(Window(IOBuffer(args.path)))
        else:
            self.windows.append(Window(IOBuffer()))

        self.active_window = self.windows[-1]

    def run(self) -> None:
        def func(screen: Any) -> None:
            self.screen = screen
            add_event_listener(ResizeEvent, self._on_resize)

            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_RED, -1)
            curses.init_pair(2, -1, -1)

            height, width = screen.getmaxyx()
            emit_event(ResizeEvent(width, height))

            self.draw_window(screen, self.active_window)

            while True:
                try:
                    key = screen.getch()
                    if key == curses.KEY_RESIZE:
                        height, width = screen.getmaxyx()
                        emit_event(ResizeEvent(width, height))
                    else:
                        binding_list.accept_char(chr(key))
                except StopProgram:
                    break

                self.draw_window(screen, self.active_window)

        curses.wrapper(func)

    def _on_resize(self, e: ResizeEvent) -> None:
        logging.info('Terminal size changed: %dx%d', e.width, e.height)
        for window in self.windows:
            window.width = e.width
            window.height = e.height - 1
            if window.settings.auto_columns:
                window.settings.columns = int(
                    (e.width - get_offset_size(window.buffer.size) - 2)
                    // 4)

    def draw_window(self, screen: Any, window: Window) -> None:
        logging.debug('Redrawing')

        screen.erase()
        for i in range(window.height):
            y = window.y + i
            x = window.x

            offset = (window.top_offset + i * window.settings.columns)
            offset_size = get_offset_size(window.buffer.size)
            line = window.buffer.read_bytes_trunc(
                offset, window.settings.columns)

            try:
                screen.addstr(y, 0, '%0*x' % (offset_size, offset))
                x += offset_size + 1
                for i, c in enumerate(line):
                    screen.addstr(y, x + 3 * i, '%02x' % c)
                x += 3 * window.settings.columns
                screen.addstr(y, x, re.sub(b'[^\x20-\x7F]', b'.', line))
            except curses.error:
                pass

        cursor_offset = window.cursor_offset - window.top_offset
        cursor_offset_x = cursor_offset % window.settings.columns
        cursor_offset_y = cursor_offset // window.settings.columns
        cursor_offset_x = window.x + offset_size + 1 + 3 * cursor_offset_x
        cursor_offset_y = window.y + cursor_offset_y
        screen.move(cursor_offset_y, cursor_offset_x)
        screen.refresh()

    def refresh(self) -> None:
        self.draw_window(self.screen, self.active_window)


ui = UI()
