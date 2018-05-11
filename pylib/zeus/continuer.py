#!/usr/bin/env python

"""Handles continue."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

from collections import OrderedDict
import json
import os
import sys

from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils

from pylib.zeus.runner import Runner
from pylib.zeus.pipeline_config import PipelineConfig
from pylib.zeus.pipeline_utils import PipelineUtils


class Continuer(Runner):
  """Class to handle continueing the tasks by using the data for already successful tasks."""

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
    already_successful = []
    tasks_to_run = OrderedDict()
    for priority, set_tasks in list(tasks.items()):
      new_task_set = set()
      for task in set_tasks:
        out_dir = PipelineUtils.GetOutDirForTask(task)
        if out_dir and os.path.exists(os.path.join(out_dir, 'SUCCESS')):
          already_successful += [task]
          continue
        new_task_set |= set([task])
      if new_task_set:
        tasks_to_run[priority] = new_task_set

    TermColor.Info('Tasks already successful: %d\n%s' % (len(already_successful),
        json.dumps(PipelineUtils.TasksDisplayNames(already_successful), indent=2)))
    if not tasks_to_run: return (already_successful, [])

    # Run the remaining tasks.
    (successful_run, failed_run) = super(Continuer, cls).WorkHorse(tasks_to_run)
    return (successful_run + already_successful, failed_run)


def main():
  try:
    Continuer.Init(Flags.PARSER)
    Flags.InitArgs()
    return Continuer.Run()
  except KeyboardInterrupt as e:
    TermColor.Warning('KeyboardInterrupt')
    return 1


if __name__ == '__main__':
  sys.exit(main())
