"""
Util functions for dictionary
"""
__copyright__ = '2013, Room77, Inc.'
__author__ = 'Yu-chi Kuo, Kyle Konrad <kyle@room77.com>'

from collections import MutableMapping, OrderedDict

def dict_key_filter(function, dictionary):
  """
  Filter dictionary by its key.

  Args:
    function: takes key as argument and returns True if that item should be
              included
    dictionary: python dict to filter
  """
  return {k: v for k, v in dictionary.items() if function(k)}

def dict_val_filter(function, dictionary):
  """
  Filter dictionary by its value.

  Args:
    function: takes value as argument and returns True if that item should be
              included
    dictionary: python dict to filter
  """
  return {k: v for k, v in dictionary.items() if function(v)}

def dict_filter(function, dictionary):
  """
  Filter dictionary by its key and value.

  Args:
    function: takes k, v as argument and returns True if that item should be
              included
    dictionary: python dict to filter
  """
  return {k: v for k, v in dictionary.items() if function(k, v)}

def dict_reverse(dictionary):
  """
  Reverse a dictionary. If values are not unique, only one will be used. Which one is not specified

  Args:
    dictionary (dict): dict to reverse

  Returns:
    reversed (dict): reversed dictionary
  """
  return {v: k for k, v in dictionary.items()}

class LRUDict(MutableMapping):
  """
  A dictionary of limited size where items are evicted in LRU-order

  inspired by http://stackoverflow.com/a/2438926
  """
  def __init__(self, size, *args, **kwargs):
    self.size = size
    self.dict = OrderedDict(*args, **kwargs)
    while len(self) > self.size:
      self.dict.popitem(last=False)

  def __iter__(self):
    return iter(self.dict)

  def __len__(self):
    return len(self.dict)

  def __getitem__(self, key):
    return self.dict[key]

  def __setitem__(self, key, value):
    if key not in self and len(self) == self.size:
      self.dict.popitem(last=False)
    if key in self: # need to delete and reinsert to maintain order
      del self[key]
    self.dict[key] = value

  def __delitem__(self, key):
    del self.dict[key]
