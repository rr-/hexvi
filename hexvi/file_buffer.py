import os

class FileBuffer(object):
  def __init__(self, path=None):
    if path:
      self._handle = open(path, 'rb')
      self._path = path
    else:
      self._handle = None
      self._path = None

  def __destroy__(self):
    close(self._handle)

  def get_content_range(self, offset, size):
    if self._handle:
      self._handle.seek(offset, os.SEEK_SET)
      return self._handle.read(size)
    return b''

  def get_path(self):
    return self._path

  def get_size(self):
    if self._handle:
      old_off = self._handle.tell()
      self._handle.seek(0, os.SEEK_END)
      size = self._handle.tell()
      self._handle.seek(old_off, os.SEEK_SET)
      return size
    else:
      return 0

  size = property(get_size)
  path = property(get_path)
