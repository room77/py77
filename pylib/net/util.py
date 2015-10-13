"""
RPC util functions
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrad'

from ConfigParser import ConfigParser
import md5
import json
import os
import requests
from functools import wraps
import smtplib
from email.mime.text import MIMEText

from pylib.base.environment import IN_PRODUCTION
from pylib.file.file_utils import FileUtils

_PATH_PREFIX = 'https://room77.com' if IN_PRODUCTION else 'http://localhost'

def __get_cookie_salt():
  CONFIG_FILE = 'static_data/push/auto/credentials/web.cfg'
  config_parser = ConfigParser()
  files_read = config_parser.read(os.path.join(FileUtils.GetSrcRoot(),
                                               CONFIG_FILE))
  if not files_read:
    raise ValueError('config file not found: %s' % CONFIG_FILE)
  return config_parser.get('web', 'user_cookie_salt')

# this must match value in meta/util/method_utils.cc
__COOKIE_SALT = __get_cookie_salt()

def verify_cookie(cookie):
  """
  Verify that a Room 77 cookie is valid
  """
  try:
    r77_id, verification_code = cookie.split('%3B') # URI-encoded semicolon
  except ValueError:
    return False # no semicolon
  return verification_code == md5.new(r77_id + __COOKIE_SALT).hexdigest()[:5]

def get_r77_id(cookie):
  """
  get a Room 77 id from a cookie
  """
  try:
    r77_id, _ = cookie.split('%3B') # URI-encoded semicolon
  except ValueError:
    raise ValueError('Invalid cookie') # no semicolon
  return int(r77_id)

def web_response(request_func):
  """
  decorator that handles a response from RPC or AJAX request

  Args:
    request_func: function returning a requests.Response object
  """
  @wraps(request_func)
  def decorated(*args, **kwargs):
    response = request_func(*args, **kwargs)
    if response.status_code != 200:
      raise ValueError('request returned with status code %s' %
                       response.status_code)
    try:
      return response.json()
    except ValueError, error: # invalid JSON
      print response.text
      raise error
  return decorated

@web_response
def rpc(path, params={}, cookies={}, verify=True, retries=0, timeout=None):
  """
  perform an Room 77 RPC call over HTTP

  Args:
    path: URI of RPC (e.g. /RadiusSearch)
    params: dict of params (JSON encoded and passed as 'q' param) or string of params
    cookies: dict {cookie_name: cookie_value} of cookies to pass with request
    verify: perform SSL certificate verification
    retries: retry connection this many times
    timeout (int): how long to wait (in seconds) for a response

  Returns:
    parsed response

  Raises:
    ValueError on failed request (non 200 status) or invalid JSON response
  """
  if isinstance(params, dict):
    data = {'q': json.dumps(params)}
  else:
    data = {'q': params}
  old_retries = requests.adapters.DEFAULT_RETRIES
  requests.adapters.DEFAULT_RETRIES = retries
  ret = requests.post(_PATH_PREFIX + path, data=data,
                      cookies=cookies, verify=verify, timeout=timeout)
  requests.adapters.DEFAULT_RETRIES = old_retries
  return ret

@web_response
def ajax(path, params={}, cookies={}, verify=True):
  """
  perform an Room 77 AJAX call

  Args:
    path: URI of AJAX endpoint (e.g. /ajax/get_deals.php)
    params: dict of params
    cookies: dict {cookie_name: cookie_value} of cookies to pass with request
    verify: perform SSL certificate verification

  Returns:
    parsed JSON response

  Raises:
    ValueError on failed request (non 200 status) or invalid JSON response
  """
  return requests.get(_PATH_PREFIX + path, params=params,
                      cookies=cookies, verify=verify)

def send_email(to_address, from_address, subject, message):
  """
  send an email
  """
  msg = MIMEText(message)
  msg['To'] = to_address
  msg['From'] = from_address
  msg['Subject'] = subject
  smtp = smtplib.SMTP('localhost')
  smtp.sendmail(from_address, [to_address], msg.as_string())
  smtp.quit()

def send_alert_email(subject, message, from_address='alert@room77.com'):
  """
  send an email from alert@room77.com
  """
  send_email('alert@room77.com', from_address, subject, message)




