#! /usr/bin/python

"""
Test cases for operations on list
"""

__author__ = "Kar Epker, karepker@room77.com"
__copyright__ = "Room 77, Inc. 2013"

import unittest

import r77_init  # pylint: disable=W0611
from pylib.util.math.list_ops import mean_std, median
from pylib.util.math.errors import NotDefinedError

class ListOpsTest(unittest.TestCase):
  """A class for testing mathematical list operations"""

  def test_mean_std_error(self):
    self.assertRaises(NotDefinedError, mean_std, [])
    self.assertRaises(NotDefinedError, mean_std, [1], pop=False)

  def test_mean_std_single(self):
    self.assertEqual(mean_std([1]), (1, 0))

  def test_mean_std_same(self):
    self.assertEqual(mean_std([2, 2, 2, 2]), (2, 0))
    self.assertEqual(mean_std([2, 2, 2, 2], pop=False), (8/3, 0))

  def test_mean_std_typical(self):
    mean, std = mean_std([5, 7, 8, 6])
    self.assertEqual(mean, 6.5)
    self.assertEqual(round(std, 5), 1.11803)
    mean, std = mean_std([5, 7, 8, 6], pop=False)
    self.assertEqual(mean, 6.5)
    self.assertEqual(round(std, 5), 1.29099)

  def test_median_empty(self):
    self.assertRaises(NotDefinedError, median, [])

  def test_median_single(self):
    self.assertEqual(median([2]), 2)

  def test_median_even(self):
    self.assertEqual(median([4, 3, 5, 2]), 3.5)

  def test_median_odd(self):
    self.assertEqual(median([3, 5, 2]), 3)

if __name__ == '__main__':
  unittest.main()
