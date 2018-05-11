"""
string utils
"""

__author__ = 'Kyle Konrad <kyle@room77.com>'
__copyright__ = '2013, Room 77, Inc.'

# Python 2/3 compatibility
try:
  from itertools import zip_longest # Python 3
except ImportError:
  from itertools import izip_longest as zip_longest # Python 2

def chunk(iterable, n, fillvalue=None):
  """
  Collect data into fixed-length chunks or blocks
  Source: http://docs.python.org/2/library/itertools.html#recipes

  Args:
    n (int): number of elements per chunk
    fillvalue: value to fill last group with
  """
  # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
  args = [iter(iterable)] * n
  return zip_longest(fillvalue=fillvalue, *args)
