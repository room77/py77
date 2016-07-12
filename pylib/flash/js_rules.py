"""Manages different functions related to js rules parsing."""

__author__ = 'pramodg@room77.com (Pramod Gupta), edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'


from pylib.base.flags import Flags

from url_rules_base import UrlRulesBase

Flags.PARSER.add_argument('--qunit_timeout', type=int, default=10,
                          help='Timeout for phantom JS test (seconds).')

class JSRules(UrlRulesBase):
  """Class to manage different functions related to parsing of js rules."""
  """phantomjs --ignore-ssl-errors=yes [root_dir]/js/lib/qunit-runner.js [url] [timeout]"""

  @classmethod
  def PhantomJSCmd(cls):
    """@override"""
    return 'phantomjs --ignore-ssl-errors=yes $(SRCROOT)/js/lib/qunit-runner.js'

  @classmethod
  def UrlParam(cls):
    """@override"""
    return 'qunit'

  @classmethod
  def GetDefaultTimeout(cls):
    """@override"""
    return Flags.ARGS.qunit_timeout

  @classmethod
  def GetTestType(cls):
    """@override"""
    return "js_test"
