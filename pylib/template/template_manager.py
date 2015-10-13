"""
manager for Jinja2 templates
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrad'

from jinja2 import (Environment, FileSystemLoader, DictLoader,
                    meta, StrictUndefined)
from jinja2.exceptions import UndefinedError, TemplateNotFound
import re

class TemplateManager(object):
  """
  template manager for all files in a path
  """
  def __init__(self, template_path):
    """
    Args:
      template_path: string or list of strings of directory containing templates
    """
    self._environment = Environment(loader=FileSystemLoader(template_path), undefined=StrictUndefined)


  def render(self, template_name, params=None):
    """
    render a template
    """
    template = self._environment.get_template(template_name)
    try:
      return template.render(**(params or {}))
    except UndefinedError as e:
      if e.message.endswith('is undefined'):
        raise ValueError('missing "%s" param' % e.message.split("'")[1])
      raise ValueError('template param error: ' + e.message)

  def params(self, template_name):
    """
    This requires parsing the template so it should only be used in exceptional cases

    Returns:
      set of params used by this template
    """
    source = self._environment.loader.get_source(self._environment, template_name)
    parsed = self._environment.parse(source)
    return meta.find_undeclared_variables(parsed)


class DictTemplateManager(TemplateManager):
  """
  template manager for templates in a dict
  """
  def __init__(self, templates):
    """
    Args:
      templates (dict): {template_name: template_string}
    """
    self._environment = Environment(loader=DictLoader(templates), undefined=StrictUndefined)
