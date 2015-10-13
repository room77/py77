"""
Mathematical operations that may be performed on a list
"""

__author__ = "Kar Epker, karepker@gmail.com"
__copyright__ = "Room 77, Inc. 2013"

import math

import r77_init  # pylint: disable=W0611
from pylib.util.math.errors import NotDefinedError
from pylib.util.algorithm import nth_element

def mean_std(x, pop=True):
  """Calculate mean and standard deviation of a list using Knuth/Welford's algorithm

  See this page:
    http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance

  Args:
    x (list): A list of reals
    pop (bool): Calculate the mean and standard deviation for a population or
      sample (default: population)

  Returns:
    The mean, standard deviation of x

  Raises:
    NotDefinedError if list is empty or if list has length one and pop is True
  """
  # check for length 0 list or length 1 list with pop False
  if not x or (len(x) == 1 and not pop):
    raise NotDefinedError('mean_std', {'x': x, 'pop': pop})

  # calculate two sums
  mean = 0
  M2 = 0

  for n, elt in enumerate(x):
    delta = elt - mean
    mean += float(delta)/(n + 1)
    M2 += delta * (elt - mean)

  std = math.sqrt(M2 / (n + 1)) if pop else math.sqrt(M2 / (n))
  return mean, std


def median(x):
  """Calculates the median of x

  Args:
    x (list): A list of reals

  Returns:
    The median of x

  Raises:
    NotDefinedError if list is empty
  """
  # check for length 0 list
  if not x:
    raise NotDefinedError('median', {'x': x})

  # choose order statistics to get based on length of list
  if len(x) % 2 == 1:
    index = int(math.floor(len(x) / 2))
    return nth_element(x, index)[0]
  else:
    lower_elt = nth_element(x, int(len(x) / 2) - 1)[0]
    upper_elt = nth_element(x, int(len(x) / 2))[0]
    return float(lower_elt + upper_elt)/2
