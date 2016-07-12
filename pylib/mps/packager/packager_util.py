#!/usr/bin/env python

"""
Utility functions for packaging
"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import subprocess
import os
import random
import time
import yaml

from pylib.prod.cluster.packages import Packages
from pylib.util.git_util import GitUtil

class Error(Exception):
  """The exception class for PackagerUtil"""
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)

class PackagerUtil(object):
  """A set of utility functions for building packages"""

  @classmethod
  def make_packages(cls, packages):
    """builds a sets of package rules and returns the dict from package
    name to package version
    Args:
      packages (list) - list of package rules to build
    Returns:
      dict from package name to package version
    Raises:
      Error - one or more of the packages could not be created
    """
    pkg_prefix = Packages.get_valid_package_prefix(
      GitUtil.get_latest_commit()[0:6])
    tmp_fn = '%d_%d' % (int(time.time()), random.randint(1, 1e5))
    cmd = 'flash --pkg_version_prefix=%s --pkg_version_path=%s run %s' % \
          (pkg_prefix, tmp_fn, ' '.join(packages))
    process = subprocess.Popen(['/bin/bash', '-c', cmd])
    process.wait()
    if not process.returncode == 0:
      if os.path.exists(tmp_fn):
        # delete the temporary package file if it exists
        os.remove(tmp_fn)
      raise Error('one of more of the packages cannot be created')
    # construct the release yaml from the temp package list
    packages = {}
    with open(tmp_fn, 'r') as f:
      packages = yaml.safe_load(f)
    os.remove(tmp_fn)  # delete the temporary package file
    return packages
