
"""Util file for the different pipeline operations."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import glob
import os
import socket

from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils
from pylib.zeus.pipeline_config import PipelineConfig

class PipelineUtils:
  """Utility class."""

  @classmethod
  def TaskNormalizedName(cls, task):
    """Returns the normalized name for the task.
    Args:
      task: string: The task to normalize.

    Return:
      string: The Normalized name of the task.
    """
    abs_path = FileUtils.GetAbsPathForFile(task)
    if abs_path: return abs_path
    return task

  @classmethod
  def TaskRelativeName(cls, task):
    """Returns the relative name for the task w.r.t the src dir.
    Args:
      task: string: The task for which the relative name is required.

    Return:
      string: The relative name of the task.
    """
    if not task: return None
    return os.path.relpath(cls.TaskNormalizedName(task),
                           PipelineConfig.Instance().pipeline_base_dir())

  @classmethod
  def TaskDisplayName(cls, task):
    """Returns the display name for the task.
    Args:
      task: string: The task to display.

    Return:
      string: The display name of the task.
    """
    if not task: return None
    return '//' + cls.TaskRelativeName(task)

  @classmethod
  def TaskBaseName(cls, task):
    """Returns the base name for the task.
    Args:
      task: string: The task for which the base name is required.

    Return:
      string: The base name of the task.
    """
    if not task: return None
    return os.path.basename(task)

  @classmethod
  def TaskDirName(cls, task):
    """Returns the dir name for the task.
    Args:
      task: string: The task for which the base name is required.

    Return:
      string: The dir name of the task.
    """
    if not task: return None
    return os.path.dirname(task)


  @classmethod
  def TasksDisplayNames(cls, tasks):
    """Returns the display name for a list of tasks.
    Args:
      tasks: list: List of tasks to display.

    Return:
      list: The display name of the tasks.
    """
    return [cls.TaskDisplayName(task) for task in tasks]

  @classmethod
  def GetTaskPriority(cls, task):
    """Returns the priority of the task.
    Args:
      task: string: The task for which the priority is to be computed.

    Return:
      string: The priority for the task.
    """
    if not task: return None

    task = cls.TaskRelativeName(task)

    priority = ''
    parts = task.split(os.sep)
    for part in parts:
      priority_name = part.split('_', 1)
      if len(priority_name) < 2 or not priority_name[0].isdigit(): return None
      priority += priority_name[0]
    return priority

  @classmethod
  def GetTaskOutputRelativeDir(cls, task):
    """Returns the output directory for the task. This removes all priority info from the task.
    This path is intended for use as input to CreateAllSubDirsForPath() which can generate the
    relevant output dirs for the path.

    Args:
      task: string: The task for which the output relative dir needs to be prepared.

    Return:
      string: The priority for the task.
    """
    task = os.path.dirname(cls.TaskRelativeName(task))
    if not task: return ''

    parts = task.split(os.sep)
    res_parts = []
    for part in parts:
      priority_name = part.split('_', 1)
      res_parts += [priority_name[1]]
    return os.sep.join(res_parts)

  @classmethod
  def GetOutSubDir(cls):
    """Returns the out dir base for the pipeline.

    Returns:
      string: the out dir base for the pipeline. '' if there is no out dir.
    """
    return PipelineConfig.Instance().pipeline_subdirs().get('PIPELINE_OUT_DIR', '')

  @classmethod
  def GetOutDirForTask(cls, task):
    """Returns the out dir for the task.

    Args:
      task: string: The task for which the outdir should be prepared.

    Returns:
      string: the out dir for the task. '' if there is no out dir.
    """
    rel_path = cls.GetTaskOutputRelativeDir(task)
    subdirs = PipelineConfig.Instance().GetAllSubDirsForPath(rel_path)
    return subdirs.get('PIPELINE_OUT_DIR', '')

  @classmethod
  def GetPublishDirForTask(cls, task):
    """Returns the publish dated dir for the task.

    Args:
      task: string: The task for which the publish dir should be prepared.

    Returns:
      string: the publish dated dir for the task. '' if there is no publish dir.
    """
    if not PipelineConfig.Instance().pipeline_publish_dir(): return ''

    out_dir = cls.GetOutDirForTask(task)
    if not out_dir: return ''
    return out_dir.replace(cls.GetOutSubDir(), PipelineConfig.Instance().pipeline_publish_dir())

  @classmethod
  def GetPublishCurrentDirForTask(cls, task):
    """Returns the current publish dir for the task.

    Args:
      task: string: The task for which the publish current dir should be prepared.

    Returns:
      string: The current publish dir for the task. '' if there is no publish dir.
    """
    if not PipelineConfig.Instance().pipeline_publish_dir(): return ''

    out_dir = cls.GetOutDirForTask(task)
    if not out_dir: return ''
    out_dir = out_dir.replace(cls.GetOutSubDir(), PipelineConfig.Instance().pipeline_publish_dir())
    return os.path.join(os.path.dirname(out_dir), 'current')

  @classmethod
  def GetLogFileForTask(cls, task):
    """Returns the log file for the task.

    Args:
      task: string: The task to run.

    Returns:
      dict {string, string}: The dictionary of IDS to values.
    """
    rel_path = cls.TaskRelativeName(task)
    if not rel_path or not PipelineConfig.Instance().pipeline_log_dir(): return None
    # Flatten the path.
    rel_path = rel_path.replace(os.sep, '.')
    return os.path.join(PipelineConfig.Instance().pipeline_log_dir(), rel_path + '.log')

  @classmethod
  def GetPrevDatedDirCotainingPattern(cls, path, pattern):
    """Returns the previous dated sibling directory containing the request file.

    Args:
      path: string: The dir whose sibling is to be returned.
      pattern: string: The pattern (glob.glob) that is expected to be present in the sibling
          directory.

    Returns:
      string: the out dir base for the pipeline. None if there is no out dir.
    """
    while path:
      prev_dir = FileUtils.GetPreviousDatedDir(path)
      if prev_dir and glob.glob(os.path.join(prev_dir, pattern)):
        return prev_dir
      path = prev_dir
    return None

  @classmethod
  def ZeusEmailId(cls, mail_domain):
    """Returns the email id for zeus."""
    return ('zeus+%s+noreply@%s.%s' %
            (PipelineConfig.Instance().pipeline_id(), socket.gethostname(),
             mail_domain))
