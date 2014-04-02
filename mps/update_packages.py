#!/usr/bin/env python

"""
Builds the appropriate packages updates the releases file for a given cluster
"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import os
import yaml

import r77_init # pylint: disable=W0611
from pylib.prod.packager.packager_util import PackagerUtil, Error as PackagerUtilError
from pylib.prod.util.queue_cluster_config_updates import QueueClusterConfigUpdates
from pylib.prod.util.push_util import PushUtil
from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.util.git_util import GitUtil

class Error(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return "'%s'" % self.value

class UpdatePackages(object):
  RULES_DIR = 'prod/config'

  def __init__(self, release_name, rules):
    """
    Args:
      release_name (string) - string name of release in the releases.yaml
      rules (list) - the list of rules to build OR if the RULES_DIR directory
        is not specified as part of the path. prefix the path
        e.g. for client, the package becomes os.path.join(RULES_DIR, 'client')
    """
    self._release_name = release_name
    prefix_lambda = \
      lambda x: os.path.join(self.RULES_DIR, x) if not self.RULES_DIR in x else x
    self._rules = map(prefix_lambda, rules)

  def build_update_release(self):
    """builds the requested packages, updates the releases file including
    the cluster.yaml, commits/pushes the new releases file.
    """
    # build the packages
    try:
      packages = PackagerUtil.make_packages(self._rules)
    except PackagerUtilError:
      raise Error(
        'one or more of the packages could NOT be built. Once you fix '
        'the problem, please run update_packages again with the following '
        'rules : %s'  % ' '.join(self._rules))
    # update the releases file with the new packages and version names
    QueueClusterConfigUpdates.update_release(self._release_name, packages)
    # update the submodule to get the latest cluster info
    GitUtil.update_submodules()
    # success!
    print TermColor.ColorStr(
      'Updated releases.yaml for RULES: %s' % (' '.join(self._rules)),
      'GREEN')

if __name__ == '__main__':
  # setup the parser
  parser = Flags.PARSER
  parser.add_argument('--deployspec', default='',
                      help=('name of the deployspec to use. if not specified, '
                            'computes the deploysec from $cluster-$branch'))
  parser.add_argument('--deployspecs_path',
                      default='prod/cluster/conf/deployspecs.yaml',
                      help='the path to the deployspecs file')
  parser.add_argument('cluster',
                      help='the name of the cluster in the clusters.yaml ' + \
                        'deployed to. dummy value okay if deployspec specified')
  parser.add_argument('pkg_rules', nargs='*',
                      help=('the space separated list of package rules to '
                            'update. if you specify the RULE without a '
                            'directory, it will prefix the directory %s' % (
                            UpdatePackages.RULES_DIR)))
  Flags.InitArgs()
  args = Flags.ARGS
  if not args.pkg_rules:
    raise Error(TermColor.ColorStr(
      'You must specify a package rules or set of packages rules to build ' + \
      'for update packages.',
      'RED'))
  deployspec_name = args.deployspec
  # if no deployspec is specified, generate the name from the branch and cluster
  if not deployspec_name:
    deployspec_name = PushUtil.get_deployspec_name(args.cluster)
  # verify the expected deployspec exists in the deployspecs file
  with open(args.deployspecs_path, 'r') as f:
    deployspec = yaml.safe_load(f)
    if not deployspec_name in deployspec:
      raise Error(TermColor.ColorStr(
        'deployspec name %s not found in the deployspecs' % deployspec_name,
        'RED'))

  up = UpdatePackages(deployspec[deployspec_name]['release'], args.pkg_rules)
  up.build_update_release()
