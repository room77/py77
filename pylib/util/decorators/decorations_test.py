#! /usr/bin/python

"""
Test cases for decorations.
"""

__copyright__ = "Room 77, Inc. 2013"
__author__ = "Pramod Gupta, pramodg@room77.com"

import unittest

from pylib.util.decorators.decorations import static_var


class DecorationsTest(unittest.TestCase):
  """A class for testing decorations."""

  def test_static_var(self):
    """Test for static var."""

    @static_var("counter", 0)
    def foo():
        foo.counter += 1
        return foo.counter

    for i in range(10):
      self.assertEqual(i + 1, foo())

if __name__ == '__main__':
  unittest.main()
