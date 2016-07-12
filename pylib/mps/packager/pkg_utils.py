#!/usr/bin/env python

"""Util functions for packaging"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import os
import shutil

from pylib.file.file_utils import FileUtils

class PkgUtils(object):
  @classmethod
  def create_working_dir(cls, name):
    """Delete old temporary files AND create the working directory
    Args:
      name (string) : the package name
    Returns:
      the working directory to use
    """
    workingdir = os.path.join(FileUtils.GetBinDir(), 'package', '%s' % name)
    # clean up the old package if necessary
    if os.path.isdir(workingdir):
      shutil.rmtree(workingdir)
    os.makedirs(workingdir)
    return workingdir
