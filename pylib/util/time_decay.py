""" Library for updating values and counters based taking into account a time
decay funtion"""

__author__ = 'Andrea Tacchetti - atacchet@room77.com - Contact: kyle@'
__copyright__ = '2013, Room77, Inc'

import datetime
from pylib.base.flags import Flags


class TimeStampInTheFutureError(Exception):

  def __init__(self, timestamp):
    self.timestamp = timestamp
  def __str__(self):
    return 'Timestamp: %s is in the future' % timestamp.strftime('%m.%d.%Y')


class TimeDecay(object):
  """TimeDecay class. Helps to update counters that require a time decay"""
  def __init__(self, decay_time, decay_factor=2.0):
    """
    decay_time is timedelta
    """
    if decay_time <= datetime.timedelta(0):
      raise ValueError('decay_time must have positive duration')
    self.decay_time = decay_time
    self.decay_factor = decay_factor

  def update_value(self, value, now=None):
    """Computes the updated value for the given half-life.

    Args:
      value (tuple(datetime.datetime, numeric_type)): tuple with the numeric
          value we wish to update (must support multiplication with a scalar as *)
          and timestamp.
      now (datetime.datetime): used as current time. If not provided, actual
          current time is used. Should be UTC.
    Returns:
      value (tuple(numeric_type, datetime.datetime)): tuple with updated numeric
      value and timestamp.
    Raises:
      TimeStampInTheFutureError: the timestamp passed as argument is in the
      future with respect to self.today.
    """

    timestamp, x = value
    if now is None:
      now = datetime.datetime.utcnow()
    delta = now - timestamp
    if delta < datetime.timedelta(seconds=0):
      raise TimeStampInTheFutureError(timestamp)
    x *= pow(self.decay_factor,
        -delta.total_seconds()/self.decay_time.total_seconds())
    return (now, x)
