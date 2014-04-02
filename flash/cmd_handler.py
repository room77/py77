"""Base class for command handlers."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import json
import os

import r77_init  # pylint: disable=W0611
from pylib.base.flags import Flags
from pylib.base.term_color import TermColor

from rules import Rules
from utils import Utils

class CmdHandler(object):
  """Base class for various command handlers."""

  @classmethod
  def Init(cls, parser):
    """Initialize the cleaner.
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    parser.add_argument('-a', '--allowed_rule_types',
                        type=lambda x : [y for y in x.split(',') if x],
                        default=Rules.PARSED_RULE_TYPES,
                        help='Comma separated list of Rule types that can be to '
                        'collect from the RULES file. Useful when the target '
                        'is a directory. e.g. "-t bin,test".')
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='Debug mode.')
    parser.add_argument('-i', '--ignore_rules',
                        type=lambda x : [y for y in x.split(',') if x],
                        default=['deprecated', 'no_build'],
                        help='Comma separated list of substrings specifying '
                        'rules to ignore. e.g. specify "_xxx" to ignore all '
                        'rules containing "_xxx".')
    parser.add_argument('-p', '--pool_size', type=int, default=0,
                        help='The pool size for parallelization.')
    parser.add_argument('rule', type=str, nargs='*',
                        help='Can be any of: \n'
                            'Files: "meta/search/search_server.cc"; '
                            'Rules: "meta/search/search_server"; '
                            'Directories: "meta" "meta/*"; '
                            'Tree: "meta/..." ')

  @classmethod
  def Run(cls):
    """Runs the command handler.

    Return:
      int: Exit status. 0 means no error.
    """
    rules = cls._ComputeRules(Flags.ARGS.rule, Flags.ARGS.ignore_rules)
    if not rules:
      TermColor.Warning('Could not find any rules.')
      return 101

    (successful_rules, failed_rules) = cls.WorkHorse(rules)
    if successful_rules:
      TermColor.Info('')
      TermColor.Success('No. of Rules: %d' % len(successful_rules))
      TermColor.VInfo(1, 'Successful Rules: %s' %
                      json.dumps(Utils.RulesDisplayNames(successful_rules), indent=2))

    if failed_rules:
      TermColor.Info('')
      TermColor.Failure('No. of Rules: %d' % len(failed_rules))
      TermColor.Failure('Rules: %s' %
                        json.dumps(Utils.RulesDisplayNames(failed_rules), indent=2))
      return 102

    return 0

  @classmethod
  def WorkHorse(cls, rules):
    """Runs the workhorse for the command. All derived classes must implement
    this method.

    Args:
      rules: list: List of rules to be handled.

    Return:
      (list, list): Returns a tuple of list in the form
          (successful_rules, failed_rules) specifying rules that succeeded and
          ones that failed.
    """
    TermColor.Fatal('Not supported!')
    return (None, None)

  @classmethod
  def _ComputeRules(cls, targets, ignore_list=[]):
    """Computes the rules to be run given the input targets.
    Args:
      targets: list: List of input targets.
    Return:
      list: List of actual rules to be run.
    """
    rules = []
    for target in targets:
      ignore = Utils.IgnoreRule(target, ignore_list)
      if ignore:
        TermColor.Warning('Ignored target %s as anything with [%s] is ignored.' %
                          (target, ignore))
        continue

      if os.path.isdir(target):
        target = os.getcwd() if target == '.' else target
        rule = os.path.join(target, 'RULES')
        if os.path.isfile(rule):
          rules += [ Utils.RuleNormalizedName(rule) ]
        else:
          TermColor.Warning('No RULES file in directory: %s' % target)
      elif os.path.isfile(target):
        rules += [ Utils.RuleNormalizedName(os.path.splitext(target)[0]) ]
      elif os.path.basename(target) == '...' :
        dir = os.path.dirname(target)
        if not dir: dir = os.getcwd()
        dir = os.path.dirname(Utils.RuleNormalizedName(
            os.path.join(dir, 'RULES')))
        rules += Utils.GetRulesFilesFromSubdirs(dir, ignore_list)
      else:
        rules += [Utils.RuleNormalizedName(target)]

    temp_list = []
    seen = set()
    for rule in rules:
      if rule in seen: continue
      temp_list += [rule]
      seen |= set([rule]);

    rules = []
    for rule in temp_list:
      if ((os.path.basename(rule) != 'RULES') and
          (os.path.join(os.path.dirname(rule), 'RULES') in seen)):
        continue
      rules += [rule]

    return rules

