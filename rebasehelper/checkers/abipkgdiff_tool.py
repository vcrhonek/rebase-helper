# -*- coding: utf-8 -*-
#
# This tool helps you to rebase package to the latest version
# Copyright (C) 2013-2014 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# he Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Authors: Petr Hracek <phracek@redhat.com>
#          Tomas Hozza <thozza@redhat.com>

from __future__ import print_function
import os
import re

import rpm
import six

from rebasehelper.utils import ProcessHelper, RpmHelper
from rebasehelper.logger import logger
from rebasehelper.exceptions import RebaseHelperError, CheckerNotFoundError
from rebasehelper.results_store import results_store
from rebasehelper import settings
from rebasehelper.checker import BaseChecker


class AbiCheckerTool(BaseChecker):
    """abipkgdiff compare tool"""

    NAME = "abipkgdiff"
    DEFAULT = True
    abi_changes = None
    results_dir = ''
    log_name = 'abipkgdiff.log'
    category = 'RPM'

    # Example
    # abipkgdiff --d1 dbus-glib-debuginfo-0.80-3.fc12.x86_64.rpm \
    # --d2 dbus-glib-debuginfo-0.104-3.fc23.x86_64.rpm \
    # dbus-glib-0.80-3.fc12.x86_64.rpm dbus-glib-0.104-3.fc23.x86_64.rpm
    @classmethod
    def match(cls, cmd=None):
        if cmd == cls.NAME:
            return True
        else:
            return False

    @classmethod
    def is_default(cls):
        return cls.DEFAULT

    @classmethod
    def _get_packages_for_abipkgdiff(cls, input_structure=None):
        debug_package = None
        rest_packages = None
        packages = input_structure.get('rpm', [])
        if packages:
            debug_package = [x for x in packages if 'debuginfo' in os.path.basename(x)]
            rest_packages = [x for x in packages if 'debuginfo' not in os.path.basename(x)]

        return debug_package, rest_packages

    @classmethod
    def _find_debuginfo(cls, debug, pkg):
        name = RpmHelper.split_nevra(os.path.basename(pkg))['name']
        debuginfo = '{}-debuginfo'.format(name)
        find = [x for x in debug if RpmHelper.split_nevra(os.path.basename(x))['name'] == debuginfo]
        if find:
            return find[0]
        srpm = RpmHelper.get_info_from_rpm(pkg, rpm.RPMTAG_SOURCERPM)
        debuginfo = '{}-debuginfo'.format(RpmHelper.split_nevra(srpm)['name'])
        find = [x for x in debug if RpmHelper.split_nevra(os.path.basename(x))['name'] == debuginfo]
        if find:
            return find[0]
        return None

    @classmethod
    def run_check(cls, results_dir, **kwargs):
        """Compares old and new RPMs using abipkgdiff"""
        # Check if ABI changes occured
        cls.abi_changes = None
        cls.results_dir = os.path.join(results_dir, cls.NAME)
        os.makedirs(cls.results_dir)
        debug_old, rest_pkgs_old = cls._get_packages_for_abipkgdiff(results_store.get_build('old'))
        debug_new, rest_pkgs_new = cls._get_packages_for_abipkgdiff(results_store.get_build('new'))
        cmd = [cls.NAME]
        reports = {}
        for pkg in rest_pkgs_old:
            command = list(cmd)
            debug = cls._find_debuginfo(debug_old, pkg)
            if debug:
                command.append('--d1')
                command.append(debug)
            old_name = RpmHelper.split_nevra(os.path.basename(pkg))['name']
            find = [x for x in rest_pkgs_new if RpmHelper.split_nevra(os.path.basename(x))['name'] == old_name]
            if not find:
                logger.warning('New version of package %s was not found!', old_name)
                continue
            new_pkg = find[0]
            debug = cls._find_debuginfo(debug_new, new_pkg)
            if debug:
                command.append('--d2')
                command.append(debug)
            command.append(pkg)
            command.append(new_pkg)
            logger.debug('Package name for ABI comparison %s', old_name)
            output = os.path.join(cls.results_dir, old_name + '.txt')
            try:
                ret_code = ProcessHelper.run_subprocess(command, output_file=output)
            except OSError:
                raise CheckerNotFoundError("Checker '{}' was not found or installed.".format(cls.NAME))

            if int(ret_code) & settings.ABIDIFF_ERROR and int(ret_code) & settings.ABIDIFF_USAGE_ERROR:
                raise RebaseHelperError('Execution of {} failed.\nCommand line is: {}'.format(cls.NAME, cmd))
            reports[old_name] = int(ret_code)
        return dict(packages=cls.parse_abi_logs(reports),
                    abi_changes=cls.abi_changes,
                    path=cls.get_checker_output_dir_short())

    @classmethod
    def parse_abi_logs(cls, reports):
        """
        Parse abipkgdiff logs
        :param reports: dictionary with paths to the logs of the produced (sub)packages
        :return: returns dict of packages names with its abipkgdiff changes
        """
        def parse_changes(lines):
            """
            Parses each line with abipkgdiff output info
            :param lines: list of lines of changes
            :return: dictionary of list of changes

            Example abipkgdiff line:
            '  Functions changes summary: 3 Removed, 0 Changed, 0 Added functions (4 filtered out)'
            """
            summary_re = re.compile(r'''^
            \s+(?P<kind>[\w\s]+changes\s+summary):\s+
            (?P<changes>.+)
            $
            ''', re.VERBOSE)
            changes_re = re.compile(r'''
            (?P<count>\d+)\s+
            (?P<what>Added|Changed|Removed)(\s+functions|variables)?
            (\s+\((?P<filtered_out>\d+)\s+filtered\s+out\))?
            ''', re.VERBOSE)
            result = {}
            for line in lines:
                ms = summary_re.match(line)
                if ms:
                    ds = ms.groupdict()
                    result[ds['kind']] = {}
                    for mc in changes_re.finditer(ds['changes']):
                        dc = mc.groupdict()
                        if int(dc['count']) or dc['filtered_out']:
                            result[ds['kind']][dc['what']] = dc
            return result

        pkgs = {}
        for pkg, ret_code in six.iteritems(reports):
            # If no abi changes for the package, store empty dictionary
            cur_pkg = {}
            if ret_code:
                with open(os.path.join(cls.results_dir, pkg + '.txt'), 'r') as f:
                    cur_pkg = parse_changes(f.readlines())
                    cls.abi_changes = True
            pkgs[pkg] = cur_pkg
        return pkgs

    @classmethod
    def format(cls, data):
        """
        Format abipkgdiff output
        :param data: abipkgdiff dictionary output
        :return: formated abipkgdiff list of strings
        """
        output_lines = [cls.get_underlined_title('abipkgdiff')]
        if not data['abi_changes']:
            output_lines.append('No ABI changes occured')
            return output_lines

        for pkg_name, pkg_changes in sorted(six.iteritems(data['packages'])):
            if not pkg_changes:
                continue
            output_lines.append("ABI changes in {}:".format(pkg_name))

            for sum_title, changes_list in sorted(six.iteritems(pkg_changes)):
                if not changes_list:
                    continue
                output_lines.append("{}".format(sum_title))

                for change_name, change_info in sorted(six.iteritems(changes_list)):
                    if change_info['filtered_out']:
                        output_lines.append(" - {} {} (filtered out {})".format(change_name,
                                                                                change_info['count'],
                                                                                change_info['filtered_out']))
                    else:
                        output_lines.append(" - {} {}".format(change_name, change_info['count']))
        output_lines.append("Details in {}:".format(data['path']))
        for pkg_name, pkg_changes in sorted(six.iteritems(data['packages'])):
            output_lines.append(" - {}.txt".format(pkg_name))

        return output_lines
