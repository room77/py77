#!/usr/bin/env python

"""Handles build."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import os
import sys

import r77_init  # pylint: disable=W0611
from pylib.base.flags import Flags
from pylib.file.file_utils import FileUtils
from pylib.base.term_color import TermColor

from cc_rules import CCRules
from cmd_handler import CmdHandler
from gen_makefile import GenMakefile
from pkg_rules import PkgRules
from ng_rules import NGRules
from nge2e_rules import NGe2eRules
from js_rules import JSRules
from py_rules import PyRules
from swig_rules import SwigRules
from rules import Rules
from utils import Utils


class Builder(CmdHandler):
  """Class to handle build."""

  @classmethod
  def WorkHorse(cls, rules):
    """Runs the workhorse for the command.

    Args:
      rules: list: List of rules to be handled.

    Return:
      (list, list): Returns a tuple of list in the form
          (successful_rules, failed_rules) specifying rules that succeeded and
          ones that failed.
    """
    # Create the user friendly link to bin dir if it doesn't already exist.
    FileUtils.CreateLink(FileUtils.GetEDir(), FileUtils.GetBinDir())
    # Create the link to the web test directory if it exists
    if os.path.exists(FileUtils.GetWebTestHtmlLink()):
      FileUtils.CreateLink(FileUtils.GetWebTestHtmlLink(),
                           FileUtils.GetWebTestHtmlDir())

    gen_makefile = GenMakefile(Flags.ARGS.debug)
    gen_makefile.GenMainMakeFile()
    (success_genmake, failed_genmake) = gen_makefile.GenAutoMakeFileFromRules(
        rules, Flags.ARGS.allowed_rule_types)

    (success_make, failed_make) = cls._MakeRules(
        success_genmake, gen_makefile.GetMakeFileName())

    return (success_make, failed_genmake + failed_make)

  @classmethod
  def _CreateLink(cls, linkdir, dir):
    """
    Creates a link to the build or template directories if it does
    not already exist OR if it is invalid. AND creates the directory
    Args:
      linkdir: string: the location to create the link
      dir: string: the location where the buildfiles or template are stored
    """
    if not os.path.exists(dir):
      os.makedirs(dir)
    if not os.path.exists(linkdir):
      if os.path.lexists(linkdir):
        os.remove(linkdir)
      os.symlink(dir, linkdir)

  @classmethod
  def _MakeRules(cls, rules, makefile):
    """Makes all the rules in the give list.

    Args:
      rules: dict: Dict of rules by type_base to make.
      gen_makefile: GenMakefile: The genmakefile object that manages all
          makefile data.

    Return:
      (list, list): Returns a tuple of list in the form
          (successful_rules, failed_rules) specifying rules for which the make
          rules were successfully generated and for which it failed.
    """
    if not rules:
      TermColor.Warning('No rules to build.')
      return ([], [])

    rules_map = {'cc': CCRules,
                 'js': JSRules,
                 'ng': NGRules,
                 'nge2e': NGe2eRules,
                 'pkg': PkgRules,
                 'py': PyRules,
                 'swig': SwigRules}

    # Build the rules for each rule type.
    successful_rules = []; failed_rules = []
    for (k, v) in rules.items():
      (s, f) = ([], [])
      try:
        (s, f) = rules_map[k].MakeRules(v, makefile)
      except KeyError:
        TermColor.Error('Make for %s not supported' % k)
        failed_rules += v
        continue
      successful_rules += s
      failed_rules += f

    return (successful_rules, failed_rules)


def main():
  try:
    Builder.Init(Flags.PARSER)
    Flags.InitArgs()
    return Builder.Run()
  except KeyboardInterrupt as e:
    TermColor.Warning('KeyboardInterrupt')
    return 1


if __name__ == '__main__':
  sys.exit(main())
