"""
string utils
"""

__author__ = 'Kyle Konrad <kyle@room77.com>'
__copyright__ = '2013, Room 77, Inc.'

from itertools import izip_longest

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
  return izip_longest(fillvalue=fillvalue, *args)
