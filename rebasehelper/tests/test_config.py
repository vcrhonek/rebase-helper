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

import pytest
import six

from six.moves import configparser

from rebasehelper.cli import CLI
from rebasehelper.config import Config


class TestConfig(object):
    CONFIG_FILE = 'test_config.cfg'

    @pytest.fixture
    def config_file(self, config_args):
        config = configparser.ConfigParser()
        config.add_section('Section1')
        for key, value in six.iteritems(config_args):
            config.set('Section1', key, value)
        with open(self.CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

        return os.path.abspath(self.CONFIG_FILE)

    @pytest.mark.parametrize('config_args', [
        {
            'changelog-entry': 'Updated to',
            'versioneer': 'pypi',
        },
        {},
    ], ids=[
        'configured',
        'empty',
    ])
    def test_get_config(self, config_args, config_file):
        config = Config(config_file)
        expected_result = {k.replace('-', '_'): v for k, v in six.iteritems(config_args)}
        assert expected_result == config.config

    @pytest.mark.parametrize('cli_args, config_args, merged', [
        (
            [
                '--changelog-entry', 'Version set to',
                '--buildtool', 'rpmbuild',
            ],
            {
                'changelog-entry': 'Updated to ',
                'versioneer': 'pypi',
            },
            {
                'changelog-entry': 'Version set to',
                'versioneer': 'pypi',
                'buildtool': 'rpmbuild',
                'color': 'auto',
            },
        ),
    ], ids=[
            'CLI with config',
    ])
    def test_merge(self, cli_args, merged, config_file):
        expected_result = {k.replace('-', '_'): v for k, v in six.iteritems(merged)}
        cli = CLI(cli_args)
        config = Config(config_file)
        config.merge(cli)
        # True if expected_result is a subset of conf.config
        assert six.viewitems(expected_result) <= six.viewitems(config.config)
