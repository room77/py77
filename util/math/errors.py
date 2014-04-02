"""
Math function related errors
"""

__author__ = "Kar Epker, karepker@gmail.com"
__copyright__ = "Room 77, Inc. 2013"

class NotDefinedError(Exception):
  """Error to raise when the operation is not defined"""

  def __init__(self, operation, arg_dict):
    """Builds a not defined error

    Args:
      operation (string): The operation that was undefined (e.g. mean)
      arg_dict (dict): A dict of args given to the function that wants to raise
        this error
    """
    self.operation = operation
    self.arg_dict = arg_dict

  def __str__(self):
    return "operation %s is not defined with arguments %s!" % (
      self.operation, str(self.arg_dict))

