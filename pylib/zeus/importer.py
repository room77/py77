#!/usr/bin/env python

"""Handles import."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import itertools
import os
import sys
import time

from pylib.base.flags import Flags
from pylib.base.exec_utils import ExecUtils
from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils

from pipeline_cmd_base import PipelineCmdBase
from pipeline_config import PipelineConfig
from pipeline_utils import PipelineUtils

class Importer(PipelineCmdBase):
  """Class to handle import of the output directory to a public location."""

  # The different exit codes that can be returned after running a task.
  EXITCODE = {
    'SUCCESS': 0,
    'FAILURE': 1,
  }

  @classmethod
  def Init(cls, parser):
    super(Importer, cls).Init(parser)
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
    dirs_to_import = {}
    dir_to_task_map = {}
    for set_tasks in tasks.itervalues():
      for task in set_tasks:
        all_tasks += [task]
        out_dir = PipelineUtils.GetOutDirForTask(task)
        publish_dir = PipelineUtils.GetPublishCurrentDirForTask(task)
        if not out_dir or not publish_dir: continue
        dirs_to_import[publish_dir] = out_dir
        dir_to_task_map[publish_dir] = (dir_to_task_map.get(publish_dir, []) + [publish_dir])

    # Check if there are any directories to publish.
    if not dirs_to_import:
      TermColor.Error('Did not find any dirs to import. Do not forget to specify publish root '
                      'using --publish_root')
      return ([], all_tasks)

    # Create all the target dirs to import to.
    for dir in dirs_to_import.itervalues():
      FileUtils.MakeDirs(dir)

    # Run all the copy tasks.
    successful_dirs = []; failed_dirs = []
    args = itertools.izip(itertools.repeat(cls), itertools.repeat('_RunSingeTask'),
                          dirs_to_import.keys(), dirs_to_import.values())
    dir_res = ExecUtils.ExecuteParallel(args, Flags.ARGS.pool_size)
    if not dir_res:
      TermColor.Error('Could not process: %s' % all_tasks)
      return ([], all_tasks)

    for (res, dir) in dir_res:
      if res == Importer.EXITCODE['SUCCESS']:
        successful_dirs += [dir]
      elif res == Importer.EXITCODE['FAILURE']:
        failed_dirs += [dir]
      else:
        TermColor.Fatal('Invalid return %d code for %s' % (res, dir))

    # Get the reverse mapping from dirs to tasks.
    successful_tasks = []; failed_tasks = []
    for i in successful_dirs:
      successful_tasks += dir_to_task_map.get(i, [])

    for i in failed_dirs:
      failed_tasks += dir_to_task_map.get(i, [])

    return (successful_tasks, failed_tasks)

  @classmethod
  def _RunSingeTask(cls, src_dir, target_dir):
    """Runs a Single Task.

    Args:
      src dir: string: The src directory.
      target dir: string: The target directory.

    Return:
      (EXITCODE, string): Returns a tuple of the result status and the src_dir.
    """
    TermColor.Info('Copying %s to %s' % (src_dir, target_dir))
    start = time.time()
    res = FileUtils.CopyDirTree(src_dir, target_dir)
    time_taken = time.time() - start
    status_code = Importer.EXITCODE['FAILURE'] if not res else Importer.EXITCODE['SUCCESS']
    TermColor.Info('Finished copying %s to %s. Took %.2fs' % (src_dir, target_dir, time_taken))

    # Everything done. Mark the task as successful.
    return (status_code, src_dir)


def main():
  try:
    Importer.Init(Flags.PARSER)
    Flags.InitArgs()
    return Importer.Run()
  except KeyboardInterrupt as e:
    TermColor.Warning('KeyboardInterrupt')
    return 1


if __name__ == '__main__':
  sys.exit(main())
