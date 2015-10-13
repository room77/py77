#!/usr/bin/env python

"""Interface for packaging"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

from exceptions import NotImplementedError

class PkgRulesInterface(object):
  """Base class for making packages"""
  @classmethod
  def make_package(cls, rule):
    """Generates a package
    Args:
      rule: rule to generate the package
    Returns:
      tuple(string, string) the package name followed by the package
      version name (e.g. $pkgname_$timestamp)
    """
    raise NotImplementedError
