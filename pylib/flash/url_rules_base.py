"""
Base class for tests that run form a url target
Let url => test url
    url_params  => test url params
    test_param  => url param of the test
    hash_params => hash param of the test
    test_src => test source file
The test url is expected to be executed by the runner
in the following form:
url?url_param&test_param=test_src
OR
url?url_param#hash_params&test_param=test_src
"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import json
import socket

# Python 2/3 compatibility
try:
  from urllib.parse import quote # Python 3
except ImportError:
  from urllib import quote # Python 2

from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils
from pylib.base.exec_utils import ExecUtils

from pylib.flash.make_rules import MakeRules

class UrlRulesBase(MakeRules):

  @classmethod
  def PhantomJSCmd(cls):
    """The phantom js command to run"""
    TermColor.Fatal('Abstract base called. Not supported!')

  @classmethod
  def UrlParam(cls):
    """return the url param to search for"""
    TermColor.Fatal('Abstract base called. Not supported!')

  @classmethod
  def GetDefaultTimeout(cls):
    """return the default test timeout in seconds"""
    TermColor.Fatal('Abstract base called. Not supported!')

  @classmethod
  def GetTestType(cls):
    """return the name of this test type in this rules file"""
    TermColor.Fatal('Abstract base called. Not supported!')

  @classmethod
  def WriteMakefile(cls, specs, makefile):
    """Writes the auto make file for the given spec.
    Args:
      specs: List of dict of type {target, target_type, src, urls, ...}.
          Each dict contains everything needed to build 'target'
      makefile: The (auto) makefile to generate.
    """
    url_param = cls.UrlParam()
    f = open(makefile, 'w')
    index = 0
    for item in specs:
      index += 1
      target = item['_target']
      target_bin = FileUtils.GetBinPathForFile(target)

      f.write('\n# Srcs for %s\n' % target)
      f.write('JS_SRC_%d = %s\n' %
              (index, str.join('\\\n  ', item.get('src', set()))))

      hostname = socket.gethostname()
      tests = set(item.get('test', set()))
      urls = []
      for test in tests:
        test_dict = {}
        test_dict['test'] = test
        if 'src' in item:
          test_dict['dep'] = ['/%s' % \
            FileUtils.FromAbsoluteToRepoRootPath(src) for src in item['src']]
          if test in test_dict['dep']:
            test_dict['dep'].remove(test)
        for url in item['urls']:
          components = url.split('#')
          unit = "&%s" % url_param
          # if empty string remove the ampersand
          if len(components) > 0 and not components[0]:
            unit = "%s" % url_param
          # if no url param add the question mark
          if len(url.split('?')) == 1:
            unit = "?%s" % url_param
          # equivalent to encodeuricomponent see:
          # http://stackoverflow.com/questions/946170/equivalent-javascript-functions-for-pythons-urllib-quote-and-urllib-unquote
          test_json = quote(json.dumps(test_dict), safe='~()*!.\'')
          # build the urls
          if len(components) == 1:
            urls.append('https://%s/%s%s=%s' % (hostname, components[0], unit,
                                                test_json))
          elif len(components) == 2:
            urls.append('https://%s/%s%s=%s#%s' % \
              (hostname, components[0], unit, test_json,
               components[1]))
          else:
            TermColor.Fatal("Unable to parse URL: %s" % url)

      timeout = item.get('timeout', cls.GetDefaultTimeout())
      # Write the target.
      f.write('\n%s' % target)
      f.write(': $(JS_SRC_%d)\n' % (index))
      type = item.get('_type', 'invalid')
      if type == cls.GetTestType():
        f.write('\t@echo "Creating Test for %s "\n' % target)
        f.write('\t@mkdir -p $(dir %s)\n' % target_bin)
        f.write('\t@echo "# JS Test for %s" > %s\n' % (target, target_bin))
        for url in urls:
          f.write('\t@echo \'%s "%s" "%d" $$@\' >> %s\n' %
                  (cls.PhantomJSCmd(), url, timeout, target_bin))
        f.write('\tchmod 754 %s\n' % target_bin)
        f.write('\t@ln -s -f %s $(BINDIR)/$(notdir $@)\n' % target_bin)
        f.write('\t@echo "Created: %s"\n' % target_bin)

      f.write('\t@echo "Finished: $@"\n\n')
      f.write('\n\n')
    f.close()
