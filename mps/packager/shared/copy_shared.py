"""
Copies the shared utilities to the appropriate package destination.
@WARNING keep this list small, because nearly every package will
include these files
"""

import os.path
import shutil

class CopyShared(object):
  # the set of utility files are copied
  SHARED_FILES = ['control_base.py']

  @classmethod
  def copy(cls, dest_dir):
    """copies all the SHARED_FILES for packaging to the given directory
    Args:
      dest_dir - the directory to copy these files
    """
    shared_dir = os.path.dirname(__file__)
    for f in cls.SHARED_FILES:
      shutil.copy2(os.path.join(shared_dir, f),
                   os.path.join(dest_dir, f))
