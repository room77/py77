#!/usr/bin/env python

"""Handles clean."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import os
import shutil
import sys

from pylib.base.flags import Flags
from pylib.file.file_utils import FileUtils
from pylib.base.term_color import TermColor

from pylib.zeus.pipeline_cmd_base import PipelineCmdBase
from pylib.zeus.pipeline_config import PipelineConfig
from pylib.zeus.pipeline_utils import PipelineUtils


class Cleaner(PipelineCmdBase):
  """Class to handle clean."""

  @classmethod
  def Init(cls, parser):
    super(Cleaner, cls).Init(parser)
    parser.add_argument('--all', action='store_true', default=False,
                        help='Cleans all subdirs. Note this can be very dangerous!')

  @classmethod
  def Run(cls):
    """Runs the command handler.

    Return:
      int: Exit status. 0 means no error.
    """
    if not Flags.ARGS.all:
      return super(Cleaner, cls).Run()

    TermColor.Info('Cleaning entire output tree: %s' %
                    PipelineConfig.Instance().pipeline_output_dir())
    shutil.rmtree(PipelineConfig.Instance().pipeline_output_dir(), True)
    return 0

  @classmethod
  def WorkHorse(cls, tasks):
    """Runs the workhorse for the command.

    Args:
      tasks: OrderedDict {int, set(string)}: Dict from priority to set of tasks to execute at the
          priority. Note: the dict is ordered by priority.


    Return:
      (list, list): Returns a tuple of list in the form
          (successful_tasks, failed_tasks) specifying tasks that succeeded and
          ones that failed.
    """
    success_tasks = []
    paths_to_clean = set()
    for set_tasks in tasks.values():
      for task in set_tasks:
        paths = PipelineConfig.Instance().GetAllSubDirsForPath(
            PipelineUtils.GetTaskOutputRelativeDir(task))
        paths_to_clean |= set(paths.values())
        success_tasks += [task]

    TermColor.VInfo(1, 'Cleaning %d' % len(paths_to_clean))
    for i in paths_to_clean:
      TermColor.VInfo(3, 'Cleaning %s' % i)
      shutil.rmtree(i, True)

    return (success_tasks, [])


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
