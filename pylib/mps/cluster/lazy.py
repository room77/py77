#!/usr/bin/python

"""
Examples for how to use cluster.py
"""

import argparse
import os.path
import time
import yaml

import pylib.mps.cluster.packages as packages

def push(p, packages, args):
  p.push(args.local_root, args.package, args.version)

def f_import(p, packages, args):
  if '' != args.location:
    src = args.location
  else:
    src = packages[args.package]['src']
  version = p.f_import(src, args.package, args.version)
  print(version)

def list(p, packages, args):
  versions = p.get_versions(args.package)
  current = p.get_current(args.package)
  maxlen = 0
  for v in versions:
    if maxlen < len(v):
      maxlen = len(v)
  for v in versions:
    if args.pretty:
      t, Null, ver = v.partition('_')
      print("%s %s  %s  %s" %  ('*' if current == v else ' ',
        v + (maxlen-len(v)) * ' ', time.asctime(time.localtime(int(t))), ver))
    else:
      print(v)

def remove(p, packages, args):
  p.remove(args.package, args.version)

def stop(p, packages, args):
  p.stop(args.package)

def start(p, packages, args):
  p.start(args.package)

def activate(p, packages, args):
  p.activate(args.package, args.version)

def get_current(p, packages, args):
  current = p.get_current(args.package)
  if current:
    print(current)

def set_current(p, packages, args):
  p.set_current(args.package, args.version)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description = 'Cluster Library')
  parser.add_argument('--dry-run', action = 'store_true')
  parser.add_argument('--host', required = True)
  parser.add_argument('--package_def',
    default = os.path.join(os.path.dirname(__file__), 'packages.yaml'))
  parser.add_argument('-u', '--user', default = 'walle')
  parser.add_argument('-i', '--key',
    default = '/home/share/aws/r77_aws_keypair')
  parser.add_argument('-r', '--root', default = '/home/share/repo')
  subparsers = parser.add_subparsers(help = "Sub Commands:")

  p = subparsers.add_parser('import', help = 'import package to repository')
  p.add_argument('-p', '--package', required = True)
  p.add_argument('-v', '--version', default = '')
  p.add_argument('--location', default = '')
  p.set_defaults(func = f_import)

  p = subparsers.add_parser('push', help = 'copy package to the remote node')
  p.add_argument('-p', '--package', required = True)
  p.add_argument('-v', '--version', default = '')
  p.add_argument('--local-root', default = '/home/share/repo')
  p.set_defaults(func = push)

  p = subparsers.add_parser('list', help = 'list all versions for a given package')
  p.add_argument('-p', '--package', required = True)
  p.add_argument('--pretty', dest = 'pretty', action = 'store_true',
    default = False)
  p.set_defaults(func = list)

  p = subparsers.add_parser('remove', help = 'delete version of the package')
  p.add_argument('-p', '--package', required = True)
  p.add_argument('-v', '--version', required = True)
  p.set_defaults(func = remove)

  p = subparsers.add_parser('stop',  help = 'stop running package')
  p.add_argument('-p', '--package', required = True)
  p.set_defaults(func = stop)

  p = subparsers.add_parser('start', help = 'start running package')
  p.add_argument('-p', '--package', required = True)
  p.set_defaults(func = start)

  p = subparsers.add_parser('activate', help = 'stop, set_current, start in one command')
  p.add_argument('-p', '--package', required = True)
  p.add_argument('-v', '--version', required = True)
  p.set_defaults(func = activate)


  p = subparsers.add_parser('get_current', help = 'get current version of the package')
  p.add_argument('-p', '--package', required = True)
  p.set_defaults(func = get_current)

  p = subparsers.add_parser('set_current', help = "change 'current' symlink")
  p.add_argument('-p', '--package', required = True)
  p.add_argument('-v', '--version', required = True)
  p.set_defaults(func = set_current)

  args = parser.parse_args()

  pkg = packages.Packages(args.host, user = args.user,
    root = args.root, key = args.key, dry_run = args.dry_run)

  packages = {}
  if os.path.isfile(args.package_def):
    packages = yaml.safe_load(file(args.package_def, 'r'))

  args.func(pkg, packages, args)
