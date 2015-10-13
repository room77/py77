#!/usr/bin/python

"""Packages and deploys"""

__author__ = 'chernyak@room77.com (Michael Chernyak)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import copy
import glob
import os
import re
import shutil
import subprocess
from string import Template
import sys
import time
import yaml

class Error(Exception):
  """The exception class for the packager"""
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return "'%s'" % self.value

class Packages(object):
  @classmethod
  def get_valid_package_prefix(cls, pkg_str=''):
    """ classmethod for creating the valid package version string
    Args:
      pkg_str - an optional package string to suffix to the package timestamp
    Returns:
      a valid package version prefix
      e.g. $ts_${pkg_str}_ or $ts_ => 123432432_aba_ or 1324342_
    """
    ts = int(time.time()) + 1
    ver_str = '%d_' % ts
    if pkg_str:
      ver_str = '%s%s_' % (ver_str, pkg_str)
    return ver_str

  @classmethod
  def generate_package_name(cls, prefix, name):
    """Given a package prefix and a package name, generates
    the package name for import
    Args:
      prefix - the package prefix (if not specified or invalid, generates for you)
      name - the package
    Returns:
      the package name to save to the repo
    """
    if not prefix:
      prefix = cls.get_valid_package_prefix()
    if not re.match('^\d+_', prefix):
      raise Error('the prefix name: %s is invalid!' % prefix)
    return '%s%s' % (prefix, name)

  def __init__(self, host, user='',
               root = '/home/share/repo', key='',
               dry_run=False, verbose=True, compress=False):
    self.packages_versions = {}
    self.host = host
    self.repo = root
    self.dry_run = dry_run
    self.verbose = verbose
    self.compress = compress
    if user != '':
      self.user = user
    if key != '':
      self.key = key

  def _call_ssh(self, command, need_result=False, dry_run=None):
    destination = self.host
    if hasattr(self, 'user'):
      destination =  self.user + '@' + destination
    cmd = ['/usr/bin/ssh', destination]
    # TODO(edelman) - "-t" has a terrible impact. you cannot ctrl-C
    #   when "-t" is set
    #   adding this option also messes with the printing, but I can't
    #   figure out a better alternative. there must be a proper way to do
    #   buffered line by line writing.
    #cmd.append('-t')  # tty - need this option set so can see the unbuffered
                      # output. unfortunately newlines are \r\n instead of \n
                      # in tty mode
    cmd.append('-q')
    cmd.extend(['-c', 'aes128-cbc'])
    cmd.extend(['-o', 'UserKnownHostsFile=/dev/null'])
    cmd.extend(['-o', 'StrictHostKeyChecking=no'])
    cmd.extend(['-o', 'ConnectTimeout=30'])
    if hasattr(self, 'key'):
      cmd.extend(['-i', self.key])
    cmd.append(command)
    # don't print this too spammy and uninformative. perhaps
    # add a super verbose option in the future
    #if dry_run or self.verbose:
    #  print_cmd = '%s: %s'  % (destination, command)
    #  print print_cmd.strip()
    if not dry_run:
      if need_result:
        return subprocess.check_output(cmd)
      else:
        subprocess.check_call(cmd)

  def get_packages(self):
    self._get_versions()
    return self.packages_versions.keys()

  def get_versions(self, pkg_name=''):
    if pkg_name == '':
      self._get_versions()
      return
    if not pkg_name in self.packages_versions:
      self._get_versions(pkg_name)
    # this is a new package so it has no versions
    if not pkg_name in self.packages_versions:
      return []
    else:
      return copy.copy(self.packages_versions[pkg_name]['versions'])

  def get_current(self, pkg_name):
    if not pkg_name in self.packages_versions:
      self._get_versions(pkg_name)
    return self.packages_versions[pkg_name].get('current', None)

  def _get_versions(self, pkg_name=''):
    code = Template('''
import os, yaml
repo = '$repo'
pkg_name = '$pkg_name'
pkgs = {}

def get_pkg_versions(pkg):
  pkg_path = os.path.join(repo, pkg)
  if os.path.isdir(pkg_path):
    pkgs[pkg] = {'versions': []}
    for ver in os.listdir(pkg_path):
      ver_path = os.path.join(repo, pkg, ver)
      if ver == 'current' and os.path.islink(ver_path):
        pkgs[pkg]['current'] = os.readlink(ver_path)
        continue
      pkgs[pkg]['versions'].append(ver)
    pkgs[pkg]['versions'].sort()

if pkg_name:
  get_pkg_versions(pkg_name)
else:
  for pkg in  os.listdir(repo):
    get_pkg_versions(pkg)
print yaml.dump(pkgs)
''').substitute({'repo': self.repo, 'pkg_name': pkg_name})
    old_verbose = self.verbose
    self.verbose = False
    data = yaml.safe_load(
      self._call_ssh('/bin/echo "%s" | /usr/bin/python' %code, need_result=True, dry_run=False))
    if old_verbose:
      pkg_name_str = pkg_name if pkg_name else 'ALL packages'
      # too verbose quiet down!
      # print '%s: list versions of %s' % (self.host, pkg_name)
    self.verbose = old_verbose
    for k, v in data.iteritems():
      self.packages_versions[k] = v

  def f_import(self, src_dir, pkg_name, version_prefix=None):
    """Imports the package to the repository
    Args:
      src_dir - the directory to import
      pkg_name - name of the package
      version_prefix - optionally the package version prefix
    """
    version = self.generate_package_name(version_prefix, pkg_name)
    self._push(src_dir, pkg_name, version)
    return version

  def push(self, local_root, pkg_name, version):
    self._push(os.path.join(local_root, pkg_name, version), pkg_name, version)

  def _push(self, srcDir, pkg_name, version):
    versions = self.get_versions(pkg_name)
    if version in versions:
      return
    # rsync to a temp place
    cmd = ['/usr/bin/nice', '-n', '19']
    cmd.extend(['/usr/bin/ionice', '-c3'])
    cmd.extend(['/usr/bin/rsync', '-aH', '--delete'])
    cmd.append('--rsync-path=/usr/bin/nice -n 19 /usr/bin/ionice -c 3 /usr/bin/rsync')
    if self.compress:
      cmd.append('-z')

    rsh = '--rsh=/usr/bin/ssh -q -c aes128-cbc'
    rsh += ' -o UserKnownHostsFile=/dev/null'
    rsh += ' -o StrictHostKeyChecking=no'
    rsh += ' -o ConnectTimeout=30'

    if hasattr(self, 'key'):
      rsh += " -i '%s'" % self.key
    cmd.append(rsh)
    for v in reversed(versions[-4:]):
      cmd.append("--link-dest='%s'" % os.path.join(self.repo, pkg_name, v))
    ## Do NOT do this. if packages are created frequently, this can cause issues.
    ## Should fix the core issue to ensure the timestamps are preserved during
    ## package creation
    ### cmd.extend(['--modify-window', '180']) # clock may be out of sync
    cmd.append(srcDir + '/')
    repoName = os.path.join(self.repo, pkg_name, version)
    tmpName = os.path.join(self.repo, 'tmp', pkg_name + '__' + version)
    destination = "%s:'%s'" % (self.host, tmpName)
    if hasattr(self, 'user'):
      destination =  self.user + '@' + destination
    cmd.append(destination)
    if self.dry_run or self.verbose:
      # print cmd
      print '%s: copying package %s => %s to host' % (
        self.host, pkg_name, version)
    if not self.dry_run:
      subprocess.check_call(cmd)

    # rename
    if pkg_name in self.packages_versions:
      del self.packages_versions[pkg_name]
    self._call_ssh(
      Template("mkdir -p '$pkgDir' && mv '$tmpName' '$repoName'").substitute({
       'pkgDir': os.path.join(self.repo, pkg_name),
       'tmpName': tmpName,
       'repoName': repoName}), dry_run=self.dry_run)

  def search_version(self, pkg_name, version):
    versions = self.get_versions(pkg_name)
    if version in versions:
      return version
    v = filter(lambda x: re.search('^\d+_' + version + '$', x), versions)
    if 0 == len(v):
     raise Exception("version %s doesn't exist" % version)
    elif len(v) > 1:
      raise Exception('version %s: multiple matches' % version)
    return v[0]

  def remove(self, pkg_name, version):
    version = self.search_version(pkg_name, version)
    if self.verbose:
      print "%s.%s(%s, %s, %s)" %(self.__class__.__name__, sys._getframe().f_code.co_name, self.host, pkg_name, version)
    if version == self.get_current(pkg_name):
      raise Exception("Can't remove current")
    saved = self.packages_versions[pkg_name]
    del self.packages_versions[pkg_name]
    self._call_ssh(Template("mv '$repoName' '$tmpName' && rm -rf '$tmpName'")
      .substitute({
      'repoName': os.path.join(self.repo, pkg_name, version),
      'tmpName': os.path.join(self.repo, 'tmp', pkg_name + '__' + version)}), dry_run=self.dry_run)
    saved['versions'].remove(version)
    self.packages_versions[pkg_name] =  saved

  def stop(self, pkg_name):
    current = self.get_current(pkg_name)
    if not current:
      return
    if self.verbose:
      print '%s: stopping %s' % (self.host, pkg_name)
    self._call_ssh(Template('''
if [ -x '$control' ]; then
  '$control' stop
fi
''').substitute({
      'control': os.path.join(self.repo, pkg_name, current, 'control')}), dry_run=self.dry_run)

  def start(self, pkg_name):
    current = self.get_current(pkg_name)
    if not current:
      raise Exception("current is not set for %s" % pkg_name)
    if self.verbose:
      print '%s: starting %s' % (self.host, pkg_name)
    self._call_ssh(Template('''
if [ -x '$control' ]; then
  '$control' start
fi
''').substitute({
      'control': os.path.join(self.repo, pkg_name, current, 'control')}), dry_run=self.dry_run)

  def set_current(self, pkg_name, version):
    version = self.search_version(pkg_name, version)
    old_current = self.get_current(pkg_name) or ''
    if version == old_current:
      return
    del self.packages_versions[pkg_name]
    if self.verbose:
      print '%s: %s => %s setting current and calling setlive' % (
        self.host, pkg_name, version)
    self._call_ssh(Template('''
if [ 'X' != 'X$currentVer' ]; then
  rm -f '$currentLink'
fi &&
ln -s '$version' '$currentLink'
if [ -x '$newCtl' ]; then
  # delete the current symlink if setlive failed
  # so the new round it will try again
  $newCtl setlive || (rm '$currentLink' && false)
fi''').substitute({
      'currentVer': old_current,
      'version': version,
      'currentLink': os.path.join(self.repo, pkg_name, 'current'),
      'newCtl': os.path.join(self.repo, pkg_name, version, 'control')}), dry_run=self.dry_run)

  def activate(self, pkg_name, version):
    version = self.search_version(pkg_name, version)
    old_current = self.get_current(pkg_name) or ''
    if version == old_current:
      return
    del self.packages_versions[pkg_name]
    if self.verbose:
      print '%s: %s => %s activating' % (self.host, pkg_name, version)
    self._call_ssh(Template('''
if [ 'X' != 'X$currentVer' ]; then
  if [ -x '$oldCtl' ]; then
    '$oldCtl' stop
  fi &&
  rm -f '$currentLink'
fi &&
ln -s '$version' '$currentLink' &&
if [ -x '$newCtl' ]; then
  $newCtl setlive &&
  '$newCtl' start
fi''').substitute({
      'currentVer': old_current,
      'oldCtl': os.path.join(self.repo, pkg_name, old_current, 'control'),
      'newCtl': os.path.join(self.repo, pkg_name, version, 'control'),
      'version': version,
      'currentLink': os.path.join(self.repo, pkg_name, 'current')}), dry_run=self.dry_run)

