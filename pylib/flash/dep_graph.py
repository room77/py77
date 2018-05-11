#!/usr/bin/env python

"""Handles depgraph. Generates the dependency graph for the given rules."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'


import itertools
import os
import subprocess
import sys
import time

from pygraph.classes import digraph  # $ sudo easy_install python-graph-core
import pygraph.readwrite.dot as dot  # $ sudo easy_install python-graph-dot

from pylib.base.flags import Flags
from pylib.base.term_color import TermColor
from pylib.base.exec_utils import ExecUtils
from pylib.file.file_utils import FileUtils

from pylib.flash.cmd_handler import CmdHandler
from pylib.flash.rules import Rules
from pylib.flash.utils import Utils

# gv is not necessary for the basic operation of DepGraph, so do not force it
# to be included.
try:
  import gv  # $ sudo aptitude install libgv-python
except:
  pass

class DepGraph(CmdHandler):
  """Class to handle depgraph."""

  @classmethod
  def Init(cls, parser):
    super(DepGraph, cls).Init(parser)
    parser.add_argument('-m', '--mode', type=str,
                        default='gv' if 'gv' in sys.modules else 'text',
                        choices=['gv', 'text'],
                        help='The mode in which the output file is generated.')
    parser.add_argument('-q', '--quiet', action="store_true", default=False,
                        help='If true, do not show the output in "gv" mode.')

  @classmethod
  def WorkHorse(cls, rules):
    """Runs the workhorse for the command.

    Args:
      rules: list: List of rules to be handled.

    Return:
      (list, list): Returns a tuple of list in the form
          (successful_rules, failed_rules) specifying rules that succeeded and
          ones that failed.
    """
    (successful_expand, failed_expand) = Rules.GetExpandedRules(
        rules, Flags.ARGS.allowed_rule_types)

    args = zip(itertools.repeat(cls), itertools.repeat('_RunSingeRule'),
                          successful_expand)
    rule_res = ExecUtils.ExecuteParallel(args, Flags.ARGS.pool_size)
    successful_deps = []; failed_deps = []
    for (res, rule) in rule_res:
      if res == 1:
        successful_deps += [rule]
      elif res == -1:
        failed_deps += [rule]

    return (successful_deps, failed_expand + failed_deps)

  @classmethod
  def _RunSingeRule(cls, rule):
    """Runs a Single Rule.

    Args:
      rule: string: The rule to run.

    Return:
      (int, string): Returns a tuple of the result status and the rule.
          The status is '1' for success, '0' for 'ignore', '-1' for fail.
    """
    TermColor.Info('Generating dependencies for %s' % Utils.RuleDisplayName(rule))
    start = time.time()

    gr = digraph.digraph()
    gr.add_node(rule)

    nodes = [rule]
    while len(nodes):
      node = nodes.pop(0)
      # The rule has already been processed. We assume if the node has outgoing
      # edges, the we already processed it.
      if gr.node_order(node) > 0: continue

      # Add the dependencies of the rule to the graph.
      if not Rules.LoadRule(node) or not Rules.GetRule(node):
        TermColor.Warning('Could not load dependency %s for target %s ' %
                          (Utils.RuleDisplayName(node),
                           Utils.RuleDisplayName(rule)))
        return (-1, rule)

      node_data = Rules.GetRule(node)
      for dep in node_data.get('dep', set()):
        nodes += [dep]
        # Add the dep to the graph.
        if not gr.has_node(dep): gr.add_node(dep)
        if not gr.has_edge([node, dep]): gr.add_edge([node, dep])

    # Now we have the graph, lets render it.
    try:
      dt = dot.write(gr)
      dt = dt.replace('"%s";' % rule, ('"%s" [style=filled];' % rule), 1)
      dt = dt.replace(FileUtils.GetSrcRoot(), '')
      depgrah_file_name = cls.__GetDepGraphFileNameForRule(rule)
      if Flags.ARGS.mode == 'gv':
        gvv = gv.readstring(dt)
        gv.layout(gvv, 'dot')
        gv.render(gvv, 'pdf', depgrah_file_name)
        if not Flags.ARGS.quiet:
          subprocess.call('gv %s &' % depgrah_file_name, shell=True)
      elif Flags.ARGS.mode == 'text':
        FileUtils.CreateFileWithData(depgrah_file_name, dt)

      TermColor.Info('Generated dependency graph (%d nodes) for %s at %s \tTook %.2fs' %
                     (len(gr.nodes()), Utils.RuleDisplayName(rule),
                      depgrah_file_name, (time.time() - start)))
      return (1, rule)
    except Exception as e:
      TermColor.Error('Failed to render %s. Error: %s' %
                      (Utils.RuleDisplayName(rule), e))
      if type(e) == KeyboardInterrupt: raise e

    return (-1, rule)

  @classmethod
  def __GetDepGraphFileNameForRule(cls, rule):
    """Returns the file name for the dep graph of a given rule."""
    display_rule = Utils.RuleDisplayName(rule)
    return os.path.join('/tmp' ,
                        Utils.RuleDisplayName(rule).replace(os.sep, '_') + '.depgraph')


def main():
  try:
    DepGraph.Init(Flags.PARSER)
    Flags.InitArgs()
    return DepGraph.Run()
  except KeyboardInterrupt as e:
    TermColor.Warning('KeyboardInterrupt')
    return 1


if __name__ == '__main__':
  sys.exit(main())
