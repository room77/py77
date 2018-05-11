#!/usr/bin/env python

"""
Centralized class for updating the releases and the deployspecs files.
These files should ONLY be updated through this class, because this class
handles all the fancy locking necessary to avoid conflicts
"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import os

from pylib.base.flags import Flags
from pylib.base.exec_utils import ExecUtils
from pylib.util.git_util import GitUtil

Flags.PARSER.add_argument('--queue_config_host', default='titan',
                          help='default host to run the queue config command')
Flags.PARSER.add_argument('--queue_config_repo',
                          default='/home/r77/src/mps_dev',
                          help='default host to run the queue config command')
Flags.PARSER.add_argument('--queue_config_user', default='r77',
                          help='default user to run the queue config command')

class Error(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return "'%s'" % self.value

class QueueClusterConfigUpdates(object):
  BIN_NAME = 'prod/update_config'
  # implemented with flock. if the flock process is killed uncleanly,
  # this file *may* need to be deleted manually on r77@titan
  MPS_LOCK_FILE = '/run/lock/mps'

  @classmethod
  def update_deployspec(cls, name, cluster, release_name):
    """
    Args:
      name (string) - the name of this deployspec
      cluster (string) - the name of the cluster
      release_name (string) - the name of this release
    """
    cmd = '%s --required_user=%s %s deployspecs %s %s %s' % (
      cls.BIN_NAME, Flags.ARGS.queue_config_user,
      GitUtil.get_current_branch(), name, cluster, release_name)
    cls._run_locked_update(cmd)

  @classmethod
  def update_release(cls, name, release_pkgs):
    """
    Args:
      name (string) - the name of this release
      release (dict) - dict from package name to package version name
    """
    pkgs_str = ''
    for pkg_name, pkg_ver in release_pkgs.items():
      pkgs_str += '%s %s ' % (pkg_name, pkg_ver)
    cmd = '%s --verbose --required_user=%s %s releases %s %s' % (
      cls.BIN_NAME, Flags.ARGS.queue_config_user,
      GitUtil.get_current_branch(), name, pkgs_str)
    cls._run_locked_update(cmd)

  @classmethod
  def _run_locked_update(cls, cmd):
    """
    Runs the command on the remote machine
    Args:
      cmd (string) - the command to run
    Raises:
      Error - the command fails to run
    """
    remote_cmd = 'ssh %s@%s "flock %s -c \'echo %d > %s && cd %s && git pull && %s\'"' % (
      Flags.ARGS.queue_config_user, Flags.ARGS.queue_config_host,
      cls.MPS_LOCK_FILE, os.getpid(), cls.MPS_LOCK_FILE,
      Flags.ARGS.queue_config_repo, cmd)
    print("running locked update with cmd: %s" % remote_cmd)
    if ExecUtils.RunCmd(remote_cmd)[0]:
      raise Error('mps system failed to update for command: %s' % remote_cmd)

