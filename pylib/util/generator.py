"""
Util functions for generator
"""
__copyright__ = '2013, Room77, Inc.'
__author__ = "Yu-chi Kuo"

def advance_generator_once(f):
  """
  decorator to advance a generator once immediately after it is created
  """
  def decorated(*args, **kwargs):
    gen = f(*args, **kwargs)
    assert next(gen) is None
    return gen
  return decorated
