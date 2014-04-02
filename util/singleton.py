"""
Singleton implementation.
Usage:

class A(singleton.Singleton): pass

Please NOTE:
id(A.Instance()), id(A))
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Pramod Gupta'

import threading


class SingletonException(Exception):
    pass


class _SingletonMeta(type):
  def __new__(cls, name, bases, dct):
    if dct.has_key('__new__'):
      raise SingletonException, 'Can not override __new__ in a Singleton'
    return super(_SingletonMeta, cls).__new__(cls, name, bases, dct)

  def __call__(cls, *args, **dictArgs):
    raise SingletonException('Singletons may only be instantiated through Instance()')


class Singleton(object):
  __metaclass__ = _SingletonMeta
  _lock = threading.RLock()

  @classmethod
  def Instance(cls, *args, **kw):
    """
    Call this to instantiate an instance or retrieve the existing instance.
    If the singleton requires args to be instantiated, include them the first
    time you call Instance.
    """
    if not cls.Instantiated(): Singleton._createSingletonInstance(cls, args, kw)
    return cls._instance

  @classmethod
  def Instantiated(cls):
      # Don't use hasattr(cls, '_instance'), because that screws things up if there is a singleton
      # that extends another singleton.
      # hasattr looks in the base class if it doesn't find in subclass.
      return '_instance' in cls.__dict__

  @staticmethod
  def _createSingletonInstance(cls, args, kw):
    with Singleton._lock:
      # Check if the the class really needs to be instantiated.
      if cls.Instantiated(): return

      try:
      # Create the new instance and init it.
        instance = cls.__new__(cls)
        instance.__init__(*args, **kw)
      except TypeError, e:
        if e.message.find('__init__() takes') != -1:
          raise SingletonException('If the singleton requires __init__ args, '
                                   'supply them on first call to Instance().')
        else:
          raise e
      cls._instance = instance

