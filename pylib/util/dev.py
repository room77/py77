"""
Development tool utilities
"""

__copyright__ = '2013 Room 77, Inc.'
__author__ = 'Kyle Konrad <kyle@room77.com>'

import inspect
import warnings

def deprecated(message):
  def deprecate(obj):
    class_or_func = 'class' if inspect.isclass(obj) else 'function'
    warnings.warn('Use of deprecated %s %s: %s' % (class_or_func, obj.__name__, message)) # warn at import time
    return obj # unmodified
  return deprecate
