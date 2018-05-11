"""
class play back recordings on production servers
run as a script to play back all recordings in data directory
"""

__author__ = "Kyle Konrad"
__copyright__ = "2013, Room 77, Inc."

from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth

from pylib.base.term_color import TermColor
from pylib.util.credentials import get_username_and_password

def advance_generator_once(f):
  'decorator to advance a generator once immediately after it is created'
  def decorated(*args, **kwargs):
    gen = f(*args, **kwargs)
    assert next(gen) is None
    return gen
  return decorated

class Player(object):
  """
  Play recordings back on a staging server
  """
  def __init__(self, host, port, use_apache=True, https=False):
    self.successes = 0
    self.failures = 0
    protocol = 'https' if https else 'http'
    if use_apache:
      self.prefix = '%s://%s' % (protocol, host)
    else:
      self.prefix = '%s://%s:%d' % (protocol, host, port)

  @advance_generator_once
  def play(self):
    """
    play requests on host
    send requests using send

    Returns:
      None
    """
    username, password = get_username_and_password('beta')
    auth = HTTPBasicAuth(username, password) # authentication for beta (does nothing for hosts without authentication (e.g. titan)
    while True:
      timestamp, url, params = yield
      if url == '.ping':
        continue
      request_time = datetime.now().isoformat()
      response = requests.post('%s/%s' % (self.prefix, url),
                               data='q='+params, verify=False,
                               auth=auth, stream=False) # data must be string (not dict) to avoid double url-encoding. stream=False to prevent keep-alive connections
      if response.status_code == requests.codes.ok:
        self.successes += 1
        TermColor.PrintStr('%s %s %s' % (request_time, response.status_code, response.url),
                           'GREEN', print_trace=False)
      else:
        self.failures += 1
        TermColor.PrintStr('%s %s %s' % (request_time, response.status_code, response.url),
                           'RED', print_trace=False)
        #TermColor.PrintStr(response.content, 'RED', print_trace=False)

  @property
  def failure_rate(self):
    total = self.successes + self.failures
    return float(self.failures) / total if total else 0
