"""
Few Threading util decorations.
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Pramod Gupta'

def synchronized(lock):
    '''Synchronization decorator.
    Args:
      lock: Lockable Object(supports acquire and release): The lock to use for synchronization.
      # Example usage:

      from threading import Lock
      my_lock = Lock()

      @synchronized(my_lock)
      def critical1(*args):
          # Interesting stuff goes here.
          pass

      @synchronized(my_lock)
      def critical2(*args):
          # Other interesting stuff goes here.
          pass
    '''
    def wrap(f):
        def new_function(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        return new_function
    return wrap

