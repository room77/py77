#!/usr/bin/env python

"""
A variety of push utility functions
"""

from pylib.util.git_util import GitUtil

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'


class PushUtil(object):
  @classmethod
  def get_deployspec_name(cls, cluster_name):
    """given a cluster returns the deployspec name
    convention of $cluster-$current_branchname.
    Args:
      cluster - the cluster name
    Returns:
      the deployspec name for the current branch and cluster
    """
    return '%s-%s' % (cluster_name, GitUtil.get_current_branch())
