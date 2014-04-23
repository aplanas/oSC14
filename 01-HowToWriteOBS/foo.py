#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# (C) 2014 lnussel@suse.de
# (C) 2014 aplanas@suse.de
# Distribute under GLPv2 or GPLv3

from StringIO import StringIO
import sys
from xml.etree import cElementTree as ET

from osc import cmdln
from osc import oscerr
from osc.core import get_user_data
from osc.core import meta_get_packagelist
from osc.core import search
from osc.core import show_package_meta
from osc.core import show_project_meta
from osc.core import xpath_join


class DevelInfo(object):
    def __init__(self, prj, pkg, tree):
        self.pkg = pkg
        self.prj = prj
        self.bugowners = None
        self.maintainers = None
        self.develprj = None
        self.develpkg = None
        print 'PROJECT', prj
        print 'PACKAGE', pkg
        print 'TREE', ET.tostring(tree)
        self._parsepersons(tree)
        self._parsedevel(tree)

    def __repr__(self):
        return '<' + self.__str__() + '>'

    def __str__(self):
        s = 'P %s/%s\n' % (self.prj, self.pkg)
        if self.develprj:
            s += '> %s/%s\n' % (self.develprj, self.develpkg or self.pkg)
        if self.bugowners:
            s += 'B %s\n' % ' '.join(self.bugowners)
        if self.maintainers:
            s += 'M ' + '\nM '.join(self.maintainers) + '\n'
        return s

    def _parsedevel(self, tree):
        d = tree.find('devel')
        if d is not None:
            self.develprj = d.get('project')
            self.develpkg = d.get('package')

    def _parsepersons(self, tree):
        for person in tree.findall('person'):
            role = person.get('role')
            if role == 'maintainer':
                if not self.maintainers:
                    self.maintainers = []
                self.maintainers.append(person.get('userid'))
            elif role == 'bugowner':
                if not self.bugowners:
                    self.bugowners = []
                self.bugowners.append(person.get('userid'))
            else:
                print >>sys.stderr, 'unknown role %s in %s/%s' % (role, self.prj, self.pkg)


def get_develinfo(self, apiurl, prj, pkg, followdevel=True, verbose=False):
    if prj in self._metacache and pkg in self._metacache[prj]:
        di = self._metacache[prj][pkg]
    else:
        try:
            m = show_package_meta(apiurl, prj, pkg)
        except Exception, e:
            return

        tree = ET.parse(StringIO(''.join(m)))
        di = DevelInfo(prj, pkg, tree)

    dis = [di]

    depth = 0
    if followdevel:
        while di.develprj:
            prj = di.develprj
            if di.develpkg:
                pkg = di.develpkg
            if verbose:
                print "Following to the development space:", prj, "/", pkg
            m = show_package_meta(apiurl, prj, pkg)
            tree = ET.parse(StringIO(''.join(m)))

            di = DevelInfo(prj, pkg, tree)
            dis.append(di)

            if not di.bugowners and not di.maintainers:
                if verbose:
                    print "No dedicated persons in package defined, showing the project persons"
                m = show_project_meta(apiurl, prj)
                tree = ET.parse(StringIO(''.join(m)))
                di._parsepersons(tree)

            depth += 1
            if depth >= 10:
                print >>sys.stderr, 'devel project chain too long or recursive'
                break

    if not di.bugowners and not di.maintainers:
        if verbose:
            print "No dedicated persons in package defined, showing the project persons"
        m = show_project_meta(apiurl, prj)
        tree = ET.parse(StringIO(''.join(m)))
        di._parsepersons(tree)

    return dis

@cmdln.alias('bugreport', 'br')
@cmdln.option('-p', '--project', action='append', help='project')
def do_foo(self, subcmd, opts, *args):
    """${cmd_name}: print bug owners and maintainers

    Usage:
      ${cmd_name} PKG1 [PGK2] ...
          Print bug owners and maintainers of the package
      ${cmd_name} -p PRJ1 [PRJ2] ...
          Search packages inside the list of projects
    ${cmd_option_list}
    """
    apiurl = self.get_api_url()
    prjs = opts.project if opts.project else []
    pkgs = []

    if len(args) < 1:
        if len(prjs) == 1:
            pkgs = meta_get_packagelist(apiurl, prjs[0])
            opts.all = True
        else:
            raise oscerr.WrongArgs('Wrong number of arguments.')
    else:
        pkgs = args

    self._metacache = {}

    if prjs == []:
        xpath = '@name=\'%s\'' % pkgs[0]
        for pkg in pkgs[1:]:
            xpath += ' or @name=\'%s\'' % pkg
        xpath = xpath_join(xpath,
                           '(project/attribute/@name=\'%(attr)s\' or attribute/@name=\'%(attr)s\' or @project=\'%(deflt)s\')' % {
                               'attr': conf.config['maintained_attribute'],
                               'deflt': conf.config['getpac_default_project']
                           }, op='and')
        what = {'package': xpath}
        r = search(apiurl, **what)
        if r:
            for node in r['package']:
                prj = node.get('project')
                pkg = node.get('name')
                prjs += [prj]
                if prj not in self._metacache:
                    self._metacache[prj] = {}
                self._metacache[prj][pkg] = DevelInfo(prj, pkg, node)
        else:
            prjs = []

    dis = []
    for prj in prjs:
        for pkg in pkgs:
            d = self.get_develinfo(apiurl, prj, pkg)
            if d:
                dis += d

    for di in dis:
        print di
