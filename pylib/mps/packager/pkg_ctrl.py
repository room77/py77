#!/usr/bin/env python

"""Control script for data packages"""

__author__ = 'edelman@room77.com (Nicholas Edelman)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import argparse
import os
import subprocess
import yaml

from control_base import ControlBase

class PkgController(ControlBase):
  """ control script for data packages"""

  def __init__(self):
    super(PkgController, self).__init__()

  def setlive(self):
    """@override
    sets the external symlinks AFTER make_current has already been called
    on the package
    """
    version_dir = self._get_setlive_dir(__file__)
    # create the symlinks
    for src, link in self._config['syms'].iteritems():
      self._create_link(os.path.join(version_dir, src), link)

if __name__ == '__main__':
  c = PkgController()
  c.run()
