class FileBuffer(object):
  def __init__(self, path):
    with open(path, 'rb') as fh:
      self._content = fh.read()
    self._path = path

  def get_content(self):
    return self._content

  def get_content_range(self, offset, size):
    return self._content[offset:offset+size]

  def get_path(self):
    return self._path

  def get_size(self):
    return len(self._content)

  size = property(get_size)
  path = property(get_path)
  content = property(get_content)
