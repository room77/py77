#!/usr/bin/python

"""Deploys and activates deploy specs"""
from __future__ import print_function

__author__ = 'chernyak@room77.com (Michael Chernyak)'
__copyright__ = 'Copyright 2013 Room77, Inc.'

import copy
import pylib.mps.cluster.multiplecmd as multiplecmd
from hashlib import md5
import os
import subprocess
import sys
import time
import yaml

from pylib.mps.cluster.packages import Packages

class Error(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)

class Cluster(object):
  @classmethod
  def create(cls, local_root='/home/share/repo',
             conf_dir=os.path.join(os.path.dirname(__file__), 'conf')):
    """Factory method to generate a cluster"""
    with open(os.path.join(conf_dir, 'clusters.yaml'), 'r') as f:
      clusters = yaml.safe_load(f)
    with open(os.path.join(conf_dir, 'hostgroups.yaml'), 'r') as f:
      hostgroups = yaml.safe_load(f)
    releases_fn = os.path.join(conf_dir, 'releases.yaml')
    with open(releases_fn, 'r') as f:
      releases = yaml.safe_load(f)
    with open(os.path.join(conf_dir, 'services.yaml'), 'r') as f:
      services = yaml.safe_load(f)
    return Cluster(hostgroups, services, clusters, releases, local_root)


  def __init__(self, hostgroups, services, clusters, releases, local_root):
    self.hostgroups = hostgroups
    self.services = services
    self.clusters = clusters
    self.releases = releases
    self.local_root = local_root

  def get_hosts(self, elements, recursion=0):
    ++recursion
    if recursion >= 20:
      raise Error('Recursion is too deep')
    s = set()
    for element in elements:
      if element[0] == '@':
        s.update(self.get_hosts(self.hostgroups[element[1:]], recursion))
      else:
        s.add(element)
    return s

  def get_services(self, cluster_name):
    services = set()
    for el in self.clusters[cluster_name]['data']:
      services.update(el['services'])
    return services

  def get_hosts_by_service(self, cluster_name):
    services = {}
    for el in self.clusters[cluster_name]['data']:
      hosts = self.get_hosts(el['hosts'])
      for service_name in el['services']:
        if not service_name  in services:
          services[service_name] = set()
        services[service_name].update(hosts)
    return services

  def get_port_by_service(self, service_name):
    return self.services[service_name].get('port', 0)

  # returns balancers for the service
  # returns default balancers if service port is specified and there is no
  # explicit balancers specification
  def get_balancers(self, service_name):
    if 'balancers' in self.services[service_name]:
      balancers = self.services[service_name]['balancers']
      if balancers == None:
        return {}
      return copy.deepcopy(balancers)
    port = self.get_port_by_service(service_name)
    if port == 0:
      return {}
    return {'http': port + 1000, 'tcp': port + 2000}

  @staticmethod
  def deploy_cmd(arg):
    #print arg
    p = Packages(arg['host'], user=arg['user'],
      key=arg['key'], dry_run=arg['dry_run'],
      verbose=arg['verbose'], compress=arg['compress'])
    p.push(arg['local_root'],arg['package'], arg['version'])

  @staticmethod
  def deploy_cb(exit_code, function, arg, ctx):
    ctx['in_flight'].remove(arg['host'])
    if exit_code:
      raise Exception(arg)
    Cluster.schedule_next_deploy_cmd(ctx)

  @staticmethod
  def schedule_next_deploy_cmd(ctx):
    in_flight = ctx['in_flight']
    spec = ctx['spec']
    selected_host = None
    num_packages = 0
    for host in spec:
      if host in in_flight:
        continue
      if len(spec[host]) > num_packages:
        selected_host = host
        num_packages = len(spec[selected_host])

    if not selected_host:
      return
    in_flight.add(selected_host)
    package, version = spec[selected_host].pop(0)
    args = {}
    args['host'] = selected_host
    args['package'] = package
    args['version'] = version
    for k in ('key', 'user', 'local_root', 'dry_run', 'verbose', 'compress'):
      if k in ctx:
        args[k] = ctx[k]
      else:
        args[k] = ''
    ctx['mcmd'].add_job(Cluster.deploy_cmd, args, Cluster.deploy_cb, ctx)

  def deploy(self, deploy_spec, max_in_flight, dry_run=True, verbose=False):
    spec = self._create_spec(deploy_spec)
    mcmd = multiplecmd.MultipleCmd(max_in_flight)
    cluster_name =  deploy_spec['cluster']
    ctx = {}
    ctx['local_root'] = self.local_root
    for key in ('key', 'user', 'compress'):
      if key in self.clusters[cluster_name]:
        ctx[key] = self.clusters[cluster_name][key]
    ctx['dry_run'] = dry_run
    ctx['verbose'] = verbose
    ctx['spec'] = self._create_deploy_spec(spec)
    ctx['in_flight'] = set()
    ctx['mcmd'] = mcmd
    for i in range(max_in_flight):
      Cluster.schedule_next_deploy_cmd(ctx)
    ctx['mcmd'].run()

  def activate(self, deploy_spec, package_whitelist=[],
               force_restart=False,
               dry_run=True, verbose=False):
    """restarts a set of packages
    Args:
      deploy_spec - the deploy spec to find the package version from
      package_whitelist (list) - list of package names. if specified,
        ONLY packages in this list will be activated
      force_restart (bool) - if True, force restart even if the current
        package version is the same
    """
    spec = self._create_spec(deploy_spec)
    cluster_name = deploy_spec['cluster']
    for key in ('key', 'user'):
      if key in self.clusters[cluster_name]:
        exec('p_%s = "%s"' % (key,  self.clusters[cluster_name][key]))
      else:
        exec('p_%s = ""' % key)
    if 'user' in  self.clusters[cluster_name]:
      user = self.clusters[cluster_name]['user']
    pkg_obj_by_host = {}
    for service in spec:
      service_name = service['name']
      port = None
      if 'port' in service:
        port = service['port']
      for host,package_versions in service['hosts'].items():
        items = []
        # if ANY package in the service needs to be restarted, then
        # you should restart ALL packages in the service
        skip = True
        # create the package object
        if host not in pkg_obj_by_host:
          pkg_obj_by_host[host] = Packages(host, user=p_user, key=p_key,
            dry_run=dry_run, verbose=verbose)
          # preload versions of all packages
          pkg_obj_by_host[host].get_versions()
        pkg_obj = pkg_obj_by_host[host]
        for package_version in package_versions:
          pkg, ver = package_version
          # if the whitelist is specified, only allow whitelisted packages
          if package_whitelist and not pkg in package_whitelist:
            continue
          cur_ver = pkg_obj.get_current(pkg)
          # if force restart is True, do NOT skip packages. restart anyways
          if force_restart or (not cur_ver or cur_ver != ver):
            skip = False
          items.append([pkg, ver])
        if skip:
          continue
        for pkg, ver in items:
          pkg_obj.stop(pkg)
        for pkg, ver in items:
          pkg_obj.set_current(pkg, ver)
        for pkg, ver in items:
          pkg_obj.start(pkg) # the control script waits until the service is up

  def populate_repo(self, deploy_spec_name, deploy_spec, host, ssh_key,
                    local_root, conf_dir,
                    dry_run=True, verbose=False):
    """deploys all the packages in the deploy_spec to the given host
    Args:
      deploy_spec_name (string) - the name of the deploy spec
      deploy_spec - the deploy_spec to extract the packages from
      host - the host to push all the packages in the deploy_spec
      ssh_key - the ssh key to use to connect to the push machine
      local_root - the local root of the package repo
      conf_dir - the current configuration directory location
    """
    # check if the current prod/cluster/conf files are the SAME as the one
    # in the package. if not, give the user two options.
    # (1) continue as is
    # (2) two update the releases.yaml AND generate a new cluster package
    #     with the specified package name AND exit, forcing the user
    #     to re-run the command
    spec = self._create_spec(deploy_spec)
    packages = self._packages_from_spec(spec)
    if 'cluster' in packages:
      sig = self._config_dir_sig(conf_dir, deploy_spec_name)
      for cpkg in packages['cluster']:
        lpath = os.path.join(local_root, 'cluster', cpkg, 'cluster/conf')
        cpkg_sig = self._config_dir_sig(lpath, deploy_spec_name)
        # check if the package signatures differ
        if not sig == cpkg_sig:
          s = input(('Current cluster config files differ from the repo: %s.'
                         ' Would you like to create a new cluster package?'
                         ' Note: once you do, you will need to rerun the '
                         ' command. ([Y]/N) ') % lpath)
          if not s.strip().lower() == 'n':
            os.chdir(subprocess.check_output(
              'git rev-parse --show-toplevel', shell=True).strip())
            subprocess.check_call(
              'prod/update_packages.py --deployspec %s dummy %s' % (
              deploy_spec_name, 'prod/config/cluster'),
              shell=True)
            raise Error(
              'new cluster package generated please re-run the command!')

    # create a new spec and packages with the new releases update
    spec = self._create_spec(deploy_spec)
    packages = self._packages_from_spec(spec)
    # deploy the repo to prod
    cluster_name = deploy_spec['cluster']
    pkgs_obj = Packages(host,
      user=self.clusters[cluster_name].get('user', ''), key=ssh_key,
      dry_run=dry_run, verbose=verbose, compress=True)
    pkgs_obj.get_versions() # preload versions of all packages on the host
    for pname, pset in packages.items():
      for pver in pset:
        pkgs_obj.push(self.local_root, pname, pver)
        # activate the cluster config
        if pname == 'cluster':
          pkgs_obj.activate(pname, pver)

  def clean_repo(self, hostgroup, ssh_key, dry_run=True, verbose=False):
    required_pkg_versions = set()
    for release, packages in sorted(self.releases.items()):
      for pkg_name, version in sorted(packages.items()):
        required_pkg_versions.add((pkg_name, version))
    now = time.time()

    for host in sorted(self.get_hosts([hostgroup])):
      if verbose:
        print("processing host", host)
      pkgs_obj = Packages(host, user='walle', key=ssh_key,
              dry_run=dry_run, verbose=verbose)
      host_packages =  pkgs_obj.get_packages()
      for host_package in host_packages:
        #print "processing package", host_package
        host_package_versions = pkgs_obj.get_versions(host_package)
        current =  pkgs_obj.get_current(host_package)
        for host_package_version in host_package_versions:
          if current and host_package_version == current:
            continue
          if not (host_package, host_package_version) in required_pkg_versions:
            if host_package == 'tmp':
              version_ts = host_package_version.partition('__')[2] .partition('_')[0]
            else:
              version_ts = host_package_version.partition('_')[0]
            try:
              version_age = int((now - int(version_ts)) / 86400)
            except (ValueError):
              raise Error("%s: invalid version %s for packages %s" %(host, host_package_version, host_package))
            if version_age > 15:
              #print "delete", host, version_age, host_package, host_package_version
              pkgs_obj.remove(host_package, host_package_version)
    pass

  @classmethod
  def generate_cluster_pkg(cls, release, name, release_fn):
    """Generate a cluster package with the latest config. The key
    is to write the package name of the cluster package BEFORE
    generating the package
    Args:
      release - the release read from releases.yaml. this struct is
          UPDATED with the latest cluster package name
      name - the release name
      release_fn - the file_name to write the release
    """
    pkg_prefix = Packages.get_valid_package_prefix()
    pkg_name = Packages.generate_package_name(pkg_prefix, 'cluster')
    release[name]['cluster'] = pkg_name
    with open(release_fn, 'w') as f:
      # writeback the releases config with the new release
      f.write(yaml.safe_dump(release, default_flow_style=False))
    # generate the package now that the new releases file is created
    subprocess.check_call(
      'flash --pkg_version_prefix=%s run prod/config/cluster' % pkg_prefix,
      shell=True)
    print('generated cluster package %s and updated releases.yaml' % pkg_name)

  def _create_spec(self, deploySpec):
    spec = []
    self._create_spec_helper(spec, deploySpec['cluster'],
                             self.releases[deploySpec['release']])
    if not 'override' in deploySpec:
      return spec
    for override in deploySpec['override']:
      filter_hosts = None
      filter_services = None
      package_versions = {}
      if 'hosts' in override:
        filter_hosts = self.get_hosts(override['hosts'])
      try:
        if 'services' in override:
          if 'packages' in override:
            raise Error("Can't override both services and packages")
          filter_services = override['services']
          package_versions = self.releases[override['release']]
        else:
          if 'release' in override:
            if 'packages' in override:
              for package in override['packages']:
                package_versions[package] = self.releases[override['release']][package]
            else:
              package_versions = self.releases[override['release']]
          else:
            for package in override['packages']:
              package_versions[package] = override['version']
          filter_services = None
      except:
        print("invalid override", override, file=sys.stderr)
        raise
      self._create_spec_helper(spec, deploySpec['cluster'], package_versions,
        filter_services = filter_services,
        filter_hosts = filter_hosts)
    return spec

  def _create_spec_helper(self, spec, cluster_name, package_versions,
                          filter_services=None, filter_hosts=None):
    """Parses and expands the data vector for a cluster spec, e.g
    -
     hosts: [ '@staging']
     services: [ general_files, repo]
    -
      skips the group if external: 1 is specified. "external" is used for
      services that are not deployment target, such as mysql or node.js
    Returns:
      For each service, finds the packages and generates a output in
      the following format:
      [ {'hosts':
           {'staging-foo.com': [['repo', '111_repo'], ['gen', '123_gen']],
            'staging-bar.com': [['repo', '111_repo'], ['gen', '123_gen']]},
         'name': '$service_name'}, ... ]
      One element in the output is generated for each service
    """
    for el in self.clusters[cluster_name]['data']:
      # skip services that are managed externally
      if 'external' in el and el['external']:
        continue
      # finds all the hosts for a given set of services
      hosts = self.get_hosts(el['hosts'])
      for service_name in el['services']:
        if filter_services and not service_name in filter_services:
          continue
        # check if this service is already in the spec
        s = [s for s in spec if s['name'] == service_name]

        service_already_seen = True
        if len(s) == 0:
          # if the service is not already in the spec, add it
          service_already_seen = False
          s = {}
          s['name'] = service_name
          if 'port' in self.services[service_name]:
            s['port'] = self.services[service_name]['port']
          s['hosts'] = {}
          spec.append(s)
          s = [s for s in spec if s['name'] == service_name]

        if len(s) == 1:
          # the service has been defined once in the spec
          s = s[0]
        else:
          # the service is defined twice. raise error
          raise Error('Duplicate service: %s' % service_name)

        for host in hosts:
          # For each host, look up the service_name in the services structure.
          # the services structure expands to a set of packages. Then for
          # each package, insert into the host list for this service
          #  $host : [ [$package_name1, $package_version1], ...
          if filter_hosts and not host in filter_hosts:
            continue
          if not host in s['hosts']:
            # if this is the first time the service has been seen for this host,
            # simply insert all the packages for this host
            s['hosts'][host] = []
            for package in self.services[service_name]['packages']:
              if not package in package_versions:
                err = ('Package "%s" unspecified in the releases file. ' \
                  + 'Are you sure you are pushing from the right branch?') % package
                self.print_warning(err)
                raise Error(err)
              s['hosts'][host].append([package, package_versions[package]])
          else:
            # if the service has been seen in another context (e.g. as part of
            # a rule for a different host), verify that there are no duplicate
            # packages
            for p,v in package_versions.items():
              pv = [pv for pv in s['hosts'][host] if pv[0] == p]
              if len(pv) > 1:
                raise Error('Duplicate package %s' % p)
              elif len(pv) == 1:
                pv = pv[0]
                pv[1] = v


  def _create_deploy_spec(self, spec):
    ds = {}
    for service in spec:
      for host,package_versions in service['hosts'].items():
        if not host in ds:
          ds[host] = []
        ds[host].extend(package_versions)
    return ds

  def _config_dir_sig(self, conf, deployspec):
    """Computes a signature for the input directory
    Args:
      conf - the conf directory
      deployspec (string) - the name of the deployspec
    Returns:
      (string) signature for the directory OR '' if some parts
        of the deployspec could not be found
    """
    clusters_f = os.path.join(conf, 'clusters.yaml')
    deployspecs_f = os.path.join(conf, 'deployspecs.yaml')
    releases_f = os.path.join(conf, 'releases.yaml')
    with open(deployspecs_f, 'r') as f:
      deployspecs = yaml.safe_load(f)
    if not deployspec in deployspecs:
      print('deployspec %s NOT found in %s' % (deployspec, deployspecs_f))
      return ''
    with open(releases_f, 'r') as f:
      releases = yaml.safe_load(f)
    release_name = deployspecs[deployspec]['release']
    if not release_name in releases:
      print('release %s NOT found in %s' % (release_name, releases_f))
      return ''
    # transition code. TODO(edelman) remove once everything is in the new
    # conf_manual format
    if not os.path.exists(clusters_f):
      print('cluster file %s is in the old format' % clusters_f)
      return ''
    with open(clusters_f, 'r') as f:
      clusters = yaml.safe_load(f)
    cluster_name = deployspecs[deployspec]['cluster']
    if not cluster_name in clusters:
      print('cluster %s NOT found in %s' % (cluster_name, clusters_f))
      return ''
    cluster_str = yaml.safe_dump(clusters[cluster_name], default_flow_style=False)
    release_str = yaml.safe_dump(releases[release_name], default_flow_style=False)
    return md5(cluster_str + release_str).hexdigest()



  def _packages_from_spec(self, spec):
    """Given a list of packages returns the map from package name to set of
    package versions
    Args:
      spec - a deploy spec
    Returns:
      dict from package name to set of package versions
    """
    all_packages = {}
    for service in spec:
      for host, packages in service['hosts'].items():
        for package in packages:
          pname = package[0]
          pversion = package[1]
          if not pname in all_packages:
            all_packages[pname] = set()
          all_packages[pname].add(pversion)
    return all_packages

  def print_warning(self, msg):
    """prints text decorated for a a warning
    Args:
      msg - the text to decorate
    """
    print("%s%s%s" % ('\033[0;31m', msg, '\033[0;m'))

if __name__ == '__main__':
  import argparse
  import os.path

  parser = argparse.ArgumentParser()
  parser.add_argument('--deploy-spec', required=True)
  parser.add_argument('--dry-run', action='store_true')
  parser.add_argument('--verbose', action='store_true')
  parser.add_argument('--local-root', default='/home/share/repo')
  parser.add_argument('--maxinflight', default=6)
  subparsers = parser.add_subparsers(help = "Sub Commands:")
  # deploy parsers
  p = subparsers.add_parser('deploy')
  p.set_defaults(cmd='deploy')
  # activate_parser
  p = subparsers.add_parser('activate')
  p.set_defaults(cmd='activate')
  # populate_repo parser
  p = subparsers.add_parser('populate_repo')
  p.add_argument('--host', required=True, help="host to populate the repo on")
  p.add_argument('--key', default='/home/share/aws/r77_aws_keypair',
                 help="key to use to communicate with the repo")
  p.set_defaults(cmd='populate_repo')
  # clean_repo parser
  p = subparsers.add_parser('clean_repo')
  p.add_argument('--key', default='/home/share/aws/r77_aws_keypair',
                 help="key to use to communicate with the repo")
  p.add_argument('--hostgroup', required=True,
                 help="hostgroup or host to clean the repo on")
  p.set_defaults(cmd='clean_repo')
  # restart parser
  p = subparsers.add_parser('restart')
  p.set_defaults(cmd='restart')
  p.add_argument('packages', nargs='*',
                 help='the space separated list of packages to restart')
  # update_cluster_pkg parser
  p = subparsers.add_parser('update_cluster_pkg')
  p.set_defaults(cmd='update_cluster_pkg')
  args = parser.parse_args()

  conf_dir = os.path.join(os.path.dirname(__file__), 'conf')
  with open(os.path.join(conf_dir, 'deployspecs.yaml'), 'r') as f:
    deployspecs = yaml.safe_load(f)
  cluster  = Cluster.create(args.local_root, conf_dir)
  if not args.deploy_spec in deployspecs:
    err = '***Deploy spec with name %s not found in the deployspecs file!\n' % (
      args.deploy_spec)
    cluster.print_warning(err)
    raise Error(err)

  if args.cmd == 'deploy':
    cluster.deploy(deployspecs[args.deploy_spec], args.maxinflight,
      dry_run=args.dry_run, verbose=args.verbose)
  elif args.cmd == 'activate':
    cluster.activate(deployspecs[args.deploy_spec], dry_run=args.dry_run,
      verbose=args.verbose)
  elif args.cmd == 'populate_repo':
    cluster.populate_repo(args.deploy_spec,
                          deployspecs[args.deploy_spec], args.host,
                          args.key, args.local_root, conf_dir,
                          dry_run=args.dry_run, verbose=args.verbose)
  elif args.cmd == 'clean_repo':
    cluster.clean_repo(args.hostgroup, args.key,
      dry_run=args.dry_run, verbose=args.verbose)
  elif args.cmd == 'restart':
    cluster.activate(
      deployspecs[args.deploy_spec], package_whitelist=args.packages,
      force_restart=True, dry_run=args.dry_run, verbose=args.verbose)
  elif args.cmd == 'update_cluster_pkg':
    cluster.generate_cluster_pkg(cluster.releases,
                                 deployspecs[args.deploy_spec]['release'],
                                 os.path.join(conf_dir, 'releases.yaml'))
