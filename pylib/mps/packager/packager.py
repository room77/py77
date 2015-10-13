#!/usr/bin/env python

"""Main file that handles different packaging operations."""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import argparse
import getpass
import os
from string import Template
import sys
import time
import yaml

import r77_init # pylint: disable=W0611
from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils
from pylib.flash.rules import Rules
from pylib.flash.utils import Utils
from pylib.util.git_util import GitUtil
from pylib.prod.cluster.packages import Packages
from pylib.prod.packager.pkg_rules import PkgRules
from pylib.prod.packager.pkg_bin_rules import PkgBinRules
from pylib.prod.packager.pkg_sys_rules import PkgSysRules

Flags.PARSER.add_argument('rule', help='the build rule')
Flags.PARSER.add_argument('--pkg_host', default='titan',
                          help='default host to push packages')
Flags.PARSER.add_argument('--pkg_repo', default='/home/share/repo',
                          help='default repo to push packages')
Flags.PARSER.add_argument('--pkg_user', default='r77',
                          help='default user to own packages')
Flags.PARSER.add_argument('--pkg_version_path', default='',
                          help='the file to APPEND the package versions')
Flags.PARSER.add_argument('--pkg_version_prefix', default='',
                          help='the package name. to generate a valid' + \
                               'name use Packages.get_valid_package_prefix')

class UnsupportedRuleError(Exception):
  """Triggered when the user tries to package an unsupported rule"""
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)

class Packager(object):
  """Main class to handle all the packaging commands"""
  RULE_PACKAGER = {'pkg': PkgRules,
                   'pkg_bin': PkgBinRules,
                   'pkg_sys': PkgSysRules}

  def run(self):
    """build and create the package
    Returns:
      tuple(string, string) the package name followed by the
      package version name
    """
    if not Flags.ARGS.pkg_version_prefix:
      Flags.ARGS.pkg_version_prefix = Packages.get_valid_package_prefix(
        GitUtil.get_latest_commit()[0:6])

    version = self._packager.make_package(self._rule)
    if Flags.ARGS.pkg_version_path:
      with open(Flags.ARGS.pkg_version_path, 'a') as f:
        config = {}
        config[version[0]] = version[1]
        f.write('%s' % yaml.safe_dump(config, default_flow_style=False))
    return version

  def __init__(self, rule_name):
    """initializes the state
    Args:
      rule_name (string) - the rule name
    Raises:
      UnsupportedRuleError: raises exception if the rule type is not yet
        supported. add to the RULE_TYPES lists
    """
    # Create the user friendly link to bin dir if it doesn't already exist.
    FileUtils.CreateLink(FileUtils.GetEDir(), FileUtils.GetBinDir())
    rule_name = Utils.RuleNormalizedName(rule_name)
    Rules.LoadRule(rule_name)
    self._rule = Rules.GetRule(rule_name)
    if not self._rule['_type'] in Packager.RULE_PACKAGER:
      err = 'Rule type %s not supported' % self._rule._type
      TermColor.Error(err)
      raise UnsupportedRuleError(err)
    self._packager = Packager.RULE_PACKAGER[self._rule['_type']]

if __name__ == '__main__':
  # some external modules require the flags
  Flags.InitArgs()
  packager = Packager(Flags.ARGS.rule)
  packager.run()
