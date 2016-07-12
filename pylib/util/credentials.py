"""
Utility functions for managing credentials
"""

__author__ = 'Kyle Konrad <kyle@room77.com>'
__copyright__ = '2014, Room 77, Inc.'

from ConfigParser import ConfigParser
import os

from pylib.file.file_utils import FileUtils

def get_username_and_password(service, section=None,
                              dir='static_data/push/auto/credentials'):
  """
  Parse config file named `service`.cfg in dir.

  Args:
    service (string): Name of service to get credentials for. This should match
      a file in dir (with .cfg extension)
    section (string): section of config file to use. Defaults to same as
      `service`
    dir (stirng): directory (relative to source root) to look in for config file.

  Returns:
    (username, password) for the requested service

  Raises:
    ValueError if file does not exist
    ConfigParser.NoSectionError if section does not exist
    ConfigParser.NoOptionError if username or password is
      not in the requested section
  """
  config_parser = ConfigParser()
  files_read = config_parser.read(os.path.join(FileUtils.GetSrcRoot(), dir, '%s.cfg' % service))
  if not files_read:
    raise ValueError('No config file found for %s in %s' % (service, dir))
  username = config_parser.get(section or service, 'username')
  password = config_parser.get(section or service, 'password')
  return username, password
