#!/usr/bin/env python

"""Packager for data directories"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import os
import shutil
import subprocess
import yaml

from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.prod.cluster.packages import Packages
from pylib.prod.packager.pkg_rules_interface import PkgRulesInterface
from pylib.prod.packager.pkg_utils import PkgUtils
from pylib.prod.packager.shared.copy_shared import CopyShared

Flags.PARSER.add_argument('--pkg_ctrl_name', default='control',
                          help='name of the package control script')
Flags.PARSER.add_argument('--pkg_ctrl_yaml_fn',
                          default='control.yaml',
                          help='data package yaml' )
Flags.PARSER.add_argument('--pkg_ctrl_path',
                          default='prod/packager/pkg_ctrl.py',
                          help='data package controller')

class Error(Exception):
  """Triggered when there is an incorrect package definition"""
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return "'%s'" % self.value

class PkgRules(PkgRulesInterface):
  @classmethod
  def make_package(cls, rule):
    """@override"""
    name = rule['name']
    # ensure a data or file is specified
    if not 'data' in rule or \
       not rule['data'] or \
       not isinstance(rule['data'], basestring):
      err = 'invalid data field for rule %s' % name
      TermColor.Error(err)
      raise Error(err)
    data_path = rule['data']
    # ensure the file exists
    if not os.path.exists(data_path):
      err = 'data path does NOT exist: %s' % data_path
      TermColor.Error(err)
      raise Error(err)
    packages = Packages(host=Flags.ARGS.pkg_host,
                        user=Flags.ARGS.pkg_user,
                        root=Flags.ARGS.pkg_repo)
    workingdir = PkgUtils.create_working_dir(name)
    # copy the package to the working directory AND create the working directory
    # AND exclude specific invalid files
    subprocess.check_call(['/usr/bin/rsync', '-aHL', '--exclude', '*.pyc',
                           data_path, workingdir])
    # copy the control script and the control utility script
    ctrl_path = os.path.join(workingdir, Flags.ARGS.pkg_ctrl_name)
    shutil.copy2(Flags.ARGS.pkg_ctrl_path, ctrl_path)
    os.chmod(ctrl_path, 0754)
    # the shared control utility scripts
    CopyShared.copy(workingdir)
    # create the yaml definition for the control script
    cls._write_control_yaml(name, data_path, workingdir)
    # import the package
    if Flags.ARGS.pkg_version_prefix:
      return name, packages.f_import(workingdir, name,
                                     Flags.ARGS.pkg_version_prefix)
    else:
      return name, packages.f_import(workingdir, name)

  @classmethod
  def _extract_basename(cls, path):
    """Returns the basename of the path"""
    # remove the trailing slash
    if path[-1:] == "/":
      path = path[0:-1]
    return os.path.split(path)[1]

  @classmethod
  def _write_control_yaml(cls, name, data_path, workingdir):
    """Writes the yaml for the control script"""
    yaml_data = {}
    yaml_data['name'] = name
    yaml_data['syms'] = {}
    # map from the file that needs to be symlinked to the symlink location
    yaml_data['syms'][cls._extract_basename(data_path)] = data_path
    yaml_path = os.path.join(workingdir, Flags.ARGS.pkg_ctrl_yaml_fn)
    with open(yaml_path, 'w') as f:
      yaml.dump(yaml_data, f, default_flow_style=False)
