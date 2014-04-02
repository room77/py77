"""
module for managing machine environments
"""

__copyright__ = '2013, Room 77, Inc.'
__author__ = 'Kyle Konrad'

import os
import subprocess

__PRODUCTION_FILE = '/home/config/prod_machine'
__STAGING_FILE = '/home/config/staging_machine'
__TEST_FILE = '/localdisk/home/is_r77_test'

IN_PRODUCTION = os.path.exists(__PRODUCTION_FILE)
IN_STAGING = os.path.exists(__STAGING_FILE)
IN_TEST = os.path.exists(__TEST_FILE)
