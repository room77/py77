"""
Tests for singleton
"""

__copyright__ = "Room 77, Inc. 2013"
__author__ = "Pramod Gupta, pramodg@room77.com"

import unittest

import pylib.util.singleton as singleton


class SingletonTest(unittest.TestCase):
  """A class for testing singleton"""

  def test_sanity(self):
    class A(singleton.Singleton):
        member1 = 1
        counter = 0

        def __init__(self):
          self.counter += 1;
          print "Init called:"

    self.assertNotEqual(id(A.Instance()), id(A))
    self.assertEqual(A.Instance().member1, A.member1)
    A.Instance().member1 = 20
    self.assertEqual(20, A.Instance().member1)
    self.assertEqual(20, A.Instance().member1)
    self.assertEqual(1, A.Instance().counter)
    self.assertEqual(0, A.counter)

  def test_multi_arg(self):
    class A(singleton.Singleton):
      def __init__(self, arg1, arg2):
        super(A, self).__init__()
        self.arg1 = arg1
        self.arg2 = arg2

    i1 = A.Instance('arg1 value', 'arg2 value')
    i2 = A.Instance('!arg1 value', '!arg2 value')
    self.assertEquals(id(i1), id(i2))
    self.assertEquals(i2.arg1, 'arg1 value')
    self.assertEquals(i2.arg2, 'arg2 value')

  def test_kw_args(self):
      class A(singleton.Singleton):
          def __init__(self, arg1=5):
              super(A, self).__init__()
              self.arg1 = arg1

      i1 = A.Instance(arg1=10)
      i2 = A.Instance(arg1=20)
      self.assertEquals(id(i1), id(i2))
      self.assertEquals(i2.arg1, 10)

  def test_create_without_args(self):
      class A(singleton.Singleton):
        def __init__(self, arg1, arg2):
          super(A, self).__init__()
          self.arg1 = arg1
          self.arg2 = arg2

      self.assertRaises(singleton.SingletonException, A.Instance)

  def test_type_error(self):
    class A(singleton.Singleton):
      def __init__(self, arg1, arg2):
        super(A, self).__init__()
        self.arg1 = arg1
        self.arg2 = arg2
        raise TypeError, 'some type error'

    self.assertRaises(TypeError, A.Instance, 1, 2)

  def test_try_direct_create(self):
      class A(singleton.Singleton):
          def __init__(self):
              super(A, self).__init__()

      self.assertRaises(singleton.SingletonException, A)

  def test_inheritance(self):
    class Base(singleton.Singleton):
      def set_x(self, x):
        self.x = x

    class Derived(Base):
      def set_y(self, y):
        self.y = y

    b = Derived.Instance()
    b.set_x(-5)
    b.set_y(50)
    a = Base.Instance()
    a.set_x(5)

    self.assertEqual((a.x, b.x, b.y), (5, -5, 50))
    self.assertRaises(AttributeError, eval, 'a.setY', {}, locals())
    self.assertNotEqual(id(a), id(b))


if __name__ == '__main__':
  unittest.main()
