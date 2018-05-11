#!/usr/bin/env python

"""Handles test."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import sys

from pylib.base.flags import Flags
from pylib.base.term_color import TermColor

from pylib.flash.run import Runner
from pylib.flash.utils import Utils

class Tester(Runner):
  """Class to handle test."""

  @classmethod
  def Init(cls, parser):
    super(Tester, cls).Init(parser)
    parser.set_defaults(
        allowed_rule_types=['cc_test', 'js_test', 'ng_test', 'nge2e_test', 'py_test'],
        timeout=600)

def main():
  try:
    Tester.Init(Flags.PARSER)
    Flags.InitArgs()
    return Tester.Run()
  except KeyboardInterrupt as e:
    TermColor.Warning('KeyboardInterrupt')
    return 1


if __name__ == '__main__':
  sys.exit(main())
