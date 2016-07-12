"""
Tests for dictionary utils
"""

import unittest

from pylib.util.dictionary import *

class TestLRUDict(unittest.TestCase):
  SIZE = 3
  def setUp(self):
    self.lru_dict = LRUDict(self.SIZE)

  def test_expiration(self):
    self.lru_dict[1] = 1
    self.assertEqual(dict(self.lru_dict), {1: 1})
    self.lru_dict[2] = 2
    self.assertEqual(dict(self.lru_dict), {1: 1, 2: 2})
    self.lru_dict[3] = 3
    self.assertEqual(dict(self.lru_dict), {1: 1, 2: 2, 3: 3})
    self.lru_dict[4] = 4
    self.assertEqual(dict(self.lru_dict), {2: 2, 3: 3, 4: 4})

  def test_update(self):
    self.lru_dict[1] = 1
    self.lru_dict[2] = 2
    self.lru_dict[1] = 3
    self.assertEqual(dict(self.lru_dict), {1: 3, 2: 2})
    self.lru_dict[3] = 4
    self.assertEqual(dict(self.lru_dict), {1: 3, 2: 2, 3: 4})
    self.lru_dict[4] = 5
    self.assertEqual(dict(self.lru_dict), {1: 3, 3: 4, 4: 5})
