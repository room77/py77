#!/usr/bin/env python

"""
utility file for various git functions
"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import os
import subprocess

from pylib.base.exec_utils import ExecUtils
from pylib.base.term_color import TermColor

class Error(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return "'%s'" % self.value

class EmptyHotfixError(Exception):
  """this exception is raised when a hotfix is applied twice"""
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return "'%s'" % self.value

class GitUtil(object):

  @classmethod
  def apply_hotfix(cls, branch, commit_hash=""):
    """applies a hotfix to a specific branch
    Args:
      branch (string) - the branch to apply the hotfix
      hash (string) - the commit hash to use
    Raises:
      EmptyHotfixError - raised when the hotfix is empty
      Error - critical error such as conflict stopped with
        hotfix from being applied
    """
    print("moving to branch %s" % TermColor.ColorStr(branch, 'GREEN'))
    # get onto the appropriate branch
    cls.checkout_branch(branch)
    # try to cherry-pick
    print(TermColor.ColorStr("Applying hotfix to branch: %s" % branch,
                             'GREEN'))
    ret = ExecUtils.RunCmd('git cherry-pick %s' % commit_hash)[0]
    if not ret == 0:
      r = ExecUtils.RunCmd('git diff --name-only')
      if r[0]:
        raise Error(TermColor.ColorStr('error doing a git diff', 'RED'))
      files = r[1]
      if not files:
        raise EmptyHotfixError('hotfix is empty. likely already applied')
      # not an error if empty
      raise Error(TermColor.ColorStr(
        ('Hotfix apply failed at step cherry pick on branch %s.\n'
         'You NEED to fix this NOW! Go to %s and fix the issue! '
         'Impacted files: %s') % (
        cls.get_current_branch(), os.getcwd(), files), 'RED'))
    # push cherry-pick to remote
    ret = ExecUtils.RunCmd('git push origin %s' % branch)[0]
    if not ret == 0:
      raise Error(TermColor.ColorStr(
        'Please manually resolve your merge conflicts,' + \
        'then commit, and finally run hotfix selecting the ' + \
        'branches that have not yet received the commit', 'RED'))
    print(TermColor.ColorStr('Applied hotfix to %s' % branch, 'GREEN'))
    print(TermColor.ColorStr('On branch %s' % branch, 'GREEN'))

  @classmethod
  def checkout_branch(cls, branch):
    """Checks out the specified branch with the latest code
    Args:
      branch (string) - the branch name
    """
    # fetches the latest code
    ret = ExecUtils.RunCmd('git fetch origin')[0]
    if not ret == 0:
      raise Error(TermColor.ColorStr('error during git fetch origin!', 'RED'))
    #subprocess.check_call(
    #  'git checkout -b %s --track origin/%s 2>/dev/null' % \
    #  (branch, branch),
    #  shell=True)
    ret = ExecUtils.RunCmd('git checkout -B %s --track origin/%s' % (
      branch, branch))[0]
    if not ret == 0:
      raise Error(TermColor.ColorStr(
        'error checking out branch %s' % branch, 'RED'))

  @classmethod
  def commit_push_hotfix(cls, files, msg, branch=''):
    """Commits/pushes the set of files to the CURRENT branch
    AND if a branch param is specified, hotfixes to the specified branch
    with this same commit
    Args:
      files (list) - the files to commit
      msg (string) - the commit message
      branch (string) - the name of the additional branch to hotfix if desired
    """
    # commit/push the specified files
    cls.commit_push(files, msg)
    # find the SHA1 of the latest commit
    commit_hash = cls.get_latest_commit()
    # save the current branch
    current_branch = cls.get_current_branch()
    # hotfix to branch if not already on the branch
    if branch and not current_branch == branch:
      cls.apply_hotfix(branch, commit_hash)
    # get back on current branch
    cls.checkout_branch(current_branch)

  @classmethod
  def commit_push(cls, files, msg):
    """Commits to the current branch AND pushes to remote
    Args:
      files (list) - list of files to commit
      msg (string) - the commit message
    """
    ret = ExecUtils.RunCmd('git commit %s -m "%s"' % (' '.join(files), msg))[0]
    if not ret == 0:
      raise Error(TermColor.ColorStr(
        'error committing these files: %s' % ' '.join(files), 'RED'))
    ret = ExecUtils.RunCmd('git pull && git push')[0]
    if not ret == 0:
      raise Error(TermColor.ColorStr(
        'Please manually resolve any conflicts preventing git push of ' + \
        'the commit to remote', 'RED'))

  @classmethod
  def create_branch(cls, name):
    """Create and checkout branch and push to origin for tracking. Simply
    checks out if the branch already exists
    Args:
      name (string) - the name of the branch to create
    """
    # only create a new branch if did not exist before
    params = ''
    # check if the branch already exists
    ret = subprocess.call(
      'git show-ref --verify refs/heads/%s' % name, shell=True)
    if ret:
      params = '-b'
    # checkout and/or create the branch
    subprocess.check_call('git checkout %s %s' % (params, name), shell=True)
    # push to remote for tracking
    subprocess.check_call('git push -u origin %s' % name, shell=True)

  @classmethod
  def get_current_branch(cls):
    """Returns the name of the current branch"""
    cmd = 'git rev-parse --abbrev-ref HEAD'
    r = ExecUtils.RunCmd(cmd)
    if r[0]:
      raise Error(TermColor.ColorStr('error executing cmd %s' % cmd, 'RED'))
    return r[1].strip()

  @classmethod
  def get_latest_commit(cls):
    """Returns the latest commit hash"""
    commit_hash = subprocess.check_output('git log -1 --pretty=format:%H',
                                          shell=True)
    if not commit_hash:
      raise Error(TermColor.ColorStr(
        'unable to find the latest commit hash', 'RED'))
    return commit_hash

  @classmethod
  def get_latest_release_branch(cls):
    """Returns the name of the latest release branch"""
    return subprocess.check_output("git branch -r | grep release- | sed -e 's/^[ \t]*//' | sed 's/\* //' | sed 's/origin\///' | sort -r | head -n1", shell=True).strip()

  @classmethod
  def repo_root(cls):
    """Returns the root of the repository"""
    return subprocess.check_output('git rev-parse --show-toplevel',
                                   shell=True).strip()

  @classmethod
  def update_submodules(cls):
    """Does a git pull and then update the submodules to the latest version
    AND finally ensure the submodule is on master
    @warning if you run this from a module run that does a os.chdir, this
       os.chdir will NOT persist here
    """
    if ExecUtils.RunCmd('git pull')[0]:
      raise Error(TermColor.ColorStr(
        'unable to git pull as part of submodule update', 'RED'))

    if ExecUtils.RunCmd('git submodule init && git submodule update')[0]:
      raise Error(TermColor.ColorStr(
        'git submodule update failed!', 'RED'))
