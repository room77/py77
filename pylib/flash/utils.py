
"""Utils file for the different build operations."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import os

import r77_init  # pylint: disable=W0611
from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils

class Utils:
  """Utility class."""

  @classmethod
  def GetRulesFileForRule(cls, rule):
    """Returns the RULES file for the rule.
    Args:
      rule: string: The rule for which the file is needed.

    Return:
      string: The rules file if it exists.
    """
    if not rule: return None

    return FileUtils.GetAbsPathForFile(os.path.join(os.path.dirname(rule), 'RULES'))

  @classmethod
  def RuleNormalizedName(cls, rule):
    """Returns the normalized name for the rule.
    Args:
      rule: string: The rule to normalize.

    Return:
      string: The Normalized name of the rule.
    """
    if rule.find(FileUtils.GetSrcRoot()) == 0:
      return os.path.normpath(rule)

    rules_file = cls.GetRulesFileForRule(rule)
    if rules_file:
      return os.path.join(os.path.dirname(rules_file), os.path.basename(rule))

    # This does not have a rules file. Generally this happens for src files.
    abs_path = FileUtils.GetAbsPathForFile(rule)
    if abs_path: return abs_path

    return rule

  @classmethod
  def RuleRelativeName(cls, rule):
    """Returns the relative name for the rule w.r.t the src dir.
    Args:
      rule: string: The rule for which the relative name is required.

    Return:
      string: The relative name of the rule.
    """
    if not rule: return None
    return os.path.relpath(cls.RuleNormalizedName(rule), FileUtils.GetSrcRoot())

  @classmethod
  def RuleDisplayName(cls, rule):
    """Returns the display name for the rule.
    Args:
      rule: string: The rule to display.

    Return:
      string: The display name of the rule.
    """
    if not rule: return None
    return '/' + cls.RuleRelativeName(rule)

  @classmethod
  def RuleBaseName(cls, rule):
    """Returns the base name for the rule.
    Args:
      rule: string: The rule for which the base name is required.

    Return:
      string: The base name of the rule.
    """
    if not rule: return None
    return os.path.basename(rule)

  @classmethod
  def RulesDisplayNames(cls, rules):
    """Returns the display name for a list of rules.
    Args:
      rules: list: List of rules to display.

    Return:
      list: The display name of the rules.
    """
    return [cls.RuleDisplayName(rule) for rule in rules]

  @classmethod
  def IgnoreRule(cls, rule, ignore_list):
    """Check if a given rule can be ignored.
    Args:
      rule: string: The rule to check.
      ignore_list: list: List of strings to ignore.

    Return:
      string: Returns the string because of which the rule is ignored and None
          otherwise.
    """
    return next((x for x in ignore_list if rule.find(x) != -1), None)

  @classmethod
  def GetRulesFilesFromSubdirs(cls, dir, ignore_list=[]):
    """Given a directory, returns the rules files from all the subdirectories.
    Args:
      dir: string: The directory to walk.
      ignore_list: list: List of strings to ignore.

    Return:
      list: List of rules files to be run.
    """
    rules = []
    if not os.path.isdir(dir):
      TermColor.Warning('Not a directory: %s' % dir)
      return rules

    for (root, subdirs, files) in os.walk(dir):
      if 'RULES' in files:
        ignore = cls.IgnoreRule(root, ignore_list)
        if ignore:
          TermColor.Info('Ignored targets in %s as anything with [%s] is ignored' %
                         (root, ignore))
          continue
        rules += [ cls.RuleNormalizedName(os.path.join(root, 'RULES')) ]

    return rules
