"""
Tests for HAProxyMonitor

run with nosetests
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrad <kyle@room77.com>'

from flexmock import flexmock
import unittest

from pylib.monitor.haproxy.haproxy_cluster_monitor_group import HAProxyClusterMonitorGroup

def mock_monitor(url, available):
  """
  Create a mock HAProxyMonitor

  Args:
    url (string): url of haproxy stats page for this monitor
    available (bool): whether this monitor is reachable
  """
  mock_monitor = flexmock(url=url)
  if available:
    mock_monitor.should_receive('check').and_return(True)
  else:
    mock_monitor.should_receive('check').and_raise(IOError)
  return mock_monitor

class TestHAProxyClusterMonitorGroup(unittest.TestCase):
  def test_check(self):
    cluster_monitors = {'cluster1': [mock_monitor(
      'http://cluster1.room77.com/mock_haproxy', avail) for avail in
                                     [True, True, True, True]],
                        'cluster2': [mock_monitor(
      'http://cluster2.room77.com/mock_haproxy', avail) for avail in
                                     [False, True, True, True]],
                        'cluster3': [mock_monitor(
      'http://cluster3.room77.com/mock_haproxy', avail) for avail in
                                     [True, False, False, False]],
                        'cluster4': [mock_monitor(
      'http://cluster3.room77.com/mock_haproxy', avail) for avail in
                                     [False, True, True, False]]}

    monitor_group = HAProxyClusterMonitorGroup('test@room77.com',
                                               cluster_monitors)

    # mock is_active so we don't read clusters conf
    (flexmock(monitor_group)
     .should_receive('is_active')
     .and_return(True))

    # expect one email to be sent in cluster 4
    (flexmock(monitor_group)
     .should_receive('send_email')
     .and_return(True)
     .once())

    monitor_group.check()
