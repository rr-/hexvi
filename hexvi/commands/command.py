from typing import Callable, List, Any
from hexvi.ui import ui, StopProgram
from hexvi.keyboard import binding_list


def binding(sequences: List[str]) -> Callable:
    def wrapper(cmd: Callable) -> None:
        def execute(**kwargs: List[Any]) -> None:
            cmd(**kwargs)
            ui.refresh()

        for sequence in sequences:
            binding_list.bind(sequence, execute)
    return wrapper


@binding(['q', '^q'])
def cmd_execute() -> None:
    raise StopProgram()
