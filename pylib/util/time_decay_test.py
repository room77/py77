"""Tester module for TimeDecay"""

__author__ = 'Andrea Tacchetti - atacchet@room77.com - Contact: kyle@'
__copyright__ = '2013, Room77, Inc'

import datetime
import unittest

from pylib.util.time_decay import (TimeDecay, TimeStampInTheFutureError)

class TimeDecayTest(unittest.TestCase):

  def test_basic(self):
    x = 10.0
    timestamp = datetime.datetime(2013,2,27)
    today = datetime.datetime.utcnow()
    td = TimeDecay(datetime.timedelta(30))
    (new_timestamp, y) = td.update_value((timestamp, x))
    self.assertTrue(y < x)
    self.assertEqual(new_timestamp.hour, today.hour)
    self.assertEqual(new_timestamp.minute, today.minute)
    self.assertEqual(new_timestamp.second, today.second)


  def test_half_life(self):
    x = 10.0
    timestamp = datetime.datetime.utcnow()- datetime.timedelta(days=15)
    td = TimeDecay(decay_time=datetime.timedelta(15))
    (new_timestamp, y) = td.update_value((timestamp, x))
    self.assertAlmostEqual(y, 5.0)

  def test_future(self):
    x = 10.0
    timestamp = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    td = TimeDecay(decay_time=datetime.timedelta(30))
    self.assertRaises(TimeStampInTheFutureError, td.update_value, (timestamp,x))


if __name__ == '__main__':
  unittest.main()
