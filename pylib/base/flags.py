"""Flags."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import argparse

# HACK(stephen): Force add_subparsers to be backwards compatible since this
# broke in Python 3.
def build_parser():
    parser = argparse.ArgumentParser(conflict_handler='resolve',
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Workaround based on: https://stackoverflow.com/a/22994500
    _add_subparsers = parser.add_subparsers
    def add_subparsers(*args, **kwargs):
        subparser = _add_subparsers(dest='', *args, **kwargs)
        subparser.required = True
        return subparser
    parser.add_subparsers = add_subparsers
    return parser

class Flags:
  """Class to manage command line flags."""
  ARGS = argparse.Namespace()
  PARSER = build_parser()
  TESTING = False

  @classmethod
  def InitArgs(cls):
    cls.ARGS = cls.PARSER.parse_args()

# TODO(pramodg): See if we can replace testing above with an argument.
# Flags.PARSER.add_argument('-t', '--testing', action='store_true', default=False,
#                        help='Testing mode.')
