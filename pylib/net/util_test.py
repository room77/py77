"""
tests for net util module

run with nosetests
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrad'

import unittest

import pylib.net.util

class RpcTest(unittest.TestCase):
  def call_test(self):
    self.assertEqual(util.rpc('/Ping', 0), 1)

  def call_failure_test(self):
    with self.assertRaises(ValueError):
      util.rpc('/Bogus', verify=False)

if __name__ == '__main__':
  unittest.main()
