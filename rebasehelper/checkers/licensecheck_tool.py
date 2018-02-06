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

import os

import six

from rebasehelper.utils import ProcessHelper
from rebasehelper.checker import BaseChecker


class LicenseCheckTool(BaseChecker):
    """license compare tool"""

    NAME = "licensecheck"
    DEFAULT = True
    category = "SOURCE"

    @classmethod
    def match(cls, cmd=None):
        if cmd == cls.NAME:
            return True
        else:
            return False

    @classmethod
    def get_checker_name(cls):
        return cls.NAME

    @classmethod
    def is_default(cls):
        return cls.DEFAULT

    @classmethod
    def get_license_changes(cls, old_dir, new_dir):
        """
        Finds differences in licenses between old and new source files

        :return: changes dictionary, new_licenses set, disappeared_licenses set
        """
        diffs = []
        for source_dir in [old_dir, new_dir]:
            out = six.StringIO()
            ProcessHelper.run_subprocess(["/usr/bin/licensecheck", source_dir, "--machine", "--recursive"],
                                         output_file=out)
            diff = {}
            for l in out:
                # licensecheck output format: 'Filepath\tlicense'
                file_path, dlicense = l.split('\t')
                file_path = os.path.relpath(file_path, source_dir)
                diff[file_path] = dlicense.strip()
            diffs.append(diff)

        old_lics, new_lics = set(), set()
        changes = {'added': {}, 'changed': {}, 'removed': {}}
        # Get changed licenses in existing files
        for new_file, new_license in six.iteritems(diffs[1]):
            new_lics.add(new_license)
            for old_file, old_license in six.iteritems(diffs[0]):
                old_lics.add(old_license)

                if (new_file == old_file and
                   (new_license != old_license)):
                    new_key = '{} => {}'.format(old_license, new_license)
                    if new_license == 'UNKNOWN':
                        # Conversion `known license` => `None/Unknown`
                        if old_license not in changes['removed']:
                            changes['removed'][old_license] = []
                        changes['removed'][old_license].append(new_file)
                    elif old_license == 'UNKNOWN':
                        # Conversion `None/Unknown` => `known license`
                        if new_license not in changes['added']:
                            changes['added'][new_license] = []
                        changes['added'][new_license].append(new_file)
                    else:
                        # Conversion `known license` => `known license`
                        if new_key not in changes['changed']:
                            changes['changed'][new_key] = []
                        if new_file not in changes['changed'][new_key]:
                            changes['changed'][new_key].append(new_file)

        # Get newly appeared files
        for new_file, new_license in six.iteritems(diffs[1]):
            if new_file not in diffs[0]:
                if new_license not in changes['added']:
                    changes['added'][new_license] = []
                changes['added'][new_license].append(new_file)

        # Get removed appeared files
        for old_file, old_license in six.iteritems(diffs[0]):
            if old_file not in diffs[1]:
                if old_license not in changes['removed']:
                    changes['removed'][old_license] = []
                changes['removed'][old_license].append(old_file)

        new_licenses = new_lics - old_lics
        disappeared_licenses = old_lics - new_lics
        if new_licenses or disappeared_licenses:
            cls.license_changes = True
        return changes, new_licenses, disappeared_licenses

    @classmethod
    def run_check(cls, results_dir, **kwargs):
        """Gets license differences between old and new sources"""
        # Check if license changes occured
        cls.license_changes = False
        cls.results_dir = os.path.join(results_dir, 'licensecheck')
        os.makedirs(cls.results_dir)
        changes, new_licenses, disappeared_licenses = cls.get_license_changes(kwargs['old_dir'], kwargs['new_dir'])
        cls.output_to_report_file(changes, os.path.join(cls.results_dir, cls.NAME + '.txt'))

        return {'path': cls.get_checker_output_dir_short(), 'changes': changes,
                'license_changes': cls.license_changes, 'new_licenses': new_licenses,
                'disappeared_licenses': disappeared_licenses}

    @classmethod
    def output_to_report_file(cls, changes, report_file_path):
        """
        Prints the licensecheck output to a report file
        :param changes: Changes directory produced by licensecheck_tool
        :param report_file_path: path for the report file
        :return:
        """
        output_string = [cls.get_underlined_title("licensecheck").lstrip()]
        output_string.append('License changes occured!')
        output_string.append('Removed - license removed to unset or file disappeared')
        output_string.append('Added - license added(previously unset) or new file appeared')
        for change_name, change_info in sorted(six.iteritems(changes)):
            if not change_info:
                continue
            output_string.append(cls.get_underlined_title('{} license(s)'.format(change_name)))
            for license_name, files in sorted(six.iteritems(change_info)):
                output_string.append('* {}'.format(license_name))
                for f in sorted(files):
                    output_string.append(' - {}'.format(f))

        with open(report_file_path, 'w') as f:
            f.write('\n'.join(output_string))

    @classmethod
    def format(cls, data):
        """
        Formats pkgdiff data to string
        :param data: pkgdiff data
        :return: string formated output
        """
        output_string = [cls.get_underlined_title("licensecheck")]

        if data['license_changes']:
            output_string.append('License changes occured!')
            for l in sorted(data['new_licenses']):
                output_string.append('* {} appeared'.format(l))
            for l in sorted(data['disappeared_licenses']):
                output_string.append('* {} disappeared'.format(l))

        else:
            output_string.append('No license changes detected.')
        output_string.append('Detailed output can be found in {}'.format(data['path']))
        return output_string
