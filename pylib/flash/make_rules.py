
"""Generic base class for rules using make files."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import itertools
import multiprocessing
import os
import shutil
import time

from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.base.exec_utils import ExecUtils
from pylib.file.file_utils import FileUtils

from utils import Utils


class MakeRules(object):
  """Base class for rules using make files."""

  @staticmethod
  def GetDepsFileName(makefile, target, replace_str):
    """Returns the deps file name unique to individual target.

    Args:
      makefile: string: The original makefile name.
      target: string: The target for which the deps file is to be generated.
      replace_str: string: The string replaced in the makefile name to figure
          out the right deps file name.

    Return:
      string: The name of the deps file.
    """
    if not target: return None
    return  makefile.replace(replace_str, target.replace('/', '.') + '.dep.')

  @classmethod
  def WriteMakefile(cls, specs, makefile):
    """Writes the auto make file for the given spec. All derived classes must
    implement this method.

    Args:
      specs: List of dict of type {target, target_type, src, hdr, flag, link, pack}.
        In each dict, 'src', 'hdr' 'flag' and 'link' contain everything needed to
        build 'target'
      makefile: The (auto) makefile to generate.
    """
    TermColor.Fatal('Not supported!')

  @classmethod
  def MakeRules(cls, rules, makefile):
    """Makes all the rules in the give list.

    Args:
      rules: list: List of rules by type_base to make.
      makefile: string: The *main* makefile name.

    Return:
      (list, list): Returns a tuple of list in the form
          (successful_rules, failed_rules) specifying rules for which the make
           rules were successfully generated and for which it failed.
    """
    if not rules:
      TermColor.Warning('No rules to build.')
      return ([], rules)

    args = itertools.izip(itertools.repeat(cls), itertools.repeat('_WorkHorse'),
                          rules, itertools.repeat(makefile))
    rule_res = ExecUtils.ExecuteParallel(args, Flags.ARGS.pool_size)
    successful_rules = []; failed_rules = []
    for (res, rule) in rule_res:
      if res == 1:
        successful_rules += [rule]
      elif res == -1:
        failed_rules += [rule]

    return (successful_rules, failed_rules)

  @classmethod
  def _WorkHorse(cls, rule, makefile):
    """Workhorse for building a single rule.
    Args:
      rule: string: The rule to build.
      makefile: string: The *main* makefile name.

    Return:
      (int, string): Returns a tuple of the result status and the rule.
          The status is '1' for success, '0' for 'ignore', '-1' for fail.
    """
    start = time.time()
    ignore = Utils.IgnoreRule(rule, Flags.ARGS.ignore_rules)
    if ignore:
      TermColor.Warning('Ignored targets in %s as anything with [%s] is ignored' %
                        (Utils.RuleDisplayName(rule), ignore))
      return (0, rule)

    TermColor.Info('Building %s' % Utils.RuleDisplayName(rule))

    deps_file = cls.GetDepsFileName(makefile, rule, '.main.')
    try:
      shutil.copy(makefile, deps_file)
      cls._PrepareDepsFile(rule, deps_file)
    except (OSError, IOError), e:
      TermColor.Error('Could not create makefile for rule %s' %
                      Utils.RuleDisplayName(rule))
      return (-1, rule)

    # Make the rule.
    status = cls._MakeSingeRule(rule, makefile, deps_file)
    if status != 1:
      TermColor.Failure('Failed Rule: %s' % Utils.RuleDisplayName(rule))
      return (status, rule)

    TermColor.Info('Built %s. Took %.2fs' %
                   (Utils.RuleDisplayName(rule), (time.time() - start)))
    # Everything done. Mark the rule as successful.
    return (1, rule)

  @classmethod
  def _PrepareDepsFile(cls, rule, deps_file):
    """Prepares the deps file for each rule. By default nothing is required.

    Args:
      rule: string: The rule to build.
      deps_file: string: The dep file to be prepared.
    """
    pass

  @classmethod
  def _MakeSingeRule(cls, rule, makefile, deps_file):
    """Builds a Single Rule.
    Args:
      rule: string: The rule to build.
      makefile: string: The *main* makefile name.

    Return:
      (int): Returns the result status.
          The status is '1' for success, '0' for 'ignore', '-1' for fail.
    """
    # Build the rule.

    if Flags.ARGS.pool_size:
      parallel_processes = Flags.ARGS.pool_size
    else:
      parallel_processes = max(multiprocessing.cpu_count(), 1)
    (status, out) = ExecUtils.RunCmd('make -r -j%d -f %s %s' % (parallel_processes,
                                                                deps_file, rule))
    if status:
      TermColor.Failure('Failed Rule: %s' % Utils.RuleDisplayName(rule))
      return -1

    TermColor.VInfo(1, '%s Output: \n%s' % (Utils.RuleDisplayName(rule), out))
    return 1
