"""
Handles angular unit test rules parsing
"""
__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import os
import socket
import sys

from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.base.exec_utils import ExecUtils
from pylib.file.file_utils import FileUtils
from pylib.file.parse_include_list import ParseIncludeList

from make_rules import MakeRules
from sets import Set
from utils import Utils

Flags.PARSER.add_argument('--nge2e_timeout', type=int, default=30,
                          help='Timeout for phantom NG test (seconds).')

Flags.PARSER.add_argument('--nge2e_template', default='pylib/flash/templates/nge2e_tmpl.html',
                          help='Location of the ng template')

Flags.PARSER.add_argument('--nge2e_replace_str', default='==ADD_JS_HERE==',
                          help='The string to replace in the template file')

class NGe2eRules(MakeRules):
  """Class to manage different functions related to parsing of ng unit test rules."""

  @classmethod
  def PhantomJSCmd(cls):
    """Returns the phantomjs command to execute a given test."""
    return 'phantomjs --ignore-ssl-errors=yes $(SRCROOT)/js/lib/angular-runner.js'

  @classmethod
  def GenerateTemplateJs(cls, srcs, deps):
    """
    Given a test file and dependencies, generate the javascript to be
    injected into the template
    @param srcs - array of test filenames
    @param deps - array of filename dependencies
    @return {String} the javascript to be injected into the template
    """
    tmpl = '<script src="%s"></script>\n'
    all_deps = []
    for dep in deps:
      pil = ParseIncludeList(dep)
      files = pil.get_files()
      for f in files:
        # dedup. ensure files are included at most once
        if not f in all_deps:
          all_deps.append(f)
    dep_tmpl = ''.join([ tmpl % dep for dep in all_deps])
    return dep_tmpl + ''.join([ tmpl % ('/' + FileUtils.FromAbsoluteToRepoRootPath(src)) \
                                  for src in srcs])

  @classmethod
  def WriteMakefile(cls, specs, makefile):
    """Writes the auto make file for the given spec.
    Args:
      specs: List of dict of type {target, target_type, src, urls, ...}.
          Each dict contains everything needed to build 'target'
      makefile: The (auto) makefile to generate.
    """
    f = open(makefile, 'w')
    index = 0
    for item in specs:
      index += 1
      target = item['_target']
      target_bin = FileUtils.GetBinPathForFile(target)

      f.write('\n# Srcs for %s\n' % target)
      f.write('NGE2E_SRC_%d = %s\n' %
              (index, str.join('\\\n  ', item.get('src', set()))))

      hostname = socket.gethostname()
      # read in the template and insert the proper javascript
      tmpl_f = open(Flags.ARGS.nge2e_template, 'r')
      tmpl_js = cls.GenerateTemplateJs(item.get('src'), item.get('deps'))
      tmpl = tmpl_f.read()
      test_html_content = tmpl.replace(Flags.ARGS.nge2e_replace_str, tmpl_js)

      timeout = item.get('timeout', Flags.ARGS.nge2e_timeout)
      # Write the target.
      f.write('\n%s' % target)
      f.write(': $(NGE2E_SRC_%d)\n' % (index))
      type = item.get('_type', 'invalid')
      if type == 'nge2e_test':
        # test name
        name = item['name']
        # write the test html
        test_html_fn = os.path.join(FileUtils.GetWebTestHtmlDir(), '%s.html' % name)
        test_html_f = open(test_html_fn, 'w')
        test_html_f.write(test_html_content)
        # the test url
        test_url = 'https://%s%s/%s.html' % (hostname, FileUtils.GetWebTestHtmlUrlPath(), name)
        f.write('\t@echo "Creating Test for %s "\n' % target)
        f.write('\t@mkdir -p $(dir %s)\n' % target_bin)
        f.write('\t@echo "# ng Unit Test for %s" > %s\n' % (target, target_bin))
        f.write('\t@echo \'%s %s "%d" \' >> %s\n' %
                (cls.PhantomJSCmd(), test_url, timeout, target_bin))
        f.write('\tchmod 754 %s\n' % target_bin)
        f.write('\t@ln -s -f %s $(BINDIR)/$(notdir $@)\n' % target_bin)
        f.write('\t@mkdir -p $(dir %s)\n' % test_html_fn)

        f.write('\t@\n')
        f.write('\t@echo "Created: %s"\n' % target_bin)

      f.write('\t@echo "Finished: $@"\n\n')
      f.write('\n\n')
    f.close()
