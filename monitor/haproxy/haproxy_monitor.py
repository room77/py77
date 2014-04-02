"""
Monitor servers through HAProxy

A monitor can be configured to check a different set of
  conditions for each service

Configuration happens through the final ctor parameter, which is a dictionary
  where the key is a regex used to match the service name
  and the value is a list of conditions
  where a condition is a callable which takes a ProxyStats object and
  returns an error message or None

Example configuration:
  {
    'nginx': {'http-apache$': [more_than_proportion_down(.499)]},
    'newprod_apache': {
      '': [
        more_than_proportion_down(.999),
        any_down_longer_than(timedelta(minutes=30))
        ],
      '^meta-http': [more_than_n_down(2)]}
  }

  monitors HAProxy instances on nginx maches and sends an alert if
    half or more of the apache servers are down
  monitors HAProxy instances newprod_apache and sends an alert if
    all of any server_type are down
    more than 2 meta search servers are down
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrad <kyle@room77.com>'

from collections import defaultdict
import csv
from datetime import datetime, timedelta
import logging
import re
import urllib

import r77_init  # pylint: disable=W0611
from pylib.net.mailer import ThrottledMailer

DATE_FORMAT = '%Y%m%d|%H%M%S'
LOG_FORMAT = '%(asctime)s %(pathname)s:%(lineno)d: %(message)s'
logging.basicConfig(format=LOG_FORMAT, datefmt=DATE_FORMAT)
logger = logging.getLogger('haproxy_monitor')
logger.setLevel(logging.INFO)

class ProxyStats(object):
  """
  Statisitics of a proxy
  """
  def __init__(self, name, up_count, down_count, last_up_times):
    self.name = name
    self.up_count = up_count
    self.down_count = down_count
    self.last_up_times = last_up_times

class ProxyStatsCollection(defaultdict):
  def __missing__(self, key):
    ret = self[key] = ProxyStats(key, 0, 0, {})
    return ret

class HAProxyMonitor(ThrottledMailer):
  """
  Monitor stats from an HAProxy instance
  """
  def __init__(self, url, username, password, email, conditions):
    """
    Args:
      url (string): url of HAProxyStats
      username (string): username for http basic auth for above url
      password (string): password for http basic auth for above url
      email (string): email to send alerts to
      conditions ({regex: [conditions]}): conditions to check for each proxy.
        Each condition is a callable that returns an error message or None
    """
    super(HAProxyMonitor, self).__init__(email, email, timedelta(seconds=60))
    self.url = url
    self.username = username
    self.password = password
    self.email = email
    self.conditions = conditions
    self.stats = ProxyStatsCollection(ProxyStats)

  def reset(self):
    """
    reset stats
    """
    self.stats.clear()

  def check(self):
    self.reset()
    self.parse_status(self.get_status())
    return self.alert()

  def get_status(self):
    """
    Returns:
      status (string): csv with all status info

    Raises:
      IOError: if HAProxy is unreachable
    """
    protocol, path = self.url.split('://')
    tar_url = '%s://%s:%s@%s' % (protocol or 'http', self.username, self.password, path)
    return urllib.urlopen(tar_url).read()

  def parse_status(self, status_csv):
    """
    Args:
      status_csv (string): csv of all status info

    Returns:
      None
      Outputs stats to self.stats
    """
    # field indices
    PXNAME = 0  # proxy name
    SVNAME = 1  # service name
    STATUS = 17 # status
    LASTCHG = 23 # seconds since last change in status
    HRSP_5XX = 43 # HTTP 5xx response count

    # [:-1] for trailing newline
    reader = csv.reader([row for row in status_csv.split('\n')][:-1], delimiter=',')

    # check that field indices are correct
    headers = reader.next()
    assert headers[PXNAME] == '# pxname'
    assert headers[SVNAME] == 'svname'
    assert headers[STATUS] == 'status'
    assert headers[LASTCHG] == 'lastchg'
    assert headers[HRSP_5XX] == 'hrsp_5xx'

    for fields in reader:
      proxy_name = fields[PXNAME]
      server_name = fields[SVNAME]
      if server_name == 'FRONTEND' or server_name == 'BACKEND':
        continue
      status = fields[STATUS]
      status_first_word = status.split()[0] if status else ''
      if status_first_word == 'UP':
        self.stats[proxy_name].up_count += 1
        self.stats[proxy_name].last_up_times[server_name] = datetime.utcnow()
      elif status_first_word == 'DOWN':
        self.stats[proxy_name].down_count += 1
      elif status == 'no check':
        pass
      else:
        logger.error('unknown status for %s - %s: %s', (proxy_name, server_name, status));

  def alert(self):
    all_passed = True
    for name_regex, conditions in self.conditions.items():
      matches = 0
      for name, stats in self.stats.items():
        if re.search(name_regex, name):
          matches += 1
          for condition in conditions:
            message = condition(stats)
            if message:
              all_passed = False
              if (stats.down_count + stats.up_count == 1):
                self.send_email(message + """. Please note that this instance is a singleton and
                that if you just manually restarted the cluster, it is expected to go down.
                Keep monitoring your email and if you stop receiving them when the cluster goes up,
                you can safely ignore this warning. Otherwise please refer to the document
                https://docs.google.com/a/room77.com/document/d/1Ii1cxpIucAU3Qb63Zv3Cc-Ymf9WX6a945guZ_Cg01NI/edit#heading=h.7pw52dk9gnzc""")
              else:
                self.send_email(message + """. Please refer to the document
                https://docs.google.com/a/room77.com/document/d/1Ii1cxpIucAU3Qb63Zv3Cc-Ymf9WX6a945guZ_Cg01NI/edit#heading=h.7pw52dk9gnzc """, logger)
      logger.debug('"%s" matched %d proxies' % (name_regex, matches))
      if not matches:
        self.send_email('No proxies found matching regex: %s\n%r' % (
          name_regex, self.stats),
                        logger)
    if all_passed:
      logger.info('All checks passed on %s' % self.url) # sanity check message
    return all_passed

