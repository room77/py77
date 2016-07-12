#!/usr/bin/env python

"""Mailer util."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2013 Room77, Inc.'


# Import smtplib for the actual sending function
import getpass
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pylib.base.term_color import TermColor


class Mailer(object):
  """Simple mailer class."""

  def __init__(self):
    self.__server = smtplib.SMTP('localhost')
    self.__server.ehlo()
    self.__max_msg_limit_in_bytes = int(self.__server.esmtp_features.get('size', 0)) - 10

  def __del__(self):
    self.__server.quit()

  def send_message(self, msg):
    """Sends a Message.

    Args:
      msg: email.message.Message: The message to send.

    Return:
      boolean: True if the mail was sent and false otherwise.
    """
    try:
      sender = msg.get('From', None)
      if not sender:
        TermColor.Error('Must specify sender: %s.' % msg)
        return False

      receivers = msg.get('To', None)
      if receivers: receivers = receivers.split()  # Split to get an array
      if not receivers:
        TermColor.Error('Must specify receivers: %s.' % msg)
        return False

      TermColor.VInfo(3, 'Sending mail: %s, %s' % (sender, receivers))
      msg_str = msg.as_string()
      if self.__max_msg_limit_in_bytes and len(msg_str) > self.__max_msg_limit_in_bytes:
        msg_str = msg_str[:self.__max_msg_limit_in_bytes] + '...'

      res = self.__server.sendmail(sender, receivers, msg_str)
      if res:
        TermColor.Error('Failed to send : %s. Errors: %s' % (msg, res))
        return False
      # All good.
      return True
    except Exception as e:  # TODO(pramodg): Make this more restricitive
      TermColor.Error('Could not send message: %s. Error: %s : %s' % (msg, type(e) , e))

  def send_simple_message(self, sender='', receivers=[], subject='Automated Mail',
                          body=''):
    """Sends a simple Message.

    Args:
      sender: string: The email id of the sender. Default = username@machinename
      receivers: list[string]: The email ids of receivers.
      subject: string: The subject for the mail.
      body: string: The body for the mail.

    Return:
      boolean: True if the mail was sent and false otherwise.
    """
    outer = self.PrepareMultipartMessage(sender, receivers, subject)
    outer.attach(MIMEText(body))
    return self.send_message(outer)

  def send_message_from_files(self, sender='',
                              receivers=[], subject='Automated Mail',
                              filenames=[], body=''):
    """Sends a message from files.

    Args:
      sender: string: The email id of the sender. Default = username@machinename
      receivers: list[string]: The email ids of receivers.
      subject: string: The subject for the mail.
      filenames: list[string]: The list of file to read to append the data.
      body: string: The body for the mail before the files are appended.

    Return:
      boolean: True if the mail was sent and false otherwise.
    """
    outer = self.PrepareMultipartMessage(sender, receivers, subject)
    outer.attach(MIMEText(body))
    for filename in filenames:
      outer.attach(MIMEText('$cat %s\n' % filename))
      try:
        with open(filename, 'r') as fp:
          outer.attach(MIMEText(fp.read()))
      except Exception as e:  # TODO(pramodg): Make this more restricitive
        err = 'Could not open file: %s. Error: %s : %s' % (filename, type(e) , e)
        TermColor.Error(err)
        outer.attach(MIMEText(err))
    return self.send_message(outer)

  @classmethod
  def PrepareMultipartMessage(cls, sender='', receivers=[],
                              subject='Automated Mail'):
    """Prepares a multipart message.

    Args:
      sender: string: The email id of the sender. Default = username@machinename
      receivers: list[string]: The email ids of receivers.
      subject: string: The subject for the mail.

    Return:
      MIMEMultipart: The multipart message.
    """
    if not sender:
      sender = ('%s+noreply@%s' % (getpass.getuser(), socket.gethostname()))

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(receivers)
    return msg
