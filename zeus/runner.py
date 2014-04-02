#!/usr/bin/env python

"""Handles run."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import itertools
import json
import os
import re
import sys
import time

import r77_init  # pylint: disable=W0611
from pylib.base.flags import Flags
from pylib.base.exec_utils import ExecUtils
from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils
from pylib.util.mail.mailer import Mailer

from pipeline_cmd_base import PipelineCmdBase
from pipeline_config import PipelineConfig
from pipeline_utils import PipelineUtils

class Runner(PipelineCmdBase):
  """Class to handle run."""

  # The different exit codes that can be returned after running a task.
  EXITCODE = {
    '_LOWEST':-1,  # Internal use.
    'SUCCESS': 0,
    'ALLOW_FAIL': 1,
    'FAILURE': 2,
    'ABORT_FAIL': 3,
  }

  EXITCODE_DESCRIPTION = {
    0: 'SUCCESS',
    1: 'ALLOW_FAIL',
    2: 'FAILURE',
    3: 'ABORT_FAIL',
  }

  EXITCODE_FILE = {
    0: 'SUCCESS',
    1: 'SUCCESS',
    2: 'FAILURE',
    3: 'ABORT',
  }

  @classmethod
  def Init(cls, parser):
    super(Runner, cls).Init(parser)
    parser.add_argument('-t', '--timeout', type=float, default=86400,
                        help='Timeout for each task in seconds.')
    parser.add_argument('--pool_size', type=int, default=0,
                        help='The pool size for parallelization.')
    parser.add_argument('--detailed_success_mail', action='store_true', default=False,
                        help='Sends a detailed mail even on success. Useful for debugging.')
    parser.add_argument('--success_mail', type=str, default='',
                        help='The mail to use to send info in case of success.')
    parser.add_argument('--failure_mail', type=str, default='',
                        help='The mail to use to send info in case of success.')

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
    # All our binaries assume they will be run from the source root.
    start = time.time()

    os.chdir(FileUtils.GetSrcRoot())
    cls._CreateDirsForTasks(tasks)

    successful_run = []; failed_run = []
    aborted_task = None

    dirs_status = {}
    for set_tasks in tasks.itervalues():
      if aborted_task:
        failed_run += set_tasks
        continue

      # Run all the tasks at the same priority in parallel.
      args = itertools.izip(itertools.repeat(cls), itertools.repeat('_RunSingeTask'),
                            set_tasks)
      task_res = ExecUtils.ExecuteParallel(args, Flags.ARGS.pool_size)
      # task_res = []
      # for task in set_tasks: task_res += [cls._RunSingeTask(task)]
      if not task_res:
        TermColor.Error('Could not process: %s' % set_tasks)
        failed_run += set_tasks
        continue
      for (res, task) in task_res:
        if res == Runner.EXITCODE['SUCCESS']:
          successful_run += [task]
        elif res == Runner.EXITCODE['FAILURE']:
          failed_run += [task]
        elif res == Runner.EXITCODE['ALLOW_FAIL']:
          failed_run += [task]
        elif res == Runner.EXITCODE['ABORT_FAIL']:
          failed_run += [task]
          aborted_task = task
        else:
          TermColor.Fatal('Invalid return %d code for %s' % (res, task))
        # Update the out dir status.
        out_dir = PipelineUtils.GetOutDirForTask(task)
        if out_dir:
          dirs_status[out_dir] = max(dirs_status.get(out_dir, Runner.EXITCODE['_LOWEST']), res)

    # Write the status files to the dirs.
    cls._WriteDirsStatus(dirs_status)

    # Send the final status mail.
    time_taken = time.time() - start
    cls._SendFinalStatusMail(successful_run, failed_run, aborted_task, time_taken)

    if aborted_task:
      TermColor.Failure('Aborted by task: %s' % aborted_task)

    return (successful_run, failed_run)

  @classmethod
  def _CreateDirsForTasks(cls, tasks):
    """Creates the relevant dirs for tasks.

    Args:
      tasks: OrderedDict {int, set(string)}: Dict from priority to set of tasks to execute at the
          priority. Note: the dict is ordered by priority.

    """
    for set_tasks in tasks.itervalues():
      for task in set_tasks:
        rel_path = PipelineUtils.GetTaskOutputRelativeDir(task)
        PipelineConfig.Instance().CreateAllSubDirsForPath(rel_path)

  @classmethod
  def _RunSingeTask(cls, task):
    """Runs a Single Task.

    Args:
      task: string: The task to run.

    Return:
      (EXITCODE, string): Returns a tuple of the result status and the task.
    """
    TermColor.Info('Executing %s' % PipelineUtils.TaskDisplayName(task))
    task_vars = cls.__GetEnvVarsForTask(task)
    TermColor.VInfo(4, 'VARS: \n%s' % task_vars)

    task_cmd = task
    pipe_output = True
    log_file = PipelineUtils.GetLogFileForTask(task)
    if log_file:
       task_cmd += ' > ' + PipelineUtils.GetLogFileForTask(task) + ' 2>&1'
       pipe_output = False

    timeout = cls.__GetTimeOutForTask(task)
    start = time.time()
    (status, out) = ExecUtils.RunCmd(task_cmd, timeout, pipe_output, task_vars)
    time_taken = time.time() - start
    TermColor.Info('Executed  %s. Took %.2fs' % (PipelineUtils.TaskDisplayName(task), time_taken))
    if status:
      TermColor.Failure('Failed Task: %s' % PipelineUtils.TaskDisplayName(task))
      if task_vars.get('PIPELINE_TASK_ABORT_FAIL', None):
        status_code = Runner.EXITCODE['ABORT_FAIL']
      elif task_vars.get('PIPELINE_TASK_ALLOW_FAIL', None):
        status_code = Runner.EXITCODE['ALLOW_FAIL']
      else:
        status_code = Runner.EXITCODE['FAILURE']
    else:
      status_code = Runner.EXITCODE['SUCCESS']

    cls._SendMailForTask(task, status_code, time_taken, log_file, out)

    # Everything done. Mark the task as successful.
    return (status_code, task)

  @classmethod
  def __GetEnvVarsForTask(cls, task):
    """Returns the env vars for the task.

    Args:
      task: string: The task for which the envvar should be prepared.

    Returns:
      dict {string, string}: The dictionary of IDS to values.
    """
    rel_path = PipelineUtils.GetTaskOutputRelativeDir(task)
    vars = {}
    for k, v in PipelineConfig.Instance().GetAllSubDirsForPath(rel_path).iteritems():
      vars[k] = v
      prev_dir = FileUtils.GetPreviousDatedDir(v)
      if not prev_dir: prev_dir = v
      vars[k + '_PREV'] = prev_dir
    vars.update(PipelineConfig.Instance().GetAllENVVars())

    # Check if the task is critical or not.
    rel_task = PipelineUtils.TaskRelativeName(task)
    if rel_task.find('.abort_fail') != -1: vars['PIPELINE_TASK_ABORT_FAIL'] = '1'
    if rel_task.find('.allow_fail') != -1: vars['PIPELINE_TASK_ALLOW_FAIL'] = '1'
    return vars

  @classmethod
  def __GetTimeOutForTask(cls, task):
    """Returns the timeout for the task.

    Args:
      task: string: The task for which the timeout should be prepared.

    Returns:
      int: The timeout in seconds.
    """
    timeout = FileUtils.FileContents(task + '.timeout')
    if not timeout:
      timeout = FileUtils.FileContents(os.path.join(PipelineUtils.TaskDirName(task), 'timeout'))

    if not timeout: return Flags.ARGS.timeout

    timeout = re.sub('\s*', '', timeout)
    timeout_parts = re.split('(\d+)', timeout)
    if len(timeout_parts) < 3:
      TermColor.Warning('Ignoring invalid timeout [%s] for task: %s' % (timeout, task))
      return Flags.ARGS.timeout

    timeout = float(timeout_parts[1])
    annotation = timeout_parts[2]
    if not annotation: return timeout
    elif annotation == 'd': timeout *= 86400
    elif annotation == 'h': timeout *= 3600
    elif annotation == 'm': timeout *= 60
    elif annotation == 'ms': timeout *= 0.001
    elif annotation == 'us': timeout *= 0.000001
    return timeout

  @classmethod
  def _SendMailForTask(cls, task, status_code, time_taken, log_file, msg):
    """Sends the mail if required for the task.

    Args:
      task: string: The task for which the envvar should be prepared.
      status_code: EXITCODE: The exit code for the task.
      time_taken: float: Time taken in seconds.
      log_file: string: The log file containing the output of the task.
      msg: string: The output message piped directly. Note only one of msg or log_file will be
          present at any time.

    Returns:
      dict {string, string}: The dictionary of IDS to values.
    """
    if status_code == Runner.EXITCODE['SUCCESS']:
      if not Flags.ARGS.detailed_success_mail: return
      receiver = Flags.ARGS.success_mail
    else: receiver = Flags.ARGS.failure_mail

    # Check if there is no receiver for the mail.
    if not receiver: return
    status_description = Runner.EXITCODE_DESCRIPTION[status_code]
    subject = "[%s:%s] %s : %s" % (PipelineConfig.Instance().pipeline_id(),
                                   PipelineConfig.Instance().pipeline_date(),
                                   status_description, PipelineUtils.TaskDisplayName(task))

    body = 'Executed task: %s. \nStatus:%s \nTime: %.2fs.' % (task, status_description, time_taken)
    if msg:
      body += '\n%s' % msg
      Mailer().send_simple_message(PipelineUtils.ZeusEmailId(), [receiver], subject, body)
    else:
      Mailer().send_message_from_files(PipelineUtils.ZeusEmailId(), [receiver], subject, [log_file],
                                       body)

  @classmethod
  def _WriteDirsStatus(cls, dirs_status):
    """Writes the status for each of the dirs in the dict.

    Args:
      dirs_status: dict {string, EXITCODE}: Dict of dir -> exit status.
    """
    for k, v in dirs_status.iteritems():
      FileUtils.RemoveFiles([os.path.join(k, x) for x in Runner.EXITCODE_FILE.itervalues()])
      status_file = Runner.EXITCODE_FILE.get(v, '')
      if not status_file: continue
      FileUtils.CreateFileWithData(os.path.join(k, status_file))

  @classmethod
  def _SendFinalStatusMail(cls, successful_run, failed_run, aborted_task, time_taken):
    """Sends the final status mail if required.

    Args:
      (list, list): Returns a tuple of list in the form
          (successful_tasks, failed_tasks) specifying tasks that succeeded and
          ones that failed.
      aborted_task: string: True if the pipeline was aborted.
      time_taken: float: Time taken in seconds.

    """
    if not successful_run and not failed_run: return

    if not failed_run:
      receiver = Flags.ARGS.success_mail
      status_description = 'SUCCESS'
    else:
      receiver = Flags.ARGS.failure_mail
      status_description = 'ABORT FAIL' if aborted_task else 'FAIL'

    # Check if there is no receiver for the mail.
    if not receiver: return

    subject = "[%s:%s] Final Status: %s" % (PipelineConfig.Instance().pipeline_id(),
                                            PipelineConfig.Instance().pipeline_date(),
                                            status_description)
    body = 'Aborted by: %s\n\n' % aborted_task if aborted_task else ''
    body += ('Successful tasks: %d\n%s\n\n'
             'Failed tasks: %d\n%s\n\n'
             'Total Time: %.2fs.\n'
             '\n%s\n\n' %
             (len(successful_run), json.dumps(successful_run, indent=2),
              len(failed_run), json.dumps(failed_run, indent=2),
              time_taken,
              PipelineConfig.Instance().GetConfigString()))
    Mailer().send_simple_message(PipelineUtils.ZeusEmailId(), [receiver], subject, body)


def main():
  try:
    Runner.Init(Flags.PARSER)
    Flags.InitArgs()
    return Runner.Run()
  except KeyboardInterrupt as e:
    TermColor.Warning('KeyboardInterrupt')
    return 1


if __name__ == '__main__':
  sys.exit(main())
