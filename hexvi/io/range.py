class Range:
    def __init__(self, start_offset: int, size: int) -> None:
        self.start_offset = start_offset
        self.size = size

    @property
    def end_offset(self) -> int:
        return self.start_offset + self.size

    @end_offset.setter
    def end_offset(self, value: int) -> None:
        self.start_offset = value - self.size

    def __contains__(self, offset: int) -> bool:
        return offset in range(self.start_offset, self.end_offset + 1)
