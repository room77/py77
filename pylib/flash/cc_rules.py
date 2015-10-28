
"""Manages different functions related to cc rules parsing."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import itertools
import os
import shutil
import time

import r77_init  # pylint: disable=W0611
from pylib.base.term_color import TermColor
from pylib.base.exec_utils import ExecUtils
from pylib.file.file_utils import FileUtils

from make_rules import MakeRules
from utils import Utils


class CCRules(MakeRules):
  """Class to manage different functions related to parsing of cc rules."""

  @staticmethod
  def GetDepsRuleName(target):
    """Returns the deps rule for the rule."""
    if not target : return None
    return 'depend' + target.replace('/', '_')

  @classmethod
  def WriteMakefile(cls, specs, makefile):
    """Writes the auto make file for the given spec.

    Args:
      specs: List of dict of type {target, target_type, src, hdr, flag, link, pack}.
        In each dict, 'src', 'hdr' 'flag' and 'link' contain everything needed to
        build 'target'
      makefile: The (auto) makefile to generate.
    """
    f = open(makefile, 'w')
    f.write('\nCFLAGS = $(DEFAULT_CFLAGS) $(ENV_CFLAGS)\n')
    f.write('\nCCFLAGS = $(DEFAULT_CCFLAGS) $(ENV_CCFLAGS)\n')
    index = 0
    for item in specs:
      index += 1
      target = item['_target']
      target_bin = FileUtils.GetBinPathForFile(target)
      target_name = os.path.basename(target)
      target_dep_dir = target_bin + '_deps'

      f.write('\n# Dep dir for %s\n' % target)
      f.write('CC_TARGET_DEP_DIR_%d = %s\n' % (index, target_dep_dir))

      f.write('\n# Flags for %s\n' % target)
      f.write('CFLAGS_%d = %s\n' % (index, str.join(' ', item.get('flag', set()))))

      f.write('\n# Srcs for %s\n' % target)
      f.write('CC_SRC_%d = %s\n' % (index, str.join('\\\n  ', item.get('src', set()))))
      f.write('\nCC_SRC_C_%d = $(filter %%.c,$(CC_SRC_%d))\n' % (index, index))
      f.write('CC_SRC_CC_%d = $(filter %%.cc,$(CC_SRC_%d))\n' % (index, index))
      f.write('CC_SRC_CPP_%d = $(filter %%.cpp,$(CC_SRC_%d))\n' % (index, index))

      f.write('\n# Hdrs for %s\n' % target)
      f.write('CC_HDR_%d = %s\n' % (index, str.join('\\\n  ', item.get('hdr', set()))))

      f.write('\n# Libs for %s\n' % target)
      f.write('CC_LIB_%d = %s\n' % (index, str.join(' ', item.get('link', set()))))

      f.write('\n# Dependencies for %s\n' % target)
      f.write('CC_DEPS_FILE_%d = %s\n' %
              (index, cls.GetDepsFileName(makefile, target, '.auto.cc.')))

      f.write('\n# Objs for %s\n' % target)
      f.write('CC_OBJ_C_%d = $(addprefix $(CC_TARGET_DEP_DIR_%d),$(CC_SRC_C_%d:.c=.o))\n' %
              (index, index, index))
      f.write('CC_OBJ_CC_%d = $(addprefix $(CC_TARGET_DEP_DIR_%d),$(CC_SRC_CC_%d:.cc=.o))\n' %
              (index, index, index))
      f.write('CC_OBJ_CPP_%d = $(addprefix $(CC_TARGET_DEP_DIR_%d),$(CC_SRC_CPP_%d:'
              '.cpp=.o))\n' %
              (index, index, index))

      f.write('\n$(CC_OBJ_C_%d) : $(CC_TARGET_DEP_DIR_%d)%%.o: %%.c\n' % (index, index))
      f.write('\t@mkdir -p $(dir $@)\n')
      f.write('\t$(C) $(CFLAGS_%d) $(CFLAGS) -o $@ -c $<\n' % index)

      f.write('\n$(CC_OBJ_CC_%d) : $(CC_TARGET_DEP_DIR_%d)%%.o: %%.cc\n' % (index, index))
      f.write('\t@mkdir -p $(dir $@)\n')
      f.write('\t$(CC) $(CFLAGS_%d) $(CCFLAGS) -o $@ -c $<\n' % index)

      f.write('\n$(CC_OBJ_CPP_%d) : $(CC_TARGET_DEP_DIR_%d)%%.o: %%.cpp\n' %
              (index, index))
      f.write('\t@mkdir -p $(dir $@)\n')
      f.write('\t$(CC) $(CFLAGS_%d) $(CCFLAGS) -o $@ -c $<\n' % index)

      # Write the target.
      f.write('\n%s : $(CC_OBJ_C_%d) $(CC_OBJ_CC_%d) $(CC_OBJ_CPP_%d) $(CC_HDR_%d)\n' %
              (target, index, index, index, index))
      type = item.get('_type', 'invalid')
      if type == 'cc_bin' or type == 'cc_test':
        flags = '$(CFLAGS)' if item.get('bin_type', 'cc') == 'c' else '$(CCFLAGS)'
        f.write('\t@echo "Linking %s "\n' % target)
        f.write('\t@mkdir -p $(BINDIR)\n')
        f.write('\t$(CC) $(CFLAGS_%d) %s -o %s '
                '$(filter %%.o, $^) $(DEFAULT_LIBS) $(CC_LIB_%d)\n' %
                (index, flags, target_bin, index))
        f.write('\t@ln -s -f %s $(BINDIR)/$(notdir $@)\n' % target_bin)
        pack = item.get('pack', 0)
        if pack == 1:
          f.write('\t@echo -n "Packing "\n'
                  '\t$(SRCROOT)/public/bin/codebase/package %s\n' % target_bin)
        elif pack == 2:
          record_access_file = os.path.join(target_dep_dir, target_name + '.files')
          f.write('\t@echo -n "Packing "\n')
          f.write('\t%s --r77_run_main=false --record_file_access '
                  '--record_file_access_output=%s\n' %
                  (target_bin, record_access_file))
          f.write('\t$(SRCROOT)/public/bin/codebase/package %s $(shell cat %s)\n' %
                  (target_bin, record_access_file))

        f.write('\t@echo "Created: %s"\n' % target_bin)
      elif type == 'cc_shared':
        target_lib_name = '_%s.so' % target_name
        target_lib = target_bin.replace(target_name, target_lib_name)
        flags = '$(CFLAGS)' if item.get('bin_type', 'cc') == 'c' else '$(CCFLAGS)'
        f.write('\t@echo "Linking %s "\n' % target)
        f.write('\t@mkdir -p $(BINDIR)\n')
        f.write('\t$(CC) $(CFLAGS_%d) -shared %s -o %s '
                '$(filter %%.o, $^) $(DEFAULT_LIBS) $(CC_LIB_%d)\n' %
                (index, flags, target_lib, index))

      f.write('\t@echo "Finished: $@"\n\n')

      # makedepend rule
      f.write('%s:\n'
              '\t@echo "Building dependency files..."\n'
              '\t@makedepend -p$(CC_TARGET_DEP_DIR_%d) -f$(CC_DEPS_FILE_%d) '
              '$(MAKEDEPEND_ARGS) -- $(CFLAGS_%d) -- $(CC_SRC_%d) $(CC_HDR_%d)' %
              (cls.GetDepsRuleName(target), index, index, index, index, index))
      f.write('\n\n')

    f.close()

  @classmethod
  def _PrepareDepsFile(cls, rule, deps_file):
    """Prepares the deps file for each rule. By default nothing is required.

    Args:
      rule: string: The rule to build.
      deps_file: string: The dep file to be prepared.
    """
    f = open(deps_file, 'a')
    f.write('\n\n# DO NOT DELETE THIS LINE -- make depend depends on it.\n')
    f.close()


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
    # Get dependencies list for the rule. Run this with the original main file.
    (status, out) = ExecUtils.RunCmd('make -f %s %s' %
                                     (makefile, cls.GetDepsRuleName(rule)))
    if status:
      TermColor.Error('Could not make dependency for rule %s' %
                      Utils.RuleDisplayName(rule))
      return -1

    return super(CCRules, cls)._MakeSingeRule(rule, makefile, deps_file)
