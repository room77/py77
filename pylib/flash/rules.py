#!/usr/bin/env python

"""Parses the RULES file."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import subprocess
import os
import re
import sys
import threading
import types

from pylib.base.term_color import TermColor

from pylib.flash.proto_rules import ProtoRules
from pylib.flash.swig_rules import SwigRules
from pylib.flash.utils import Utils


class RulesParseError(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)

class Rules:
  """Class that maintains data for different rules."""

  PARSED_RULE_TYPES = ['cc_lib', 'cc_bin', 'cc_test',
                       'proto_lib',
                       'js_lib', 'js_bin', 'js_test',
                       'ng_lib', 'ng_test', 'nge2e_test',
                       'pkg', 'pkg_bin', 'pkg_sys',
                       'py_lib', 'py_bin', 'py_test',
                       'swig_lib'
                      ]

  FLATTENED_RULE_TYPES = {'cc': ['cc_lib', 'proto_lib'],
                          'py': ['py_lib', 'proto_lib', 'swig_lib', 'cc_lib'],
                          'js': ['js_lib'],
                          'ng': ['ng_lib'],
                          'pkg': ['pkg', 'pkg_bin', 'pkg_sys'],
                          'swig': ['cc_lib']
                         }

  basedir = ''

  LOAD_LOCK = threading.Lock()

  # These rules are collected from the RULES files.
  # Each is a dict from rule_name -> dict {rule data}. A rule data usually
  # consists of different fields like 'src', 'hdr', 'deps',
  # 'flags', etc.
  rules = {}

  # List of rules in a given dir.
  rules_by_dir = {}

  # Rules already loaded.
  loaded = set()

  @classmethod
  def AddRuleForDir(cls, name, rule_type):
    """Adds the rules to base dir.

    Args:
      name: string: The name of the rule.
      rule_type: string: The rule_type of the rule. e.g. 'cc_lib', 'cc_bin', etc.
    """
    rules_in_dir = cls.rules_by_dir.get(cls.basedir, {})
    rules = rules_in_dir.get(rule_type, [])
    rules += [name]
    rules_in_dir[rule_type] = rules
    cls.rules_by_dir[Rules.basedir] = rules_in_dir

  @classmethod
  def GetRulesForDir(cls, basedir, types):
    """Get the rules in the base dir of the given types.

    Args:
      basedir: string: The basedir of the rule.
      types: list[string]: The types for which the rules are to be returned.
          e.g. 'cc_lib', 'cc_bin', etc.

    Return:
      list[string]: List of rules for all the specified types.
    """
    res = []
    rules_in_dir = cls.rules_by_dir.get(basedir, {})
    if not rules_in_dir:
      return res

    if not types:
      types = list(rules_in_dir)

    for type in types:
      res += rules_in_dir.get(type, [])

    return res

  @classmethod
  def GetRule(cls, expanded_name):
    """Returns the rule data for the specified rule.

    Args:
      expanded_name: string: The expanded name of the rule.

    Return:
      dict: Dictionary containing the data for the rule.
    """
    return cls.rules.get(expanded_name, {})

  @classmethod
  def AddRuleForType(cls, rule_type, name, args):
    """Adds the rules to base dir.

    Args:
      rule_type: string: The rule_type of the rule. e.g. 'cc_lib', 'cc_bin', etc.
      name: string: The name of the rule.
      args: dict: The arguments passed to the rule function.

    Exceptions:
      RulesParseError: Raises exception if parsing fails.
    """
    rule = cls.Expand(name)
    args['_target'] = rule
    args['_type'] = rule_type

    if rule in cls.rules:
      err_str = 'Rule [%s] already defined.' % name
      TermColor.Error(err_str)
      raise RulesParseError(err_str)

    cls.rules[rule] = args

  @classmethod
  def Expand(cls, name):
    """Expand a file sname based on basedir.

    Args:
      name: string: The name of the rule.

    Exceptions:
      RulesParseError: Raises exception if parsing fails.
    """
    sname = name.strip()
    if not sname:
      err_str = 'Empty names are not allowed in RULES specification'
      TermColor.Error(err_str)
      raise RulesParseError(err_str)

    if not cls.basedir:  # no basedir specified
      return sname
    elif sname[0] == '/':  # absolute path
      return Utils.RuleNormalizedName(sname)
    else:  # relative path
      return Utils.RuleNormalizedName(os.path.join(cls.basedir, sname))

  @classmethod
  def ValidateRule(cls, name, rule_type, args):
    """Validates the rules.

    Args:
      name: string: The name of the rule.
      rule_type: string: The rule_type of the rule.
      args: dict: The arguments passed to the rule function.

    Exceptions:
      RulesParseError: Raises exception if validation fails.
    """
    # Check name.
    if not name or name.find('.') != -1 or rule_type not in cls.PARSED_RULE_TYPES:
      err_str = 'Invalid target [%s] of rule_type [%s].' % (name, rule_type)
      TermColor.Error(err_str)
      raise RulesParseError(err_str)

    # Get the expanded names for all src, hdr, dep args.
    for field in ['src', 'hdr', 'dep', 'main', 'prebuild', 'flag', 'link']:
      field_data = args.get(field, [])
      if not field_data: continue
      if not isinstance(field_data, list):
        err_str = ('Invalid target: [%s]. field [%s] must be of <type \'list\'>, not %s' %
                   (name, field, type(field_data)))
        TermColor.Error(err_str)
        raise RulesParseError(err_str)

  @classmethod
  def FormatRule(cls, args):
    """Format the rules.

    Args:
      args: dict: The arguments passed to the rule function.
    """
    # Get the expanded names for all src, hdr, dep args.
    for field in ['src', 'hdr', 'dep', 'main', 'prebuild']:
      args[field] = set([ cls.Expand(x) for x in args.get(field, []) ])

    # Convert lists to sets.
    for field in ['flag', 'link']:
      args[field] = set([ x for x in args.get(field, []) ])

  @classmethod
  def AddRule(cls, args, rule_type):
    """Add a rule to the ruleset for the rule_type.

    Args:
      args: dict: The arguments passed to the rule function.
      rule_type: string: The rule_type of the rule.

    Exceptions:
      RulesParseError: Raises exception if parsing fails.
    """
    name = args.get('name', '').strip()

    # Validate the rule.
    cls.ValidateRule(name, rule_type, args)

    # Format the rule.
    cls.FormatRule(args)

    # Add the rules for the types.
    cls.AddRuleForType(rule_type, name, args)

    # Add the rule for the dir.
    cls.AddRuleForDir(name, rule_type)

  @classmethod
  def LoadRules(cls, dirname):
    """Load RULES file from the given directory.

    Args:
      dirname: string: The dirname for which the Rules file needs to be loaded.

    Exceptions:
      RulesParseError: Raises exception if parsing fails.
    """
    # check if this directory has already been loaded
    rules_file = os.path.join(dirname, 'RULES')
    if not os.path.isfile(rules_file):
      TermColor.Error('Cannot find file: %s' % rules_file)
      return

    if rules_file in cls.loaded:
      return

    with cls.LOAD_LOCK:
      cls.loaded |= set([rules_file])
      # Save basedir for restoration later.
      oldbasedir = cls.basedir
      cls.basedir = dirname
      TermColor.VInfo(5, 'Reading %s' % rules_file)
      exec(compile(open(rules_file).read(), rules_file, 'exec'))
      cls.basedir = oldbasedir

  @classmethod
  def LoadRule(cls, rule):
    """Loads the rule.

    Args:
      rule: string: The rule that needs to be loaded.

    Return:
      boolean: True if rule is already present or successfully loaded and false
          otherwise.
    """
    # Check if the rule is loaded.
    if cls.GetRule(rule): return True

    (dirname, targetname) = os.path.split(rule)
    rules_file = os.path.join(dirname, 'RULES')
    if not dirname or not os.path.isfile(rules_file):
      TermColor.Error('No rules file %s for target %s ' % (
          rules_file, Utils.RuleDisplayName(rule)))
      return False

    try:
      Rules.LoadRules(dirname)
      return True
    except Exception as e:
      if type(e) == KeyboardInterrupt: raise e
      TermColor.PrintException('Could not load %s. ' % Utils.RuleDisplayName(rule))
      return False


  @classmethod
  def GetExpandedRules(cls, rules, allowed_rule_types=None):
    """Returns the expanded rules corresponding to input rules.
    Args:
      rules: list: List of rules for which the automake is to be generated.
      allowed_rule_types: list: List of allowed rules to use from the RULES
          file. e.g. ['cc_bin', 'cc_test'] will create make rules for all
          'cc_bin' and 'cc_test' rules in the RULES file but not for 'cc_lib'
          rules.

    Return:
      (list, list): Returns a tuple in the form (successful_rules, failed_rules)
          specifying rules that were expanded successfully and ones that failed.
    """
    if not allowed_rule_types:
      allowed_rule_types = cls.PARSED_RULE_TYPES

    successful_rules = []
    failed_rules = []
    for target in rules:
      if not cls.LoadRule(target):
        failed_rules += [target]
        continue

      expanded_targets = []
      (dirname, targetname) = os.path.split(target)
      if targetname == 'RULES':
        expanded_targets = cls.GetRulesForDir(dirname, allowed_rule_types)
        if not expanded_targets:
          TermColor.Warning('No rules found in %s' % target)
          continue
      else:
        expanded_targets = [targetname]

      for item in expanded_targets:
        item_rule = os.path.join(dirname, item)
        rule_data = cls.GetRule(item_rule)
        if not rule_data:
          TermColor.Error('Unable to find a rule for %s' %
                          Utils.RuleDisplayName(item_rule))
          failed_rules += [item_rule]
          continue

        rule_type = rule_data.get('_type' , 'invalid')
        if not rule_type in allowed_rule_types:
          TermColor.Error('Rule %s of type %s not allowed ' %
                          (Utils.RuleDisplayName(item_rule), rule_type))
          failed_rules += [item_rule]
          continue

        # All good.
        successful_rules += [item_rule]

    return (successful_rules, failed_rules)

  @classmethod
  def Flatten(cls, new_dep, referrer, referrer_data):
    """Given a new dependency, flatten it into existing

    Args:
      new_dep: string: The new dependency which needs to be flattened.
      referrer: string: The referrer for which the new dep is flattened.
      referrer_data: dict: The rule data for the referrer.

    Exceptions:
      RulesParseError: Raises exception if parsing fails.
    """
    TermColor.VInfo(5, '--- Resolving dependency %s' % new_dep)
    (libdir, libname) = os.path.split(new_dep)
    if not libdir:
      err_str = ('Cannot resolve dependency [%s] (referred to by [%s])'
                 % (Utils.RuleDisplayName(new_dep),
                    Utils.RuleDisplayName(referrer)))
      TermColor.Error(err_str)
      raise RulesParseError(err_str)

    # load the corresponding RULES file
    cls.LoadRules(libdir)

    new_dep_data = Rules.GetRule(new_dep)
    if not new_dep_data:
      err_str = 'Unable to find [%s] (referred to by [%s])' % (new_dep, referrer)
      TermColor.Error(err_str)
      raise RulesParseError(err_str)

    referre_type_base = re.sub('_.*', '', referrer_data.get('_type', 'invalid'))
    new_dep_type = new_dep_data.get('_type' , 'invalid')
    if not new_dep_type in cls.FLATTENED_RULE_TYPES.get(referre_type_base, []):
      err_str = ('Invalid rule [%s] of type [%s] (referred to by [%s])' %
                 (new_dep, new_dep_type, referrer))
      TermColor.Error(err_str)
      raise RulesParseError(err_str)

    # Merge the data.
    cls._MergeDepData(new_dep, new_dep_data, referrer, referrer_data)

    # Flatten recursively.
    for d in new_dep_data.get('dep', set()):
      if d not in referrer_data.get('dep', set()):
        with cls.LOAD_LOCK:
          referrer_data['dep'] |= set([d])
        Rules.Flatten(d, new_dep, referrer_data)

  @classmethod
  def _MergeDepData(cls, new_dep, new_dep_data, referrer, referrer_data):
    """Given a new dependency, flatten it into existing
    rule_data.

    Args:
      new_dep: string: The new dependency which needs to be flattened.
      new_dep_data: dict: The rule data for the new dep.
      referrer: string: The referrer for which the new dep is flattened.
      referrer_data: dict: The rule data for the referrer.
    """
    merge_ignore = {'name', 'dep'}
    if (new_dep_data.get('_type' , 'invalid') == 'proto_lib'):
      merge_ignore |= {'src', 'hdr'}
      proto_data = ProtoRules.GetProtoRuleFormattedData(new_dep_data,
          referrer_data.get('_type', 'invalid'))
      for key in list(proto_data):
        with cls.LOAD_LOCK:
          if key in referrer_data:
            referrer_data[key] |= proto_data[key]
          else:
            referrer_data[key] = proto_data[key]
    elif (new_dep_data.get('_type' , 'invalid') == 'swig_lib'):
      merge_ignore |= {'src'}
      swig_data = SwigRules.GetSwigRuleFormattedData(new_dep_data)
      for key in list(swig_data):
        with cls.LOAD_LOCK:
          if key in referrer_data:
            referrer_data[key] |= swig_data[key]
          else:
            referrer_data[key] = swig_data[key]

    # Merge all other keys from the new dep.
    with cls.LOAD_LOCK:
      for key in list(new_dep_data):
        if key in merge_ignore or key.find('_') == 0:
          continue
        if key in referrer_data:
          referrer_data[key] |= new_dep_data[key]
        else:
          referrer_data[key] = new_dep_data[key]

###################################################################
# Global Methods used in the 'RULES' file.
###################################################################

def lib(**kwargs):
  """
  Processes the lib rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'cc_lib')

def cc_lib(**kwargs):
  """
  Processes the cc_lib rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'cc_lib')

def bin(**kwargs):
  """
  Processes the bin rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'cc_bin')

def cc_bin(**kwargs):
  """
  Processes the cc_bin rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'cc_bin')

def test(**kwargs):
  """
  Processes the test rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'cc_test')

def cc_test(**kwargs):
  """
  Processes the cc_test rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'cc_test')

def proto_lib(**kwargs):
  """
  Processes the proto rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'proto_lib')

def py_lib(**kwargs):
  """
  Processes the py_lib rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'py_lib')

def py_bin(**kwargs):
  """
  Processes the py_bin rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'py_bin')

def py_test(**kwargs):
  """
  Processes the py_test rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'py_test')

def js_lib(**kwargs):
  """
  Processes the js_lib rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'js_lib')

def js_bin(**kwargs):
  """
  Processes the js_bin rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'js_bin')

def js_test(**kwargs):
  """
  Processes the js_test rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'js_test')

def ng_lib(**kwargs):
  """
  Processes the lib rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'ng_lib')

def ng_test(**kwargs):
  """
  Processes the test rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'ng_test')


def nge2e_test(**kwargs):
  """
  Processes the test rule.
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'nge2e_test')

def pkg(**kwargs):
  """
  Processes the pkg rule.
  Receives all the arguments as a dict
  """
  Rules.AddRule(kwargs, 'pkg')

def pkg_bin(**kwargs):
  """
  Processes the pkg_bin rule
  Receives all the argument as a dict
  """
  Rules.AddRule(kwargs, 'pkg_bin')

def pkg_sys(**kwargs):
  """
  Processes the pkg_sys rule
  Receives all the argument as a dict
  """
  Rules.AddRule(kwargs, 'pkg_sys')

def swig(**kwargs):
  """
  Processes the swig rule
  Receives all the arguments as a dict.
  """
  Rules.AddRule(kwargs, 'swig_lib')
