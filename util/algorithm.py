"""
Python algorithms
"""

__author__ = "Kar Epker (karepker@room77.com), Kyle Konrad (kyle@room77.com)"
__copyright__ = "Room 77, Inc. 2013"

import random

def nth_element(x, n):
  """Returns the nth order statistic of a list

  Note on stability: If multiple order statistics are equal, this function
    will return the first index of the element in the list

  Args:
    x (list): The list from which to chooise
    n (nonnegative int): The order statistic to get

  Returns:
    A tuple of (element, position of element in list)

  Raises:
    IndexError if n is greater than or equal to length of x

  DocTests:
  >>> nth_element([4, 2, 5, 1, 3], 0)
  (1, 3)
  >>> nth_element([5, 15, 3, 6], 3)
  (15, 1)
  >>> nth_element([1, 2, 3], 2)
  (3, 2)
  >>> nth_element([3, 2, 1], 2)
  (3, 0)
  >>> nth_element([7, 7, 7, 7, 7, 7, 7], 3)
  (7, 0)
  >>> nth_element([7, 7, 7, 7, 7, 7, 7], 6)
  (7, 0)
  >>> nth_element([4, 10, 3, 16, 7, 8, 15, 9], 3)
  (8, 5)
  >>> nth_element([1, 5, 9, 3, 0, 12, 5], 5)
  (9, 2)
  >>> nth_element([4, 3, 5, 2], 2)
  (4, 0)
  """
  # make sure the index exists
  if n >= len(x):
    raise IndexError

  tmp = x
  index = n
  position = 0
  while tmp:
    # partition the elements
    pivot = tmp[random.randint(0, len(tmp) - 1)]
    # make lists of elements higher and lower than the pivot
    above = []
    below = []
    for elt in tmp:
      if elt < pivot:
        below.append(elt)
      elif elt > pivot:
        above.append(elt)
    i = len(below)
    j = len(tmp) - len(above)

    # determine which partition to further examine if necessary
    if index < i:
      tmp = below
    elif index >= j:
      tmp = above
      index -= j
    else:
      return pivot, x.index(pivot)

if __name__ == '__main__':
  import doctest
  doctest.testmod()
