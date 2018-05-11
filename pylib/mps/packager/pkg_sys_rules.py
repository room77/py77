#!/usr/bin/env python

"""Packager for arbitrary system package. Accepts
an optional parameter to get the package directory
into the appropriate state before pushing
"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import os
import shutil
import subprocess
import yaml

from pylib.prod.cluster.packages import Packages
from pylib.prod.packager.pkg_rules_interface import PkgRulesInterface
from pylib.prod.packager.pkg_utils import PkgUtils
from pylib.prod.packager.shared.copy_shared import CopyShared
from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils

Flags.PARSER.add_argument('--pkg_sys_ctrl_name', default='control',
                          help='name of the sys package control script')

Flags.PARSER.add_argument('--pkg_sys_ctrl_yaml_name', default='control.yaml',
                          help='name of the sys package control script')

class Error(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return "'%s'" % self.value

class PkgSysRules(PkgRulesInterface):
  """
  An overview of the various fields:
  name - the name of this package
  data - the location of the directory to import
  packager - OPTIONAL path to a binary that prepares the directory
    to import. e.g. minify some files
  control - OPTIONAL path to a control script if not already included
    in the data directory path. IF already in the data path directory,
    the control script is copied to the root
  """

  @classmethod
  def make_package(cls, rule):
    """@override"""
    name = rule['name']
    workingdir = PkgUtils.create_working_dir(name)
    if 'packager' in rule and rule['packager']:
      data_path = os.path.join(workingdir, name)
      # create the data_path directory
      subprocess.check_call('mkdir -p %s' % data_path, shell=True)
      # run the packager command to setup the package
      cmd = '%s %s' % (rule['packager'], data_path)
      ret = subprocess.call(cmd, shell=True)
      if not ret == 0:
        raise Error(TermColor.ColorStr(
          'failed to execute command %s for rule %s' % (cmd, name),
          'RED'))
    elif 'data' in rule and rule['data']:
      data_path = rule['data']
      # ensure the file exists
      if not os.path.exists(data_path):
        raise Error(TermColor.ColorStr(
          'data path does NOT exist: %s' % data_path, 'RED'))
      # cannot use -L or it will complain about non-referent symlinks
      subprocess.check_call(['/usr/bin/rsync', '-a', data_path, workingdir])
    else:
      raise Error(TermColor.ColorStr(
        'data OR packager field must be specified for rule %s' % name, 'RED'))

    # copy the control script. assume in the directory if not specified.
    # otherwise, assume rule['control'] contains the control script location
    control_path = rule['control'] if 'control' in rule \
        else os.path.join(data_path, Flags.ARGS.pkg_sys_ctrl_name)
    if not os.path.exists(control_path):
      raise Error(TermColor.ColorStr(
        'control script %s does not exist for rule %s' % \
        (control_path, name), 'RED'))
    ctrl_dest_path = os.path.join(workingdir, Flags.ARGS.pkg_sys_ctrl_name)
    shutil.copy2(control_path, ctrl_dest_path)
    os.chmod(ctrl_dest_path, 0o754)
    # copy the shared files
    CopyShared.copy(workingdir)
    # create the yaml
    ydata = {}
    ydata['name'] = name
    # the data directory in the package
    ydata['subdir'] = FileUtils.UnixBasename(data_path)
    yaml_path = os.path.join(workingdir, Flags.ARGS.pkg_sys_ctrl_yaml_name)
    with open(yaml_path, 'w') as f:
      yaml.dump(ydata, f, default_flow_style=False)
    # import the package
    packages = Packages(host=Flags.ARGS.pkg_host,
                        user=Flags.ARGS.pkg_user,
                        root=Flags.ARGS.pkg_repo)
    if Flags.ARGS.pkg_version_prefix:
      return name, packages.f_import(workingdir, name, Flags.ARGS.pkg_version_prefix)
    else:
      return name, packages.f_import(workingdir, name)
