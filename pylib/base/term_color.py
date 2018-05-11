"""Terminal Logging implementation."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import re
import sys
import traceback

from pylib.base.flags import Flags

Flags.PARSER.add_argument('-v', '--verbose', type=int, default=0,
                          help='Verbosity level.')

class TermColor:
  """Class for manipulating terminal colors."""

  CODE = {
    'ENDC': 0,  # RESET COLOR
    'BOLD': 1,
    'UNDERLINE': 4,
    'BLINK': 5,
    'INVERT': 7,
    'CONCEALD': 8,
    'STRIKE': 9,
    'GREY30': 90,
    'GREY40': 2,
    'GREY65': 37,
    'GREY70': 97,
    'GREY20_BG': 40,
    'GREY33_BG': 100,
    'GREY80_BG': 47,
    'GREY93_BG': 107,
    'DARK_RED': 31,
    'RED': 91,
    'RED_BG': 41,
    'LIGHT_RED_BG': 101,
    'DARK_YELLOW': 33,
    'YELLOW': 93,
    'YELLOW_BG': 43,
    'LIGHT_YELLOW_BG': 103,
    'DARK_BLUE': 34,
    'BLUE': 94,
    'BLUE_BG': 44,
    'LIGHT_BLUE_BG': 104,
    'DARK_MAGENTA': 35,
    'PURPLE': 95,
    'MAGENTA_BG': 45,
    'LIGHT_PURPLE_BG': 105,
    'DARK_CYAN': 36,
    'AUQA': 96,
    'CYAN_BG': 46,
    'LIGHT_AUQA_BG': 106,
    'DARK_GREEN': 32,
    'GREEN': 92,
    'GREEN_BG': 42,
    'LIGHT_GREEN_BG': 102,
    'BLACK': 30,
  }

  @staticmethod
  def TermCode(num):
      return '\033[%sm' % num

  @staticmethod
  def ColorStr(s, color):
      return (TermColor.TermCode(TermColor.CODE[color]) + s +
              TermColor.TermCode(TermColor.CODE['ENDC']))

  @staticmethod
  def PrintStr(s, color, print_trace=True):
    if print_trace:
     caller = traceback.extract_stack()[-3]
     s = (caller[0] + ':' + str(caller[1]) + ': ' + s)

    if sys.stdout.isatty():
      s = TermColor.ColorStr(s, color)

    print(s)

  @staticmethod
  def Fatal(s):
    TermColor.PrintStr('FATAL: ' + s, 'RED_BG')
    traceback.print_stack()
    exit(1)

  @staticmethod
  def PrintException(s):
    TermColor.PrintStr('Exception: ' + s, 'DARK_RED')
    traceback.print_exc()

  @staticmethod
  def Error(s, print_stack=False):
    TermColor.PrintStr('ERROR: ' + s, 'DARK_RED')
    if print_stack: traceback.print_stack()

  @staticmethod
  def Warning(s):
    TermColor.PrintStr('WARNING: ' + s, 'PURPLE')

  @staticmethod
  def Notice(s):
    TermColor.PrintStr(s, 'ENDC')

  @staticmethod
  def Info(s):
    TermColor.PrintStr(s, 'ENDC', False)

  @staticmethod
  def VInfo(level, s):
    if level > Flags.ARGS.verbose: return
    TermColor.Info(s)

  @staticmethod
  def VNotice(level, s):
    if level > Flags.ARGS.verbose: return
    TermColor.Notice(s)

  @staticmethod
  def Debug(s):
    TermColor.PrintStr('DEBUG: ' + s, 'BLUE')

  @staticmethod
  def Success(s):
    TermColor.PrintStr('SUCCESS: ' + s, 'GREEN', False)

  @staticmethod
  def Failure(s):
    TermColor.PrintStr('FAILURE: ' + s, 'RED', False)
