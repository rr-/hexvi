from hexvi.io.io_buffer import IOBuffer
import logging


class WindowSettings:
    def __init__(self) -> None:
        self.columns = 32
        self.auto_columns = True


class Window:
    def __init__(self, buffer: IOBuffer) -> None:
        self.buffer = buffer
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.settings = WindowSettings()
        self._top_offset = 0
        self._cursor_offset = 0

    @property
    def cursor_offset(self) -> int:
        return self._cursor_offset

    @cursor_offset.setter
    def cursor_offset(self, value: int) -> None:
        if value < 0:
            value = 0
        if value > self.buffer.size:
            value = self.buffer.size
        self._cursor_offset = value

    @property
    def height_clipped(self) -> int:
        return min(
            self.height,
            (self.buffer.size - self.top_offset + self.settings.columns - 1)
            // self.settings.columns)

    @property
    def top_offset(self) -> int:
        return self._top_offset

    @property
    def bottom_offset(self) -> int:
        if not self.height or not self.settings.columns:
            return self.top_offset
        return self.top_offset + (self.height - 1) * self.settings.columns

    @property
    def bottom_offset_clipped(self) -> int:
        if not self.height_clipped or not self.settings.columns:
            return self.top_offset
        return self.top_offset + (
            self.height_clipped - 1) * self.settings.columns
