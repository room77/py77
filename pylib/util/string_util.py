"""
string utils
"""

__author__ = 'Kyle Konrad <kyle@room77.com>'
__copyright__ = '2013, Room 77, Inc.'

import re

from pylib.util.iter_util import chunk

def to_unicode(s, encoding='utf-8'):
  """
  convert a string or unicode to unicode
  """
  if isinstance(s, str):
    return s
  else:
    return str(s, encoding=encoding)

def camelize(strings):
  """
  Make a camelcase string
  Args:
    strings (list[string]): list of strings

  DocTests:
    >>> camelize(['one', 'two', 'three'])
    'OneTwoThree'
  """
  return ''.join((s[0].upper() +
                  ''.join([c.lower() for c in s[1:]])
                  for s in strings))

def break_and_indent(string, max_line_length=80, indent='',
                     break_at=' ', indent_first=False):
  r"""
  break a string into multiple lines and indent the lines

  Args:
    string (str): the string to break
    max_line_length (int): maximum line length
    indent (str): string to indent lines with
    break_at (str or regular expression): string or
      regular expression to break lines at

  Returns:
    broken: string broken across multiple lines

  DocTests:
    >>> break_and_indent('11 22 3334444 55 66', 5, '  ')
    '11 22\n  3334444\n  55\n  66'
    >>> break_and_indent('111111 22 3334444 55 66', 5, '  ')
    '111111\n  22\n  3334444\n  55\n  66'
    >>> break_and_indent('1111 2 3 55 66', 5, '  ')
    '1111\n  2 3\n  55\n  66'
  """
  if isinstance(break_at, str):
    break_at=re.compile('(%s)' % break_at)
  tokens = [token + separator for token, separator in
            chunk(break_at.split(string), 2, '')]
  lines = []
  current_line = indent if indent_first else ''
  current_line_is_empty = True
  for token in tokens:
    if len(current_line) + len(token.rstrip()) > max_line_length:
      # put at least one token per line, even it goes over
      if current_line_is_empty:
        current_line += token
        lines.append(current_line.rstrip())
        current_line, current_line_is_empty = indent, True
      else: # reset current line
        lines.append(current_line.rstrip())
        current_line, current_line_is_empty = indent + token, False
    else:
      current_line += token
      current_line_is_empty = False
  if not current_line_is_empty:
    lines.append(current_line)
  return '\n'.join(lines)


if __name__ == '__main__':
  import doctest
  doctest.testmod()
