"""
Monitor clusters through HAProxy

An HAProxyClusterMonitorGroup monitors multiple clusters.
For each cluster, HAProxy instances on each host in the cluster are monitored

Alerts are triggered if
  any of the individual monitors triggers an alert
    OR
  more than half of the haproxy instances in a cluster are unreachable
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrad <kyle@room77.com>'

from datetime import timedelta
from itertools import chain
import logging
import os.path
import urllib

from .haproxy_monitor import HAProxyMonitor
from .conditions import (more_than_n_down, more_than_proportion_down,
                         any_down_longer_than)

import r77_init  # pylint: disable=W0611
from prod.cluster.cluster import Cluster
from pylib.file.file_utils import FileUtils
from pylib.net.mailer import ThrottledMailer

# logging config
logger = logging.getLogger('haproxy_monitor')

class HAProxyClusterMonitorGroup(ThrottledMailer):
  """
  A collection of HAProxy monitors grouped by cluster
  """
  def __init__(self, email, cluster_monitors):
    """
    Args:
     cluster_monitors ({cluster: [monitors]}): monitors grouped by cluster
    """
    super(HAProxyClusterMonitorGroup, self).__init__(email, email,
                                                     timedelta(seconds=60))
    self.cluster_monitors = cluster_monitors

  @classmethod
  def clusters(cls):
    src_root = FileUtils.GetSrcRoot()
    return Cluster.create(
      local_root=src_root,
      # We have to specify the full path for conf files
      # in case we are running through PyInstaller (i.e. with flash)
      conf_dir=os.path.join(src_root, 'prod/cluster/conf'))

  @classmethod
  def create_from_conditions(cls, username, password, email,
                             cluster_conditions, port=10055,
                             path='/haproxy?stats;csv;norefresh'):
    """
    Factory method to create monitor group based on current cluster config

    Args:
      url (string): url of HAProxyStats
      username (string): username for http basic auth for above url
      password (string): password for http basic auth for above url
      email (string): email to send alerts to
      cluster_conditions ({cluster: {regex: [conditions]}}): conditions to
        check for each proxy. Each condition is a callable that returns
        an error message or None
    """
    clusters = cls.clusters()
    monitors = {} # cluster name -> [monitor for each host]
    for cluster_name, conditions in cluster_conditions.items():
      hosts = clusters.get_hosts(chain.from_iterable(
        [item['hosts'] for item in clusters.clusters[cluster_name]['data']
         if not item.get('external', False)]))
      monitors[cluster_name] = [HAProxyMonitor(
        'http://%s:%d%s' % (host, port, path),
        username, password, email, conditions)
                                for host in hosts]
    return HAProxyClusterMonitorGroup(email, monitors)

  @classmethod
  def is_active(cls, cluster_name):
    return cls.clusters().clusters[cluster_name].get('active', True)

  def check(self):
    """
    run a check on a monitor in each cluster until one succeeds

    the group logic is a little weird:
    for each cluster:
      if the first monitor is reachable
        we are done
      else
        check all monitors for this cluster
        if more than half are unreachable
          send alert email
    """
    # reread conf file every time so we can see changes
    success = True
    for cluster_name, monitors in self.cluster_monitors.items():
      if self.is_active(cluster_name):
        unreachable = 0
        for monitor in monitors:
          try:
            success = monitor.check()
          except IOError:
            try:
              # check the network connection
              urllib.urlopen('http://google.com')
            except IOError:
              logger.log('no network connection')
            else:
              unreachable += 1
              logger.error('Failed to get %s' % monitor.url)

          # we've tried at least one monitor by this point
          # if it was reachable (or the netowrk is down) so
          # we don't want to check any more monitors
          if unreachable == 0:
            break

        if unreachable >= (len(monitors) + 1) // 2:
          sent = self.send_email('More than half of HAProxy instances are'
                                 'unreachable on %s' % cluster_name + ". Please refer to doc https://docs.google.com/a/room77.com/document/d/1Ii1cxpIucAU3Qb63Zv3Cc-Ymf9WX6a945guZ_Cg01NI/edit#heading=h.7pw52dk9gnzc", logger)
          success = False
    return success
