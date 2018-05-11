"""Manages different functions related to js rules parsing."""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'


from pylib.base.flags import Flags

from pylib.flash.url_rules_base import UrlRulesBase

Flags.PARSER.add_argument('--ng_timeout', type=int, default=10,
                          help='Timeout for phantom JS test (seconds).')

class NGRules(UrlRulesBase):
  """Class to manage different functions related to parsing of ng rules."""

  @classmethod
  def PhantomJSCmd(cls):
    """@override"""
    return 'phantomjs --ignore-ssl-errors=yes $(SRCROOT)/js/lib/jasmine-runner.js'

  @classmethod
  def UrlParam(cls):
    """@override"""
    return 'jasmine'

  @classmethod
  def GetDefaultTimeout(cls):
    """@override"""
    return Flags.ARGS.ng_timeout

  @classmethod
  def GetTestType(cls):
    """@override"""
    return "ng_test"
