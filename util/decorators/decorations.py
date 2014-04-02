"""
Few util decorations.
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Pramod Gupta'

def static_var(varname, value):
    def decorate(func):
        setattr(func, varname, value)
        return func
    return decorate
