"""
Parses the include.*.list files. If the file is a valid
include file it is parsed; otherwise the original file
is returned
"""

class ParseIncludeList:
  """
  @TODO(edelman) handle recursive include dependencies
  """
  # the end str of the include path
  INCLUDE_END_STR = '.list'

  def get_files(self):
    """
    Checks if the file is a valid include file. If so,
    the include file is expanded. Otherwise, the original
    file is returned.
    @return List of filenames. throws exception on io error
    """
    return list(self._files)

  def __init__(self, include_path):
    """
    @param include_path - the potential include path
    """
    self._include_path = include_path.strip()
    self._files = []
    # if not valid, simply use the passed in path
    if not self._valid_include_file():
      self._files.append(self._include_path)
    else:
      f = open(self._include_path, 'r')
      for line in f:
        line = line.strip()
        if line and not '#' in line:
          self._files.append(line)

  def _valid_include_file(self):
    """ @return {bool} True if valid to parse, False otherwise"""
    include_end_str = ParseIncludeList.INCLUDE_END_STR
    return len(self._include_path) > len(include_end_str) and \
           self._include_path[-1*len(include_end_str):] == include_end_str

