#!/usr/bin/env python

"""Packager for server binaries"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import os
import shutil
import subprocess

from pylib.prod.cluster.packages import Packages
from pylib.prod.packager.pkg_rules_interface import PkgRulesInterface
from pylib.prod.packager.pkg_utils import PkgUtils
from pylib.prod.packager.shared.copy_shared import CopyShared
from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils

Flags.PARSER.add_argument('--loop_script_path', default='scripts/loop',
                          help='location of the loop script')

Flags.PARSER.add_argument('--pkg_bin_ctrl_path',
                          default='prod/config/bin/pkg_bin_ctrl.py',
                          help='location of the pkg binary control script')

class Error(Exception):
  """Triggered when there is an incorrect package bin definition"""
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)

class PkgBinRules(PkgRulesInterface):

  @classmethod
  def make_package(cls, rule):
    """@override"""
    name = rule['name']
    if not 'rule' in rule or not rule['rule']:
      err = 'no rule field for %s' % name
      TermColor.Error(err)
      raise Error(err)
    if not 'ctrl' in rule or not rule['ctrl']:
      err = 'no yaml ctrl field for %s' % name
      TermColor.Error(err)
      raise Error(err)
    subprocess.check_call('flash build %s' % rule['rule'], shell=True)
    # clean up the old package and create the working directory
    workingdir = PkgUtils.create_working_dir(name)
    # collect the files
    files = {}
    # the binary path
    files[os.path.join(FileUtils.GetBinDir(), rule['rule'])] = \
      os.path.basename(rule['rule'])
    # the loop script
    files[os.path.join(FileUtils.GetSrcRoot(),
                       Flags.ARGS.loop_script_path)] = 'loop'
    # the control script
    files[os.path.join(FileUtils.GetSrcRoot(),
                       Flags.ARGS.pkg_bin_ctrl_path)] = 'control'
    # the yaml file
    files[os.path.join(FileUtils.GetSrcRoot(),
                       rule['ctrl'])] = 'control.yaml'
    # copy the files
    for src, dest in files.items():
      shutil.copy2(src, os.path.join(workingdir, dest))
    # copy the shared files
    CopyShared.copy(workingdir)
    # import the package
    packages = Packages(host=Flags.ARGS.pkg_host,
                        user=Flags.ARGS.pkg_user,
                        root=Flags.ARGS.pkg_repo)
    # import the package
    if Flags.ARGS.pkg_version_prefix:
      return name, packages.f_import(workingdir, name,
                                     Flags.ARGS.pkg_version_prefix)
    else:
      return name, packages.f_import(workingdir, name)
