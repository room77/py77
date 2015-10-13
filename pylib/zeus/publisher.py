#!/usr/bin/env python

"""Handles publish."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import os
import sys

import r77_init  # pylint: disable=W0611
from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils

from pipeline_cmd_base import PipelineCmdBase
from pipeline_config import PipelineConfig
from pipeline_utils import PipelineUtils

class Publisher(PipelineCmdBase):
  """Class to handle publishing the dirs for the pipeline date."""

  # The different exit codes that can be returned after running a task.
  EXITCODE = {
    'SUCCESS': 0,
    'FAILURE': 1,
  }

  @classmethod
  def Init(cls, parser):
    super(Publisher, cls).Init(parser)
    parser.add_argument('--pool_size', type=int, default=0,
                        help='The pool size for parallelization.')

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
    all_tasks = []
    dirs_to_publish = set()
    publish_dir_to_task_map = {}
    for set_tasks in tasks.itervalues():
      for task in set_tasks:
        all_tasks += [task]
        publish_dir = PipelineUtils.GetPublishDirForTask(task)
        if not publish_dir: continue
        dirs_to_publish |= set([publish_dir])
        publish_dir_to_task_map[publish_dir] = (publish_dir_to_task_map.get(publish_dir, []) +
                                                [publish_dir])

    # Check if there are any directories to publish.
    if not dirs_to_publish:
      TermColor.Error('Did not find any dirs to publish. Do not forget to specify publish root '
                      'using --publish_root')
      return ([], all_tasks)

    # Run all the copy tasks.
    successful_dirs = []; failed_dirs = []
    for dir in dirs_to_publish:
      publish_dir = cls._GetActualPublishDir(dir)
      if not publish_dir:
        failed_dirs += [publish_dir]
        continue
      (parent, name) = os.path.split(publish_dir)
      TermColor.Info('Making current: %s' % publish_dir)
      with FileUtils.PushDir(parent):
        FileUtils.CreateLink('current', name)
      successful_dirs += [publish_dir]

    # Get the reverse mapping from dirs to tasks.
    successful_tasks = []; failed_tasks = []
    for i in successful_dirs:
      successful_tasks += publish_dir_to_task_map.get(i, [])

    for i in failed_dirs:
      failed_tasks += publish_dir_to_task_map.get(i, [])

    return (successful_tasks, failed_tasks)

  @classmethod
  def _GetActualPublishDir(cls, publish_dir_hint):
    """Returns the actual publish dir statring at the hinted dir. If the directory does not contain
    'SUCCESS', previous siblings are checked to get the publishable directory.

    Args:
      publish_dir_hint: string: The publish dir hint.

    Return:
      string: Actual publish dir.
    """
    if not publish_dir_hint: return None
    if os.path.exists(os.path.join(publish_dir_hint, 'SUCCESS')): return publish_dir_hint
    return PipelineUtils.GetPrevDatedDirCotainingPattern(publish_dir_hint, 'SUCCESS')


def main():
  try:
    Publisher.Init(Flags.PARSER)
    Flags.InitArgs()
    return Publisher.Run()
  except KeyboardInterrupt as e:
    TermColor.Warning('KeyboardInterrupt')
    return 1


if __name__ == '__main__':
  sys.exit(main())
