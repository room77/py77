#!/usr/bin/env python

"""Handles clean."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import os
import sys
import getopt

import r77_init  # pylint: disable=W0611
from pylib.base.exec_utils import ExecUtils
from pylib.base.flags import Flags
from pylib.base.term_color import TermColor

from gen_makefile import GenMakefile
from utils import Utils

class Cleaner:
  """Class to handle clean."""

  @classmethod
  def Init(cls, parser):
    """Initialize the cleaner.
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    parser.add_argument('-a', '--all', action='store_true', default=False,
                        help='Clean BINDIR, non-src files and build cache.')
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='Debug mode.')
    parser.add_argument('-o', '--obj', action='store_true', default=False,
                        help='Cleans BINDIR only.')

  @classmethod
  def Run(cls):
    """Runs the cleaner."""
    return cls.Clean()

  @classmethod
  def Clean(cls):
    """Runs the cleaner.

    Return:
      int: Exit status. 0 means no error.
    """
    gen_makefile = GenMakefile(Flags.ARGS.debug)
    gen_makefile.GenMainMakeFile()

    clean = 'clean'
    if Flags.ARGS.obj:
      clean = 'cleano'
    elif Flags.ARGS.all:
      clean = 'cleanall'

    (status, out) = ExecUtils.RunCmd(
        'make -f %s %s' % (gen_makefile.GetMakeFileName(), clean))

    return status


def main():
  try:
    Cleaner.Init(Flags.PARSER)
    Flags.InitArgs()
    return Cleaner.Run()
  except KeyboardInterrupt as e:
    TermColor.Warning('KeyboardInterrupt')
    return 1


if __name__ == '__main__':
  sys.exit(main())
