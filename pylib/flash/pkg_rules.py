"""Builds data packages with flash"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import re

from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils
from pylib.flash.make_rules import MakeRules

Flags.PARSER.add_argument('--pkg_version_path', default='',
                          help='the file to APPEND the generated package versions')
Flags.PARSER.add_argument('--pkg_version_prefix', default='',
                          help='the package version name. version name must ' + \
                              'start with numbers')

class Error(Exception):
  """Triggered when there is an error creating a package"""
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)


class PkgRules(MakeRules):
  """Packages BOTH binaries and regular data packages. May
  eventually need to split into multiple rules if there are
  sufficient differences between the two
  """
  @classmethod
  def WriteMakefile(cls, specs, makefile):
    """@override"""
    # TODO(edelman) modify this script to actually copy the file and simply
    #   do the rsync in the run component.
    # To add a file to build you need to AT LEAST make the following edits:
    #   create a new *_rules.py files. see pkg_rules.py for an example
    #   edit gen_makefile.py and add the new type to ResetMakeFiles, GenMakeFile,
    #   and GenAutoMakeFileFromRules (at the bottom). Then add the new AUTO_MAKEFILE_*
    #   variable in Makefile.template.
    #   In rules.py, add to the PARSED_RULE_TYPES and at the bottom, register the
    #     global functions to be executed for the rule.
    #   In build.py, edit the rules_map to include the new rule.
    #   If the rule can be run, add to the allowed_rule_types in run.py
    i = 1
    pkg_arg = ''
    if Flags.ARGS.pkg_version_path:
      pkg_arg += ' --pkg_version_path=%s ' % Flags.ARGS.pkg_version_path
    with open(makefile, 'w') as f:
      for spec in specs:
        pkg_flags = pkg_arg
        # check if the version is set. if so verify that it starts with numbers
        # and an underscore
        if Flags.ARGS.pkg_version_prefix:
          if not re.match('^\d+_', Flags.ARGS.pkg_version_prefix):
            raise Error(('pkg_version_prefix, %s, is invalid! must start with' +
                         ' digits followed by underscore') \
                        % Flags.ARGS.pkg_version_prefix)
          pkg_flags += ' --pkg_version_prefix=%s ' % \
                       (Flags.ARGS.pkg_version_prefix)

        target = spec['_target']
        target_bin = FileUtils.GetBinPathForFile(target)
        f.write('\n%s:\n' % target)
        f.write('\t@echo "Creating package name %s"\n' % spec['name'])
        f.write('\t@mkdir -p $(dir %s)\n' % target_bin)
        f.write('\t@echo "$(SRCROOT)/prod/packager/packager.py %s %s" > %s\n' %
                (target, pkg_flags, target_bin))
        f.write('\tchmod 754 %s\n' % target_bin)
        f.write('\t@ln -s -f %s $(BINDIR)/$(notdir $@)\n' % target_bin)
        f.write('\t@echo "Created: %s"\n' % target_bin)
        i+=1
