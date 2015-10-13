"""Common init to get the source root for files."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import inspect
import os
import sys
import traceback

# This is needed to build binaries due to a bug in pyinstaller.
# May be removed in future if the bug is fixed.
import encodings

# directory of the file this module is imported from
_dir = os.path.dirname(os.path.realpath(os.path.abspath(
      traceback.extract_stack()[-2][0])))

##
## NO NOT PRINT ANYTHING IN THIS FILE. Many files
## include this file, and printing may mess up
## file generation and other tasks that reply on output
##

def src_root():
  """Returns the repository root."""
  d = _dir
  while (d and d != '/' and os.path.isdir(d) and not
         os.path.exists(os.path.join(d, '.git'))):
    d = os.path.dirname(d)
  return d

def pylib_parent_dir():
  """Returns the directory containing pylib."""
  d = _dir
  while (d and d != '/' and os.path.isdir(d) and not
         os.path.exists(os.path.join(d, 'pylib'))):
    d = os.path.dirname(d)
  if d is None or d == '/':
    raise ValueError('r77_init must be imported from a file under pylib')
  return d

def e_dir():
  """Returns the dir with generated code corresponding to this dir"""
  return os.path.join(src_root(), 'e')

PY_SRC = pylib_parent_dir()
E = e_dir()
# print 'SRC: %s' % SRC
if PY_SRC not in sys.path:
  sys.path.append(PY_SRC)
if E not in sys.path:
  sys.path.append(E)

