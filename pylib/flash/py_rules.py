
"""Manages different functions related to py rules parsing."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import itertools
import os
import shutil
import time

from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.base.exec_utils import ExecUtils
from pylib.file.file_utils import FileUtils

from make_rules import MakeRules
from utils import Utils


class PyRules(MakeRules):
  """Class to manage different functions related to parsing of py rules."""

  @classmethod
  def GetPyInstaller(cls):
    """Returns the pyinstaller."""
    return os.path.join(FileUtils.GetSrcRoot(),
                        'third_party/pyinstaller/latest/pyinstaller.py')

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
    index = 0
    for item in specs:
      index += 1
      target = item['_target']

      target_bin = FileUtils.GetBinPathForFile(target)
      target_dep_dir = target_bin + '_deps'

      f.write('\n# Dep dir for %s\n' % target)
      f.write('PY_TARGET_DEP_DIR_%d = %s\n' % (index, target_dep_dir))

      f.write('\n# Srcs for %s\n' % target)
      main = str.join('\\\n  ', item.get('main', set()))
      srcs = str.join('\\\n  ', item.get('src', set()))
      f.write('PY_SRC_%d = %s\n' % (index, str.join('\\\n  ', [main, srcs])))

      # Write the target.
      f.write('\n%s' % target)
      f.write(': $(PY_SRC_%d)\n' % (index))
      type = item.get('_type', 'invalid')
      if type == 'py_bin' or type == 'py_test':
        f.write('\t@echo "Creating Executable for %s "\n' % target)
        f.write('\t@mkdir -p $(PY_TARGET_DEP_DIR_%d)\n' % index)
        if type == 'py_bin':
          prebuild_commands = item.get('prebuild', [])
          for prebuild_command in prebuild_commands:
            f.write('\t@echo "Running prebuild script %s for %s "\n' %
                    (prebuild_command, target))
            f.write('\t@%s\n' % prebuild_command)
          f.write('\t@pushd $(PY_TARGET_DEP_DIR_%d);' % index)
          f.write('\tR77_SRC_ROOT=$(SRCROOT) $(PY) %s --onefile '
                  '--paths $(PYTHON_PATHS) '
                  '--out $(PY_TARGET_DEP_DIR_%d) --name=$(notdir $@) '
                  '--additional-hooks-dir=$(SRCROOT)/pylib/pyinstaller/hooks '
                  '$(PY_SRC_%d);' % (cls.GetPyInstaller(), index, index))
          f.write('\tpopd \n')
          f.write('\t@cp $(PY_TARGET_DEP_DIR_%d)/dist/$(notdir $@) %s\n' % (index, target_bin))
          if item.get('pack', 0) == 1:
            f.write('\t@echo -n "Packing "\n'
                    '\t$(SRCROOT)/scripts/package %s\n' % target_bin)
        elif type == 'py_test':
          f.write('\t@echo "# Python Test for %s" > %s\n' % (target, target_bin))
          f.write('\t@echo "export PYTHONPATH=$(PYTHON_PATHS)" >> %s\n' % target_bin)
          f.write('\t@echo \'python %s $$@\' >> %s\n' % (main, target_bin))
          f.write('\tchmod 754 %s\n' % target_bin)
        f.write('\t@ln -s -f %s $(BINDIR)/$(notdir $@)\n' % target_bin)
        f.write('\t@echo "Created: %s"\n' % target_bin)

      f.write('\t@echo "Finished: $@"\n\n')
      f.write('\n\n')
    f.close()
