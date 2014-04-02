# Room 77 Python Libraries
This is a collection of Python libraries used at Room 77, Inc.

## Installation
To run code contained in this directory, install dependencies with

    pip install -r stable-requirements.txt

There is one additional dependency not in PyPi, GraphViz. To install the necessary Python bindings run

    sudo apt-get install libgv-python

Or the equivalent command for your operating system. Depending on your environment, it may be necessary to add the installed module to your Python path either by setting the PYTHONPATH environment variable or by creating symlinks to the installed module and shared library. On Debian, by default, `gv.py` and `_gv.so` are installed to `/usr/share/pyshared`.

## Components

### Flash
A declarative build system.

### Zeus
A task runner.

### Master Packaging System
A production deployment system.

## License
All code is distributed under the MIT license, unless otherwise noted. See LICENSE for details.