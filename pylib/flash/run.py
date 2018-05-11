#!/usr/bin/env python

"""Handles run."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import itertools
import os
import sys
import time

from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.base.exec_utils import ExecUtils
from pylib.file.file_utils import FileUtils

from pylib.flash.build import Builder
from pylib.flash.cmd_handler import CmdHandler
from pylib.flash.utils import Utils

class Runner(CmdHandler):
  """Class to handle run."""

  @classmethod
  def Init(cls, parser):
    super(Runner, cls).Init(parser)
    parser.add_argument('-t', '--timeout', type=int, default=86400,
                        help='Timeout for the executable.')
    parser.add_argument('-r', '--args', type=str, default='',
                        help='Args passed to the executable.')
    parser.set_defaults(allowed_rule_types=['cc_test', 'cc_bin',
                                            'js_test', 'js_bin',
                                            'ng_test',
                                            'nge2e_test',
                                            'pkg', 'pkg_bin', 'pkg_sys',
                                            'py_test', 'py_bin',
                                           ])

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
    (successful_build, failed_build) = Builder.WorkHorse(rules)

    # All our binaries assume they will be run from the source root.
    os.chdir(FileUtils.GetSrcRoot())

    pipe_output = len(successful_build) > 1
    args = zip(itertools.repeat(cls), itertools.repeat('_RunSingeRule'),
                          successful_build, itertools.repeat(pipe_output))
    rule_res = ExecUtils.ExecuteParallel(args, Flags.ARGS.pool_size)
    successful_run = []; failed_run = []
    for (res, rule) in rule_res:
      if res == 1:
        successful_run += [rule]
      elif res == -1:
        failed_run += [rule]

    return (successful_run, failed_build + failed_run)

  @classmethod
  def _RunSingeRule(cls, rule, pipe_output):
    """Runs a Single Rule.

    Args:
      rule: string: The rule to run.
      pipe_output: bool: Whether to pipe_output or dump it to STDOUT.

    Return:
      (int, string): Returns a tuple of the result status and the rule.
          The status is '1' for success, '0' for 'ignore', '-1' for fail.
    """
    TermColor.Info('Running %s' % Utils.RuleDisplayName(rule))
    start = time.time()
    bin_file = FileUtils.GetBinPathForFile(rule)
    (status, out) = ExecUtils.RunCmd('%s %s' % (bin_file, Flags.ARGS.args),
                                     Flags.ARGS.timeout, pipe_output)
    if status:
      TermColor.Failure('Failed Rule: %s' % Utils.RuleDisplayName(rule))
      return (-1, rule)

    TermColor.Info('Ran %s. Took %.2fs' %
                   (Utils.RuleDisplayName(rule), (time.time() - start)))
    # Everything done. Mark the rule as successful.
    return (1, rule)


def main():
  try:
    Runner.Init(Flags.PARSER)
    Flags.InitArgs()
    return Runner.Run()
  except KeyboardInterrupt as e:
    TermColor.Warning('KeyboardInterrupt')
    return 1


if __name__ == '__main__':
  sys.exit(main())
