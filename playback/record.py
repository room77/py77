"""
class to record traffic from production servers
run as script to record on one of each type of server
"""

__author__ = "Kyle Konrad"
__copyright__ = "2013, Room 77, Inc."

from pylib.hosts.host_manager import HostManager

from datetime import datetime, timedelta
from paramiko import RSAKey
import requests
from sshtail import SSHTailer

class Recorder(object):
  def __init__(self, role):
    hm = HostManager('e1b')
    servers = list(hm.get_hosts_with_ports(role))
    if not servers:
      raise ValueError('no servers with role ' + role)
    self.host, self.port = servers[0]

  def record(self, time):
    """
    record traffic on an arbitrary production server

    Arguments:
      role: use a server in this role
      time: record for this many seconds

    Yields:
      tuple of (timestamp, URL, params)
    """
    # setup
    url = 'http://%s:%s/_startrecord' % (self.host, self.port)
    response = requests.get(url)
    #print response.url, response.content
    user = 'walle'
    remote_file = '/data/output/input_playback_%d' % self.port
    key_file = '/home/share/aws/r77_aws_keypair'

    tailer = SSHTailer('%s@%s' % (user, self.host), remote_file,
                       private_key=RSAKey(filename=(key_file)))

    # main loop
    start_time = datetime.utcnow()
    lines = tailer.tail()
    end_time = datetime.utcnow() + timedelta(seconds=time)
    while datetime.utcnow() < end_time:
      for line in tailer.tail():
        if datetime.utcnow() >= end_time:
          break
        timestamp, request_url, params = line.split('\t')
        yield int(timestamp), request_url, params

    # cleanup
    tailer.disconnect()
    url = 'http://%s:%s/_stoprecord' % (self.host, self.port)
    response = requests.get(url)
    #print response.url, response.content

