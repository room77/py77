
"""Manages different functions related to proto rules parsing."""

__author__ = 'pramodg@room77.com (Pramod Gupta)'
__copyright__ = 'Copyright 2012 Room77, Inc.'

import subprocess
import os

from pylib.file.file_utils import FileUtils
from pylib.base.term_color import TermColor


class ProtoRules:
  """Class to manage different functions related to parsing of proto rules."""

  @classmethod
  def GetProtoBufOutDir(cls):
    """Returns the protobuf output dir."""
    return FileUtils.GetGenDir()

  @classmethod
  def GetProtoBufBaseDir(cls):
    """Returns the protobuf base dir."""
    return os.path.join(FileUtils.GetSrcRoot(),
                         'third_party/protocol_buffer/latest')

  @classmethod
  def __GetOutFileName(cls, src, out_suffix):
    """Returns the output file name for the src.

    Args:
      src: string: The src file for which the output is generated.
      out_suffix: string: The suffix used to replace .proto in the src.

    Return:
      string: The output file name.
    """
    return (src.replace(FileUtils.GetSrcRoot(), cls.GetProtoBufOutDir())
            .replace('.proto', out_suffix))

  @classmethod
  def GetProtoRuleFormattedData(cls, rule_data, out_type):
    """Get the formatted proto dependency info for the output type.

    Args:
      rule_data: dict: The rule data for the proto rule.
      out_type: string: The type for which the proto data is to be generated.

    Return:
      dict: Corresponding rules generated for the out_type.
    """
    srcs = rule_data.get('src', set())

    protobuf_base_dir = cls.GetProtoBufBaseDir();
    out = {}
    if out_type.find('cc_') == 0 :  # Generated cc rule.
      pkg_config_cmd = ('export PKG_CONFIG_PATH=%s; '
          'pkg-config --define-variable=prefix=%s protobuf' %
          (os.path.join(protobuf_base_dir, 'lib/pkgconfig'), protobuf_base_dir))

      out['src'] = set([ cls.__GetOutFileName(x, '.pb.cc') for x in srcs ])
      out['hdr'] = set([ cls.__GetOutFileName(x, '.pb.h') for x in srcs ])
      out['flag'] = set(subprocess.getoutput(pkg_config_cmd + ' --cflags').split())
      out['link'] = set(subprocess.getoutput(pkg_config_cmd + ' --libs').split())
    else:
      TermColor.Error('Unsupported referrer type %s' % out_type)

    return out

  @classmethod
  def UpdateProtoRuleWithFormattedData(cls, rule_data, out_type):
    """Update the proto rule with formatted dependency info for the output type.

    Args:
      rule_data: dict: The rule data for the proto rule.
      out_type: string: The type for which the proto data is to be generated.
    """
    proto_data = cls.GetProtoRuleFormattedData(rule_data, out_type)

    # Remove the src.
    rule_data.pop('src', set())
    for key in list(proto_data):
      if key in rule_data:
        rule_data[key] |= proto_data[key]
      else:
        rule_data[key] = proto_data[key]

    # Update the type to signify that we do not need to format it any more.
    rule_data['_type'] = out_type

