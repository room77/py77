"""
Unit test of decsriptor module
"""

__author__ = 'Yu-chi Kuo'
__copyright__ = '2013, Room77, Inc'

import unittest

import r77_init  # pylint: disable=W0611
from descriptor import lazy

class LazyPropertyTest(unittest.TestCase):
  def test_simple(self):
    class Foo(object):
      def __init__(self):
        self.x = 2
      @lazy
      def bar(self):
        return self.x ** 2

    foo = Foo()
    self.assertEqual(foo.bar, 4)

  def test_no_double_calc(self):
    """ Test that the same property is calculated for exactly once"""
    class Foo(object):
      def __init__(self, x):
        self.x = x
        self.has_calc = False

      @lazy
      def y(self):
        assert self.has_calc == False
        self.has_calc = True
        return self.x ** 2

    foo = Foo(3)
    self.assertEqual(foo.y, 9)
    self.assertEqual(foo.y, 9)

  def test_two_lazy_props(self):
    """ Test it works in multiple lazy props """
    class Foo(object):
      def __init__(self, x, y):
        self.x = x
        self.y = y

      @lazy
      def a(self):
        return self.x * self.y

      @lazy
      def b(self):
        return self.x + self.y

    foo = Foo(2, 3)
    self.assertEqual(foo.a, 6)
    self.assertEqual(foo.b, 5)

  def test_across_instance(self):
    """ Test it works for multiple instances of the same class """
    class Foo(object):
      def __init__(self, x):
        self.x = x

      @lazy
      def y(self):
        return self.x * 2

    foo = Foo(1)
    bar = Foo(3)
    self.assertEqual(foo.y, 2)
    self.assertEqual(bar.y, 6)

if __name__ == '__main__':
  unittest.main()
