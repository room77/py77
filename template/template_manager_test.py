"""
test for template manager
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrad'

import r77_init  # pylint: disable=W0611
from pylib.template.template_manager import TemplateManager, DictTemplateManager

import os
import unittest

class TemplateManagerTest(unittest.TestCase):
  _TEMPLATE_FILE = 'test.jinja.html'
  def setUp(self):
    my_dir = os.path.dirname(__file__)
    self._template_file = os.path.join(my_dir, self._TEMPLATE_FILE)
    with open(self._template_file, 'w') as f:
      print >>f, '''
      <html><body><p>
          My variable is {{ var }}
      </html></body></p>
      '''
    self._tm = TemplateManager(my_dir)

  def tearDown(self):
    os.remove(self._template_file)

  def test_render(self):
    var = 'grooveboots'
    rendered = self._tm.render(self._TEMPLATE_FILE, {'var': var})
    self.assertIn(var, rendered)

  def test_params(self):
    params = self._tm.params(self._TEMPLATE_FILE)
    self.assertIn('var', params)

class DictTemplateManagerTest(unittest.TestCase):
  _TEMPLATES = {'foo': 'foo this {{ arg }}.',
                'bar': "it's a {{ is }}, not a {{ is_not }}!"}
  def setUp(self):
    self._tm = DictTemplateManager(self._TEMPLATES)

  def test_render(self):
    self.assertEqual(self._tm.render('foo', {'arg': 'test'}), 'foo this test.')
    self.assertEqual(self._tm.render('bar', {'is': 'bar', 'is_not': 'baz'}),
                     "it's a bar, not a baz!")
