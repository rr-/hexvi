from hexvi.ui import ui
from hexvi.commands.command import binding


def align(number: int, pad: int) -> int:
    return number - number % pad


@binding(['H'])
def cmd_jump_to_buffer_top() -> None:
    ui.active_window.cursor_offset = ui.active_window.top_offset


@binding(['M'])
def cmd_jump_to_buffer_middle() -> None:
    ui.active_window.cursor_offset = (
        ui.active_window.top_offset +
        align(
            (ui.active_window.bottom_offset_clipped -
                ui.active_window.top_offset) // 2,
            ui.active_window.settings.columns))


@binding(['L'])
def cmd_jump_to_buffer_bottom() -> None:
    ui.active_window.cursor_offset = (
        ui.active_window.bottom_offset_clipped)


@binding(['h', '<repetitions:number>h'])
def cmd_jump_to_column_to_left(repetitions: int=1) -> None:
    ui.active_window.cursor_offset = max(
        0, ui.active_window.cursor_offset - repetitions)


@binding(['l', '<repetitions:number>l'])
def cmd_jump_to_column_to_right(repetitions: int=1) -> None:
    ui.active_window.cursor_offset = min(
        ui.active_window.buffer.size,
        ui.active_window.cursor_offset + repetitions)


@binding(['k', '<repetitions:number>k'])
def cmd_jump_to_line_above(repetitions: int=1) -> None:
    ui.active_window.cursor_offset = max(
        0,
        ui.active_window.cursor_offset
        - ui.active_window.settings.columns * repetitions)


@binding(['j', '<repetitions:number>j'])
def cmd_jump_to_line_below(repetitions: int=1) -> None:
    ui.active_window.cursor_offset = min(
        ui.active_window.buffer.size,
        ui.active_window.cursor_offset
        + ui.active_window.settings.columns * repetitions)
