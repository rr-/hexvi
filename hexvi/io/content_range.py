from hexvi.io.range import Range


class ContentRange(Range):
    def read_bytes(self, offset: int, size: int) -> bytes:
        raise NotImplementedError()

    def get_narrowed(self, offset: int, size: int) -> 'ContentRange':
        raise NotImplementedError()
