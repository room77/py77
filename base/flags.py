"""Flags."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import argparse

class Flags:
  """Class to manage command line flags."""
  ARGS = argparse.Namespace()
  PARSER = argparse.ArgumentParser(conflict_handler='resolve',
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  TESTING = False

  @classmethod
  def InitArgs(cls):
    cls.ARGS = cls.PARSER.parse_args()

# TODO(pramodg): See if we can replace testing above with an argument.
# Flags.PARSER.add_argument('-t', '--testing', action='store_true', default=False,
#                        help='Testing mode.')
