import os

class FileBuffer(object):
  def __init__(self, path):
    self._handle = open(path, 'rb')
    self._path = path

  def __destroy__(self):
    close(self._handle)

  def get_content_range(self, offset, size):
    self._handle.seek(offset, os.SEEK_SET)
    return self._handle.read(size)

  def get_path(self):
    return self._path

  def get_size(self):
    old_off = self._handle.tell()
    self._handle.seek(0, os.SEEK_END)
    size = self._handle.tell()
    self._handle.seek(old_off, os.SEEK_SET)
    return size

  size = property(get_size)
  path = property(get_path)
