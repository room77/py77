"""
Descriptors
"""

__copyright__ = '2013, Room77, Inc.'
__author__ = "Yu-chi Kuo"


class lazy(object):
  """ Lazy attributes """
  def __init__(self, func, name=None):
    if name is None:
      name = func.__name__
    self.data = (func, name)
  def __get__(self, inst, class_):
    if inst is None: # called at class level
      return self

    func, name = self.data
    try:
      value = inst.__dict__[name]
    except KeyError:
      value = func(inst)
      inst.__dict__[name] = value
    return value
