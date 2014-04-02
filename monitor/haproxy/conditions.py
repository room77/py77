"""
Conditions for sending alert emails for HAProxy Monitor

A condition is a callable that takes a ProxyStats object and
returns an error string or None for success
"""

from datetime import datetime

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrad <kyle@room77.com>'

def more_than_n_down(n):
  """
  Args:
    n (int): number of instances down to trigger an alert
  """
  def func(stats):
    if stats.down_count > n:
      return '%d of %d %s instances are down' % (
        stats.down_count, stats.down_count + stats.up_count, stats.name)
  return func

def more_than_proportion_down(prop):
  """
  Args:
    prop (float): proportion of instance down to trigger an alert
  """
  def func(stats):
    total_count = stats.down_count + stats.up_count
    if total_count and stats.down_count / total_count > prop:
      return '%d of %d %s instances are down' % (
        stats.down_count, stats.down_count + stats.up_count, stats.name)
  return func

def any_down_longer_than(duration):
  """
  Args:
    duration (timedelta): duration of instance down to trigger an alert
  """
  def func(stats):
    now = datetime.utcnow()
    for server, last_up in stats.last_up_times.items():
      downtime = now - last_up
      if downtime > duration:
        return '%s on %s has been down for %d minutes' % (
          server, stats.name, downtime.total_seconds() / 60)
  return func
