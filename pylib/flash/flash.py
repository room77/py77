#!/usr/bin/env python

"""Main file that handles different build operations."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import argparse
import sys
import time

from pylib.base.flags import Flags
from pylib.base.term_color import TermColor

from pylib.flash.build import Builder
from pylib.flash.clean import Cleaner
from pylib.flash.dep_graph import DepGraph
from pylib.flash.run import Runner
from pylib.flash.test import Tester


class Flash:
  """Main class to handle all commands.
  """
  # List of supported commands.
  SUPPORTED_CMDS = ['build', 'clean', 'cleanall', 'cleano', 'run', 'test',
                    'depgraph', 'help']
  def Run(self):
    self._Init()

    start = time.time()
    try:
      status = Flags.ARGS.func()
    except KeyboardInterrupt as e:
      TermColor.Warning('KeyboardInterrupt')
      status = 1
    duration = 'Took %.2fs' % (time.time() - start)
    if not status:
      TermColor.Success(duration)
    else:
      TermColor.Failure(duration)

    return status

  def _Init(self):
    subparsers = Flags.PARSER.add_subparsers()
    for cmd in self.SUPPORTED_CMDS:
      parser = subparsers.add_parser(cmd, conflict_handler='resolve',
          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
      handler = self._GetHandler(cmd, 'init')
      if handler: handler(parser)
      parser.set_defaults(func=self._GetHandler(cmd, 'run'))

    Flags.InitArgs()

  def _GetHandler(self, command, type):
    return getattr(self, '_Handle_' + command.lower() + '_' + type, None);

  def _Handle_build_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    Builder.Init(parser)

  def _Handle_build_run(self):
    return Builder.Run();

  def _Handle_clean_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    Cleaner.Init(parser)

  def _Handle_clean_run(self):
    return Cleaner.Run();

  def _Handle_cleano_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    return self._Handle_clean_init(parser)

  def _Handle_cleano_run(self):
    Flags.ARGS.obj = True
    return self._Handle_clean_run()

  def _Handle_cleanall_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    return self._Handle_clean_init(parser)

  def _Handle_cleanall_run(self):
    Flags.ARGS.all = True
    return self._Handle_clean_run()

  def _Handle_depgraph_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    pass
    DepGraph.Init(parser)

  def _Handle_depgraph_run(self):
    return DepGraph.Run()

  def _Handle_help_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    parser.add_argument('cmd', type=str, default='build',
                        help='Cmd for which help is to be generated.')

  def _Handle_help_run(self):
    Flags.PARSER.parse_args([Flags.ARGS.cmd, '-h'])
    return 0

  def _Handle_run_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    Runner.Init(parser)

  def _Handle_run_run(self):
    return Runner.Run()

  def _Handle_test_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    Tester.Init(parser)
    pass

  def _Handle_test_run(self):
    return Tester.Run()


def main():
  flash = Flash()
  return flash.Run()


if __name__ == '__main__':
  sys.exit(main())
