#! /usr/bin/python

"""
Test cases for user defined datetime functions
"""

__author__ = "Kar Epker, karepker@room77.com"
__copyright__ = "Room 77, Inc. 2013"

import datetime
import unittest

import r77_init  # pylint: disable=W0611
from pylib.util.date_time import date_range

class DateRangeTest(unittest.TestCase):
  """A class for testing datetime operations"""

  def test_sanity(self):
    expected = [datetime.date(2013, 4, 5)]
    test = list(date_range(datetime.date(2013, 4, 5),
      datetime.date(2013, 4, 6)))
    self.assertEqual(test, expected)

  def test_negative_interval(self):
    expected = [datetime.date(2013, 4, 5), datetime.date(2013, 4, 4)]
    test = list(date_range(datetime.date(2013, 4, 5),
      datetime.date(2013, 4, 3), interval=datetime.timedelta(days=-1)))
    self.assertEqual(test, expected)

  def test_non_hour_intervals(self):
    test1 = list(date_range(datetime.datetime(2013, 4, 5, 15),
      datetime.datetime(2013, 4, 5, 17), interval=datetime.timedelta(hours=1)))
    expected1 = [datetime.datetime(2013, 4, 5, 15, 0),
      datetime.datetime(2013, 4, 5, 16, 0)]
    self.assertEqual(test1, expected1)
    test2 = list(date_range(datetime.datetime(2013, 4, 5, 15, 5),
      datetime.datetime(2013, 4, 5, 15, 2), interval=datetime.timedelta(
      minutes=-1)))
    expected2 = [datetime.datetime(2013, 4, 5, 15, 5), datetime.datetime(
      2013, 4, 5, 15, 4), datetime.datetime(2013, 4, 5, 15, 3)]
    self.assertEqual(test2, expected2)

  def test_no_hit_end(self):
    test = list(date_range(datetime.date(2013, 4, 5),
      datetime.date(2013, 4, 10), interval=datetime.timedelta(days=2)))
    expected = [datetime.date(2013, 4, 5), datetime.date(2013, 4, 7),
      datetime.date(2013, 4, 9)]
    self.assertEqual(test, expected)

  def test_wrong_way_interval(self):
    test1 = list(date_range(datetime.date(2013, 4, 5),
      datetime.date(2013, 4, 6), interval=datetime.timedelta(days=-1)))
    expected1 = []
    self.assertEqual(test1, expected1)
    test2 = list(date_range(datetime.date(2013, 4, 5),
      datetime.date(2013, 4, 4), interval=datetime.timedelta(days=1)))
    expected2 = []
    self.assertEqual(test2, expected2)

  def test_interval_larger_than_diff(self):
    test = list(date_range(datetime.datetime(2013, 4, 5, 15, 5, 20),
      datetime.datetime(2013, 4, 5, 15, 5, 10), interval=datetime.timedelta(
      hours=-1)))
    expected = [datetime.datetime(2013, 4, 5, 15, 5, 20)]
    self.assertEqual(test, expected)

  def test_zero_interval(self):
    self.assertRaises(ValueError, list, date_range(datetime.date(2013, 4, 5),
      datetime.date(2013, 4, 6), interval=datetime.timedelta(days=0)))
    self.assertRaises(ValueError, list, date_range(datetime.date(2013, 4, 5),
      datetime.date(2013, 4, 6), interval=datetime.timedelta(hours=0)))


if __name__ == '__main__':
  unittest.main()
