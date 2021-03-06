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
import shutil

import pytest


TESTS_DIR = os.path.dirname(__file__)
TEST_FILES_DIR = os.path.join(TESTS_DIR, 'testing_files')


@pytest.yield_fixture(autouse=True)
def workdir(request, tmpdir_factory):
    with tmpdir_factory.mktemp('workdir').as_cwd():
        wd = os.getcwd()
        # copy testing files into workdir
        for file_name in getattr(request.cls, 'TEST_FILES', []):
            shutil.copy(os.path.join(TEST_FILES_DIR, file_name), wd)
        yield wd


def pytest_collection_modifyitems(items):
    for item in items:
        # item is an instance of Function class.
        # https://github.com/pytest-dev/pytest/blob/master/_pytest/python.py
        if 'functional' in item.fspath.strpath:
            item.add_marker(pytest.mark.functional)
        else:
            item.add_marker(pytest.mark.standard)
