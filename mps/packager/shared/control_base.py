#!/usr/bin/env python

"""
Base class for control script. Nearly every control script inherits
from this class. This class provides shared utility functionality
used by many classes
is included with nearly every control script, so be sure to keep this
lightweight.
"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room 77, Inc.'

import argparse
import os
import subprocess
import time
import yaml

class Error(Exception):
  """Triggered when there is an error in these base class functions"""
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return "'%s'" % self.value

class ControlBase(object):
  _parser = argparse.ArgumentParser(description='Data control script')
  _subparsers = _parser.add_subparsers(help='commands')
  _subparsers.add_parser('setlive').set_defaults(func='setlive')
  _subparsers.add_parser('start').set_defaults(func='start')
  _subparsers.add_parser('stop').set_defaults(func='stop')
  _subparsers.add_parser('status').set_defaults(func='status')
  # the filename to read the package specific config
  _yaml_fn = 'control.yaml'
  # the config read in by the yaml
  _config = {}
  # file that exists if the machine is in produciton
  _prod_file = '/home/config/prod_machine'

  def __init__(self):
    """
    reads in the yaml config file to initialize the class,
    parses the command line arguments
    """
    self._load_config(self._yaml_fn)
    # parse the arguments
    self._args = self._parser.parse_args()

  def run(self):
    """calls the proper command specified by the command
    line arguments: e.g. start, stop, etc"""
    getattr(self, self._args.func)()

  #
  # the primary function called externally. start, stop, setlive, status
  # This SHOULD be overwritten by the subclass
  #

  def setlive(self):
    """Prepares the package to be started. Sets appropriate symlinks
    and installs the appropriate system packages"""
    pass

  def start(self):
    """Called to start the package"""
    pass

  def status(self):
    """Prints a status string for the package"""
    pass

  def stop(self):
    """Stops the package if necessary and performs any cleanup"""
    pass

  #
  # Utility functions
  #

  def _create_link(self, src, link, sudo=False):
    """Creates the symlink to src.
    Raises:
      Error: error creating a symlink
    """
    # non-absolute path links are converted to absolute
    # paths starting from ~
    if not os.path.isabs(link):
      link = os.path.expanduser(os.path.join('~', link))
    # create the parent directory of the link if necessary
    link_dir = os.path.dirname(link)
    if not os.path.exists(link_dir):
      if os.path.lexists(link_dir):
        os.remove(link_dir)
      os.makedirs(link_dir)

    if not os.path.exists(link) and not os.path.lexists(link):
      cmd = ['ln', '-s', src, link]
      if sudo:
        cmd = ['sudo'] + cmd
      subprocess.check_call(cmd)
    elif os.path.lexists(link):
      # if the location is NOT a link, delete the directory
      if not os.path.islink(link):
        sudo_cmd = 'sudo' if sudo else ''
        subprocess.check_call('%s rm -rf %s' % (sudo_cmd, link), shell=True)
      tmploc = '/tmp/%s_%d' % (self._extract_basename(link), int(time.time()))
      os.symlink(src, tmploc)
      cmd = ['/bin/mv', '-Tf', tmploc, os.path.abspath(link)]
      if sudo:
        cmd = ['sudo'] + cmd
      subprocess.check_call(cmd)
    else:
      err = 'Cannot create symlink to %s. Already a file or directory' % link
      raise Error(err)

  def _extract_basename(self, path):
    """Returns the basename of the path in the unix basename convention"""
    # remove the trailing slash
    if path[-1:] == "/":
      path = path[0:-1]
    return os.path.split(path)[1]

  def _get_setlive_dir(self, file):
    """
    Get the directory to setlive. If the script is run on production,
    current MUST be pointing to the current version directory. On dev,
    this may return the version directory to simplify testing
    Args:
      file - the __file__ attribute for the caller
    Returns:
      the setlive directory with any symlink expansion along the path
    Raises:
      Error - on production when setlive is trying to be called but
        the current symlink does NOT point to this version directory
    """
    version_dir = os.path.dirname(file)
    if not os.path.isabs(version_dir):
      # get logical pwd. os.getcwd returns os.realpath(pwd)
      # do NOT want /home/share/repo symlink to be expanded to the
      # actual path (e.g. /home/share/repo links to /mnt/no_backup, but
      # don't want it to expand to /mnt/no_backup)
      pwd = subprocess.check_output('pwd', shell=True).strip('\n')
      version_dir = os.path.normpath(os.path.join(pwd, version_dir))
    setlive_dir = os.path.join(os.path.dirname(version_dir), 'current')
    if not os.path.exists(setlive_dir):
      # if current does not exist, raise an error on prod, but set to the
      # version directory on dev
      if self._is_production():
        raise Error(
          'no current directory %s exists. something is wrong!' % setlive_dir)
      else:
        setlive_dir = version_dir
    else:
      # if current points to a different directory from the currently running
      # version AND we are not in the current directory, raise an error on prod,
      # but set to the version dir on dev
      setlive_link = os.readlink(setlive_dir)
      if not os.path.basename(version_dir) == 'current' and \
         not os.path.basename(version_dir) == os.path.basename(setlive_link):
        if self._is_production():
          raise Error(
            ('the current link points to %s but the control script is running '
             'out of %s') % (
            os.path.basename(setlive_link), os.path.basename(version_dir)))
        else:
          setlive_dir = version_dir
    return setlive_dir


  def _is_production(self):
    return os.path.exists(self._prod_file)

  def _load_config(self, name):
    """loads the yaml config file and saves the contents
    to self._config
    Args:
      name - the name of the yaml config file
    Raises:
      Error - cannot load the control script yaml config
    """
    fn = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                      name)
    if not os.path.exists(fn):
      raise Error('cannot find file %s' % fn)
    with open(fn, 'r') as f:
      self._config = yaml.safe_load(f)
