#!/usr/bin/env python

"""Main file that handles different pipeline operations."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import argparse
import sys
import time

import pylib.zeus.cleaner as cleaner
import pylib.zeus.continuer as continuer
import pylib.zeus.exporter as exporter
import pylib.zeus.importer as importer
import pylib.zeus.pipeline_config as pc
import pylib.zeus.publisher as publisher
import pylib.zeus.runner as runner

from pylib.base.flags import Flags
from pylib.base.term_color import TermColor

class Zeus(object):
  """Main class to handle all pipeline commands."""
  # List of supported commands.
  SUPPORTED_CMDS = ['clean', 'continue', 'export', 'import', 'publish', 'run', 'help']

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

    # Get the pipeline config instance after all args have been set up.
    pc.PipelineConfig.Instance()

  def _GetHandler(self, command, type):
    return getattr(self, '_Handle_' + command.lower() + '_' + type, None);

  def _Handle_clean_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    cleaner.Cleaner.Init(parser)

  def _Handle_clean_run(self):
    return cleaner.Cleaner.Run();


  def _Handle_continue_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    continuer.Continuer.Init(parser)

  def _Handle_continue_run(self):
    return continuer.Continuer.Run();

  def _Handle_export_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    exporter.Exporter.Init(parser)

  def _Handle_export_run(self):
    return exporter.Exporter.Run();

  def _Handle_import_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    importer.Importer.Init(parser)

  def _Handle_import_run(self):
    return importer.Importer.Run();

  def _Handle_publish_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    publisher.Publisher.Init(parser)

  def _Handle_publish_run(self):
    return publisher.Publisher.Run();

  def _Handle_run_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    runner.Runner.Init(parser)

  def _Handle_run_run(self):
    return runner.Runner.Run();

  def _Handle_help_init(self, parser):
    """
    Args:
      parser: ArgumentParser: The argument parser for the command.
    """
    parser.add_argument('cmd', type=str, default='refresh',
                        help='Cmd for which help is to be generated.')

  def _Handle_help_run(self):
    Flags.PARSER.parse_args([Flags.ARGS.cmd, '-h'])
    return 0


def main():
  zeus = Zeus()
  return zeus.Run()


if __name__ == '__main__':
  sys.exit(main())
