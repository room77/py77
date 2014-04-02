"""
Tests for HAProxyMonitor

run with nosetests
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrad <kyle@room77.com>'

from datetime import datetime, timedelta
from flexmock import flexmock
import unittest

from .conditions import more_than_n_down, any_down_longer_than
from .haproxy_monitor import HAProxyMonitor, ProxyStats

def seconds_ago(seconds):
  return datetime.utcnow() - timedelta(seconds=seconds)

class TestHAProxyMonitor(unittest.TestCase):
  def test_check(self):
    conditions = {'': [any_down_longer_than(timedelta(minutes=30))],
                  'test$': [more_than_n_down(1)]}
    monitor = HAProxyMonitor('https://foo.bar', 'user', 'passwd',
                             'test@room77.com', conditions)

    # return fake stats
    (flexmock(monitor)
     .should_receive('stats')
     .and_return({
      'test': ProxyStats('test', 4, 2, {'test01': seconds_ago(5),
                                        'test02': seconds_ago(4)}),
      'another_test': ProxyStats('another_test', 3, 0,
                                 {'another_test01': seconds_ago(4)}),
      'whatever': ProxyStats('whatever', 3, 0,
                             {'whatever01': seconds_ago(45),
                              'whatever02': seconds_ago(40*60)})
      }))

    # the stats above should fail two conditions:
    #  - more than 1 "test" servers are down
    #  - whatever02 has been down for more than 30 mintes
    (flexmock(monitor)
     .should_receive('send_email')
     .and_return(True)
     .times(2))

    monitor.alert()
