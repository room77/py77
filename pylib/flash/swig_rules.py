"""Manages different functions related to swig rules parsing."""
from __future__ import print_function

__copyright__ = '2013 Room 77, Inc.'
__author__ = 'Kyle Konrad <kyle@room77.com>'

import os

from pylib.base.term_color import TermColor
from pylib.file.file_utils import FileUtils

from pylib.flash.make_rules import MakeRules


class SwigRules(MakeRules):
  """Class to manage different functions related to parsing of swig rules."""

  @classmethod
  def GetSwigOutDir(cls):
    """Returns the swig output dir."""
    return os.path.join(FileUtils.GetEDir(), 'swig')

  @classmethod
  def __GetWrapperFileName(cls, src):
    """Returns the C++ wrapper file name for the src.

    Args:
      src: string: The interface file for which the output is generated.

    Return:
      string: The output file name.
    """
    return FileUtils.GetBinPathForFile(src).replace('.i', '.swig.cc')

  @classmethod
  def __GetLibFileName(cls, src, name):
    """Returns the .so file name for the shared lib
    the .so file name is determined by the swig module name
    if the swig file starts with %module my_module, the lib file name
    will be _my_module.so

    Args:
      src: string: The interface file for which the output is generated.

    Return:
      string: The output file name.
    """
    bin_path = FileUtils.GetBinPathForFile(src)
    return os.path.join(os.path.dirname(bin_path), '_%s.so' % name)

  @classmethod
  def __GetGenModuleName(cls, src):
    with open(src) as f:
      first_line = f.readline()
    module = first_line.lstrip('%module').strip()
    return module

  @classmethod
  def __GetGenModuleDir(cls, src):
    """Returns the python module name for the src.

    Args:
      src: string: The interface file for which the output is generated.

    Return:
      string: The directory name where the generated module will be outputted.
    """
    return os.path.dirname(src.replace(FileUtils.GetSrcRoot(), cls.GetSwigOutDir()))

  @classmethod
  def GetSwigRuleFormattedData(cls, rule_data):
    """Get the formatted swig dependency info for the output type.

    Args:
      rule_data: dict: The rule data for the swig rule.

    Return:
      dict: Corresponding rules generated for the out_type.
    """
    srcs = rule_data.get('src', set())

    out = {}
    out['src'] = {cls.__GetWrapperFileName(x) if x.endswith('.i') else x for x in srcs}
#    out['link'] = {'/usr/include/python2.7'}
    out['flag'] = {'-fPIC', '-Wno-unused-but-set-variable', '-I/usr/include/python2.7'}

    return out

  @classmethod
  def UpdateSwigRuleWithFormattedData(cls, rule_data):
    """Update the swig rule with formatted dependency info.

    Args:
      rule_data: dict: The rule data for the swig rule.
    """
    swig_data = cls.GetSwigRuleFormattedData(rule_data)

    # Remove the src.
    rule_data.pop('src', set())
    for key in list(swig_data):
      if key in rule_data:
        rule_data[key] |= swig_data[key]
      else:
        rule_data[key] = swig_data[key]

    # Update the type to signify that we do not need to format it any more.
    rule_data['_type'] = 'cc_shared'

  @classmethod
  def WriteMakefile(cls, spec, makefile):
    src_root = FileUtils.GetSrcRoot()
    name = spec['name']
    with open(makefile, 'w') as f:
      interface_files = {x for x in spec.get('src', set()) if x.endswith('.i')}
      for interface_file in interface_files:
        wrapper_file = cls.__GetWrapperFileName(interface_file)
        gen_out_dir = cls.__GetGenModuleDir(interface_file)
        target_lib = cls.__GetLibFileName(interface_file, name)
        target_lib_link = os.path.join(gen_out_dir,
                                       '_%s.so' % cls.__GetGenModuleName(interface_file))
        #target_lib = target_lib.replace('.so', '_swig.so') # TODO(KK) fix this hack
        assert gen_out_dir.startswith(src_root) # otherwise we will loop forever
        print("""
%(wrapper_file)s: %(interface_file)s
\t@mkdir -p %(gen_out_dir)s
\t@ln -s -f %(target_lib)s %(target_lib_link)s
\t@swig -c++ -python -o $@ -outdir %(gen_out_dir)s $<
\t@p=%(gen_out_dir)s; while [[ $$p != $(SRCROOT) ]]; do\
  touch $$p/__init__.py; \
  p=`dirname $$p`; \
done
""" % locals(), file=f)
