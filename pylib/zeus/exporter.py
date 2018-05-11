#!/usr/bin/env python

"""Handles export."""

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

from pylib.zeus.pipeline_cmd_base import PipelineCmdBase
from pylib.zeus.pipeline_config import PipelineConfig
from pylib.zeus.pipeline_utils import PipelineUtils

class Exporter(PipelineCmdBase):
  """Class to handle export of the output directory to a public location."""

  # The different exit codes that can be returned after running a task.
  EXITCODE = {
    'SUCCESS': 0,
    'FAILURE': 1,
  }

  @classmethod
  def Init(cls, parser):
    super(Exporter, cls).Init(parser)
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
    dirs_to_export = set()
    out_dir_to_task_map = {}
    for set_tasks in tasks.values():
      for task in set_tasks:
        all_tasks += [task]
        out_dir = PipelineUtils.GetOutDirForTask(task)
        if not out_dir: continue
        dirs_to_export |= set([out_dir])
        out_dir_to_task_map[out_dir] = out_dir_to_task_map.get(out_dir, []) + [out_dir]

    # Check if there are any directories to copy.
    if not dirs_to_export:
      TermColor.Error('Did not find any dirs to export.')
      return ([], all_tasks)

    # Check if there is a dir to publish to.
    if not PipelineConfig.Instance().pipeline_publish_dir():
      TermColor.Error('Must specify the publish root using --publish_root.')
      return ([], all_tasks)

    # Create the list of source and publish dirs.
    # At the same time, check if the pipeline was aborted. We do not export aborted pipelines.
    out_dir_base = PipelineUtils.GetOutSubDir()
    src_dirs = []; target_dirs = []
    for dir in dirs_to_export:
      src_dirs += [dir]
      target_dirs += [dir.replace(out_dir_base, PipelineConfig.Instance().pipeline_publish_dir())]
      if os.path.exists(os.path.join(dir, 'ABORT')):
        TermColor.Error('Pipeline was aborted for dir: %s' % dir)
        return ([], all_tasks)

    # Create all the dirs to publish.
    for dir in target_dirs:
      FileUtils.MakeDirs(dir)

    # Run all the copy tasks.
    successful_dirs = []; failed_dirs = []
    args = zip(itertools.repeat(cls), itertools.repeat('_RunSingeTask'),
                          src_dirs, target_dirs)
    dir_res = ExecUtils.ExecuteParallel(args, Flags.ARGS.pool_size)
    if not dir_res:
      TermColor.Error('Could not process: %s' % all_tasks)
      return ([], all_tasks)

    for (res, dir) in dir_res:
      if res == Exporter.EXITCODE['SUCCESS']:
        successful_dirs += [dir]
      elif res == Exporter.EXITCODE['FAILURE']:
        failed_dirs += [dir]
      else:
        TermColor.Fatal('Invalid return %d code for %s' % (res, dir))

    # Get the reverse mapping from dirs to tasks.
    successful_tasks = []; failed_tasks = []
    for i in successful_dirs:
      successful_tasks += out_dir_to_task_map.get(i, [])

    for i in failed_dirs:
      failed_tasks += out_dir_to_task_map.get(i, [])

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
    status_code = Exporter.EXITCODE['FAILURE'] if not res else Exporter.EXITCODE['SUCCESS']
    TermColor.Info('Finished copying %s to %s : Took %.2fs' % (src_dir, target_dir, time_taken))

    # Everything done. Mark the task as successful.
    return (status_code, src_dir)


def main():
  try:
    Exporter.Init(Flags.PARSER)
    Flags.InitArgs()
    return Exporter.Run()
  except KeyboardInterrupt as e:
    TermColor.Warning('KeyboardInterrupt')
    return 1


if __name__ == '__main__':
  sys.exit(main())
