#!/usr/bin/env python

"""
Monitoring server

Currently monitors stats from HAProxy on
nginx and apache prod clusters

Sends alarm emails if conditions are not met
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrad <kyle@room77.com>'

from datetime import timedelta
import logging
import sys
import threading

import r77_init  # pylint: disable=W0611
from pylib.base.flags import Flags
from pylib.net.server import Server

from pylib.monitor.haproxy.haproxy_cluster_monitor_group import (
  HAProxyClusterMonitorGroup)
from pylib.monitor.haproxy.conditions import (more_than_n_down,
                                              more_than_proportion_down,
                                              any_down_longer_than)
from pylib.util.credentials import get_username_and_password

# constants
PORT = 10011

# logging config
logger = logging.getLogger('haproxy_monitor')

# global server object
server = Server('monitor', PORT)

def cluster_conditions():
  """
  define monitor config here

  format is {cluster: {proxy_regex: [conditions]}
  """
  apache_conditions = {
    '': [
          more_than_proportion_down(.999),
          any_down_longer_than(timedelta(minutes=30))
        ],
    '^meta-http': [more_than_n_down(2)],
  }
  return {
    'prod_apache': apache_conditions,
  }

def loop():
  from time import sleep
  import threading
  # names of clusters to monitor
  USERNAME, PASSWORD = get_username_and_password('haproxy')

  monitor_group = HAProxyClusterMonitorGroup.create_from_conditions(
    USERNAME, PASSWORD, Flags.ARGS.alert_email, cluster_conditions())

  while True:
    monitor_group.check()
    sleep(Flags.ARGS.sleep_interval)


# this must be called after method definitions
server.configure()

Flags.PARSER.add_argument('--sleep_interval', type=int, default=5,
                          help='sleep interval between checks in seconds')

Flags.PARSER.add_argument('--alert_email', type=str, default='critical-alerts@room77.com',
                          help='email address to send alert messages to')

if __name__ == '__main__':
  Flags.InitArgs()

  # start the monitor loop
  # make it a daemon thread to make shutdown work correctly
  t = threading.Thread(target=loop)
  t.daemon = True
  t.start()

  # need to remove all args before starting server because gunicorn
  # will freak out if it sees unknown arguments
  sys.argv = sys.argv[:1]
  server.run()
