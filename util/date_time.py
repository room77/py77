"""
Util functions for datetime classes
"""

__author__ = "Kyle Konrad kyle@room77.com"
__copyright__ = "Room 77, Inc. 2013"

from datetime import timedelta, datetime, date

EPOCH = datetime(1970,1,1)
MDY_FORMAT = '%m.%d.%Y'

EPOCH = datetime(1970,1,1)
MDY_FORMAT = '%m.%d.%Y'

def date_range(start, end, interval=timedelta(days=1)):
  """
  A more general version of Python's range() function for date[time]s

  Note: Theoretically, this function may be used with any non integer type as it
    is not implemented with any specific calls to datetime specific methods. It
    has only been tested for date[time]s, though.

  Note: While this function is equivalent to (x)range() when called with ints, it
    is about an order of magnitude slower (varies by range size).

  Args:
    start (date or datetime): starting date[time]
    end (date or datetime): ending date[time]
    interval (timedelta): interval between date[time]s

  Yields:
    day: date[time] in [start, end)

  Raises:
    ValueError if interval is equivalent to 0
  """
  # raise ValueError when 0 interval (equivalent to range)
  if not interval:
    raise ValueError("date_range() interval argument must not be 0")
  # check for interval in "wrong" direction
  elif end > start and start + interval <= start:
    return
  elif start > end and start + interval >= start:
    return

  # iterate through the interval
  current = start
  in_interval = (lambda x : x < end) if current < end else (
    lambda x: x > end)
  while in_interval(current):
    yield current
    current += interval

def str_to_date(date_string, spec="%Y%m%d"):
  """
  Constructs a datetime.date object from string

  Args:
    date_string(str): Date in string (ex: 20130718)
    spec(str): a datetime spec

  Returns:
    date(date)

  Raises:
    TypeError: date_string or spec is not a str
    ValueError: date_string is not a valid date
  """
  return datetime.strptime(date_string, spec).date()

def microsecond_timestamp_to_datetime(timestamp):
  """
  Constructs a datetime object from microsecond timestamp

  Args:
    timestamp(str or int): microsecond timestamp

  Returns:
    a datetime object corresponding to timestamp

  Raises:
    TypeError: input string is not valid
    ValueError: timestamp is not valid
  """
  return datetime.fromtimestamp(float(timestamp) / 1000000)

def datetime_to_microsecond_timestamp(dt):
  """
  Convert a datetime object to a microsecond timestamp

  Args:
    a datetime object corresponding to timestamp

  Returns:
    timestamp(str or int): microsecond timestamp
  """
  return int(round((dt - EPOCH).total_seconds()*1000000))


def str_to_datetime(datetime_string, spec="%Y%m%d %H:%M:%S"):
  """
  Constructs a datetime.datetime object from string

  Args:
    datetime_string (string): Date in string (ex: 20130718)
    spec (string): a datetime spec

  Returns:
    The datetime.datetime parsed from the string

  Raises:
    TypeError: datetime_string or spec is not a str
    ValueError: datetime_string is not a valid date
  """
  return datetime.strptime(datetime_string, spec)

def date_to_struct(date_obj):
  """
  convert a date or datetime to a {y: 2013, m: 1, d: 1} struct
  """
  return {'y': date_obj.year,
          'm': date_obj.month,
          'd': date_obj.day}

def struct_to_date(date_struct):
  """
  convert a {y: 2013, m: 1, d: 1} struct to a date
  """
  return date(date_struct['y'], date_struct['m'], date_struct['d'])

