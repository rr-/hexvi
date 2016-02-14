class FileBuffer(object):
    def __init__(self, path):
        with open(path, 'rb') as fh:
            self._content = fh.read()
        self._path = path
        self._offset = 0

    def get_content(self):
        return self._content

    def get_content_range(self, offset, size):
        return self._content[offset, size]

    def get_path(self):
        return self._path

    def get_offset(self):
        return self._offset

    def set_offset(self, value):
        self._offset = value

    path = property(get_path)
    offset = property(get_offset, set_offset)
    content = property(get_content)
