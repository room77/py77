"""
Classes for sending emails
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrd <kyle@room77.com>'

from datetime import datetime

from pylib.net.util import send_email

class ThrottledMailer(object):
  """
  Send alert emails.
  Throttle the sending to allow at most one message
  every self._email_send_threshold
  """
  def __init__(self, to_email, from_email, email_send_threshold):
    """
    Args:
      email_send_threshold: timedelta
    """
    self.to_email = to_email
    self.from_email = from_email
    self._email_send_threshold = email_send_threshold
    self._email_last_sent_time = datetime(1970, 1, 1)

  def send_email(self, message, logger=None):
    """
    send an alert email if one hasn't been sent recently

    Args:
      message (string): the email body
      logger [optional] (logger object): logger to log messages to

    Returns:
      sent (bool): wheter the email was actually sent
    """
    # don't send more than once every _email_send_threshold
    if datetime.now() - self._email_last_sent_time < self._email_send_threshold:
      if logger:
        logger.info('did not send email: %s' % message)
      return False
    send_email(self.to_email, self.from_email, 'HAProxy ALARM', message)
    self._email_last_sent_time = datetime.now()
    if logger:
      logger.info('sent email: ' + message)
    return True
