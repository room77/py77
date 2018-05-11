# !/usr/bin/env python

"""Generates makefile based on user-supplied targets."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import glob
import inspect
import re
import os
import shutil
import subprocess
import sys
import tempfile

from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils

from pylib.flash.cc_rules import CCRules
from pylib.flash.js_rules import JSRules
from pylib.flash.ng_rules import NGRules
from pylib.flash.nge2e_rules import NGe2eRules
from pylib.flash.pkg_rules import PkgRules
from pylib.flash.proto_rules import ProtoRules
from pylib.flash.py_rules import PyRules
from pylib.flash.swig_rules import SwigRules
from pylib.flash.rules import Rules, RulesParseError
from pylib.flash.utils import Utils

class Error(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return "'%s'" % self.value

class GenMakefile:
  """Generates the makefile for the given rules."""

  def __init__(self, debug=False, make_dir=None):
    """Generates the default make files.
    Args:
      make_dir: string: The directory in which make files are created.
      cleanup: bool: Cleanup at the end.
    """
    if not make_dir:
      make_dir = os.path.join(FileUtils.GetBinDir(), '__build_files__')

    self.__make_dir = make_dir
    self.__debug = debug

    # Create the dir if not already present.
    if not os.path.exists(make_dir):
      os.makedirs(make_dir)

    (makefile_fd, self.__makefile_name) = tempfile.mkstemp(
        prefix='makefile_', suffix='.main.mak', dir=make_dir)

    # Detect supported compilers
    self.__gcc_supported = self._CompilerSupported('gcc')
    self.__clang_supported = self._CompilerSupported('clang')

    # Generate dummy files.
    self.ResetMakeFiles()

  def __del__(self):
    if not self.__debug: self.Cleanup()

  def _CompilerSupported(self, compiler):
    with open(os.devnull, 'w') as devnull:
      exit_code = subprocess.call(
          '%s --help | head -n1 | grep -q %s' % (compiler, compiler),
          stdout=devnull, stderr=devnull, shell=True)
      return exit_code == 0

  def Cleanup(self):
    """Remove the build files."""
    try:
      files = glob.glob(self.__makefile_name.replace('.main.mak', '.*'))
      for file in files: os.remove(file)
    except OSError as e:
      TermColor.VInfo(2, 'Could not Cleanup make files. Error: %s' % e)

  def GetMakeFileName(self):
    """Return: string: The name of the makefile."""
    return  self.__makefile_name

  def GetAutoMakeFileName(self, type="cc"):
    """Return: string: The name of the automake file."""
    return  self.__makefile_name.replace('.main.', '.auto.' + type + '.')

  def GetMakeFileTemplate(self):
    # Prefer gcc
    if self.__gcc_supported:
      return 'Makefile.template.gcc'
    elif self.__clang_supported:
      return 'Makefile.template.clang'
    else:
      raise Error(TermColor.ColorStr(
        'No supported compiler found. Require gcc or clang', 'RED'))

  def ResetMakeFiles(self):
    """Resets the main and auto make files."""
    FileUtils.CreateFileWithData(self.__makefile_name)
    FileUtils.CreateFileWithData(self.GetAutoMakeFileName('cc'))
    FileUtils.CreateFileWithData(self.GetAutoMakeFileName('js'))
    FileUtils.CreateFileWithData(self.GetAutoMakeFileName('ng'))
    FileUtils.CreateFileWithData(self.GetAutoMakeFileName('nge2e'))
    FileUtils.CreateFileWithData(self.GetAutoMakeFileName('pkg'))
    FileUtils.CreateFileWithData(self.GetAutoMakeFileName('pkg_bin'))
    FileUtils.CreateFileWithData(self.GetAutoMakeFileName('pkg_sys'))
    FileUtils.CreateFileWithData(self.GetAutoMakeFileName('py'))
    FileUtils.CreateFileWithData(self.GetAutoMakeFileName('swig'))

  def GenMainMakeFile(self):
    """Generates the main make file."""
    f = open(self.GetMakeFileName(), 'w')
    f.write('SRCROOT = %s\n' % FileUtils.GetSrcRoot())
    f.write('BINDIR = %s\n' % FileUtils.GetBinDir())
    f.write('AUTO_MAKEFILE_CC = %s\n' % self.GetAutoMakeFileName('cc'))
    f.write('AUTO_MAKEFILE_JS = %s\n' % self.GetAutoMakeFileName('js'))
    f.write('AUTO_MAKEFILE_NG = %s\n' % self.GetAutoMakeFileName('ng'))
    f.write('AUTO_MAKEFILE_NGE2E = %s\n' % self.GetAutoMakeFileName('nge2e'))
    f.write('AUTO_MAKEFILE_PKG = %s\n' % self.GetAutoMakeFileName('pkg'))
    f.write('AUTO_MAKEFILE_PKG_BIN = %s\n' % self.GetAutoMakeFileName('pkg_bin'))
    f.write('AUTO_MAKEFILE_PKG_SYS = %s\n' % self.GetAutoMakeFileName('pkg_sys'))
    f.write('AUTO_MAKEFILE_PY = %s\n' % self.GetAutoMakeFileName('py'))
    f.write('AUTO_MAKEFILE_SWIG = %s\n' % self.GetAutoMakeFileName('swig'))
    f.write('PROTOBUFDIR = %s\n' % ProtoRules.GetProtoBufBaseDir())
    f.write('PROTOBUFOUTDIR = %s\n' % ProtoRules.GetProtoBufOutDir())
    f.write('SWIGBUFOUTDIR = %s\n' % SwigRules.GetSwigOutDir())
    f.write('\n')

    makefile_template = os.path.join(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),
        self.GetMakeFileTemplate())

    f.write('###############################################################\n')
    f.write('#Template from: %s \n' % makefile_template)
    f.write('###############################################################\n')
    f.write(open(makefile_template).read())
    f.write('\n###############################################################\n')

  def GenAutoMakeFileFromRules(self, rules, allowed_rule_types=None):
    """Generates the automake file for the input set of rules.
    Args:
      rules: list: List of rules for which the automake is to be generated.
      allowed_rule_types: list: List of allowed rules to use from the RULES
          file. e.g. ['cc_bin', 'cc_test'] will create make rules for all
          'cc_bin' and 'cc_test' rules in the RULES file but not for 'cc_lib'
          rules.

    Return:
      (dict {string : list}, list): Returns a tuple in the form
           ({type: successful_rules}, failed_rules) specifying rules for which
           the make rules were successfully generated and for which it failed.
    """
    specs = {}
    successful_rules = {}

    (successful_expand, failed_rules) = Rules.GetExpandedRules(rules, allowed_rule_types)
    for target in successful_expand:
      rule_data = Rules.GetRule(target)

      # Expand dependency list.
      seen_deps = set()
      try:
        # Copy the deps to a new set.
        deps = set(rule_data.get('dep', set()))
        for dep in deps:
          if dep not in seen_deps:
            seen_deps |= set([dep])
            Rules.Flatten(dep, target, rule_data)
          else:
            TermColor.Warning('Rule %s has duplicate dep %s ' %
                              (Utils.RuleDisplayName(target),
                               Utils.RuleDisplayName(dep)))
      except RulesParseError as e:
        TermColor.Error('Could not flatten %s' % target)
        failed_rules += [target]
        continue

      rule_type = rule_data.get('_type' , '')
      if rule_type == 'proto_lib':
        # TODO(pramodg): Revisit when we want to add other code sources.
        ProtoRules.UpdateProtoRuleWithFormattedData(rule_data, 'cc_lib')
      elif rule_type == 'swig_lib':
        SwigRules.WriteMakefile(rule_data, self.GetAutoMakeFileName('swig'))
        SwigRules.UpdateSwigRuleWithFormattedData(rule_data)


      # Get the rule type again as it may have been updated.
      rule_type = rule_data.get('_type' , '')
      rule_type_base = re.sub('_.*', '', rule_type)
      if not rule_type_base:
        TermColor.Error('Invalid Rule type: [%s]' % rule_type)
        failed_rules += [target]
        continue

      # Now we have a complete list of source files, compile flags and links
      # for this target.
      specs[rule_type_base] = specs.get(rule_type_base, []) + [rule_data]
      successful_rules[rule_type_base] = (
          successful_rules.get(rule_type_base, []) + [target])

    # Generate the automake file for each rule type.
    for (k, v) in list(specs.items()):
      if k == 'cc':
        CCRules.WriteMakefile(v, self.GetAutoMakeFileName('cc'))
      elif k == 'js':
        JSRules.WriteMakefile(v, self.GetAutoMakeFileName('js'))
      elif k == 'ng':
        NGRules.WriteMakefile(v, self.GetAutoMakeFileName('ng'))
      elif k == 'nge2e':
        NGe2eRules.WriteMakefile(v, self.GetAutoMakeFileName('nge2e'))
      elif k == 'pkg':
        PkgRules.WriteMakefile(v, self.GetAutoMakeFileName('pkg'))
      elif k == 'pkg_bin':
        PkgRules.WriteMakefile(v, self.GetAutoMakeFileName('pkg_bin'))
      elif k == 'pkg_sys':
        PkgRules.WriteMakefile(v, self.GetAutoMakeFileName('pkg_sys'))
      elif k == 'py':
        PyRules.WriteMakefile(v, self.GetAutoMakeFileName('py'))
      else:
        TermColor.Info('No make file to be generated for %s' % k)

    return (successful_rules, failed_rules)
