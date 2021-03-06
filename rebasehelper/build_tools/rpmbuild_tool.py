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

from rebasehelper.utils import ProcessHelper
from rebasehelper.logger import logger
from rebasehelper.utils import PathHelper
from rebasehelper.utils import RpmHelper
from rebasehelper.utils import ConsoleHelper
from rebasehelper.build_helper import RpmbuildTemporaryEnvironment
from rebasehelper.build_helper import BuildToolBase
from rebasehelper.build_helper import BinaryPackageBuildError
from rebasehelper.exceptions import RebaseHelperError


class RpmbuildBuildTool(BuildToolBase):  # pylint: disable=abstract-method
    """
    Class representing rpmbuild build tool.
    """

    CMD = "rpmbuild"
    logs = []

    @classmethod
    def _build_rpm(cls, srpm, workdir, results_dir, rpm_results_dir, builder_options=None):
        """
        Build RPM using rpmbuild.

        :param srpm: abs path to SRPM
        :param workdir: abs path to working directory with rpmbuild directory
                        structure, which will be used as HOME dir.
        :param results_dir: abs path to dir where the log should be placed.
        :param rpm_results_dir: path directory to where RPMs will be placed.
        :return: abs paths to built RPMs.
        """
        logger.info("Building RPMs")
        output = os.path.join(results_dir, "build.log")

        cmd = [cls.CMD, '--rebuild', srpm]
        if builder_options is not None:
            cmd.extend(builder_options)
        ret = ProcessHelper.run_subprocess_cwd_env(cmd,
                                                   env={'HOME': workdir},
                                                   output_file=output)

        build_log_path = os.path.join(rpm_results_dir, 'build.log')

        if ret == 0:
            return [f for f in PathHelper.find_all_files(workdir, '*.rpm') if not f.endswith('.src.rpm')]
        # An error occurred, raise an exception
        logfile = build_log_path
        cls.logs.extend([l for l in PathHelper.find_all_files(rpm_results_dir, '*.log')])
        raise BinaryPackageBuildError("Building RPMs failed!", results_dir, logfile=logfile)

    @classmethod
    def match(cls, cmd=None):
        if cmd == cls.CMD:
            return True
        else:
            return False

    @classmethod
    def get_build_tool_name(cls):
        return cls.CMD

    @classmethod
    def is_default(cls):
        return cls.DEFAULT

    @classmethod
    def accepts_options(cls):
        return True

    @classmethod
    def creates_tasks(cls):
        return False

    @classmethod
    def prepare(cls, spec, conf):
        """
        Checks if all build dependencies are installed. If not, asks user whether they should be installed.
        If he agrees, installs build dependencies using PolicyKit.

        :param spec: SpecFile object
        """
        req_pkgs = spec.get_requires()
        if not RpmHelper.all_packages_installed(req_pkgs):
            question = '\nSome build dependencies are missing. Do you want to install them now'
            if conf.non_interactive or ConsoleHelper.get_message(question):
                if RpmHelper.install_build_dependencies(spec.get_path(), assume_yes=conf.non_interactive) != 0:
                    raise RebaseHelperError('Failed to install build dependencies')

    @classmethod
    def build(cls, spec, results_dir, srpm, **kwargs):
        """
        Builds the RPMs using rpmbuild

        :param spec: SpecFile object
        :param results_dir: absolute path to DIR where results should be stored
        :param srpm: absolute path to SRPM
        :return: dict with:
                 'rpm' -> list with absolute paths to RPMs
                 'logs' -> list with absolute paths to build_logs
        """
        rpm_results_dir = os.path.join(results_dir, "RPM")
        sources = spec.get_sources()
        patches = [p.get_path() for p in spec.get_patches()]
        with RpmbuildTemporaryEnvironment(sources, patches, spec.get_path(), rpm_results_dir) as tmp_env:
            env = tmp_env.env()
            tmp_dir = tmp_env.path()
            tmp_results_dir = env.get(RpmbuildTemporaryEnvironment.TEMPDIR_RESULTS)
            rpms = cls._build_rpm(srpm, tmp_dir, tmp_results_dir, rpm_results_dir,
                                  builder_options=cls.get_builder_options(**kwargs))

        logger.info("Building RPMs finished successfully")

        # RPMs paths in results_dir
        rpms = [os.path.join(rpm_results_dir, os.path.basename(f)) for f in rpms]
        logger.debug("Successfully built RPMs: '%s'", str(rpms))

        # gather logs
        cls.logs.extend([l for l in PathHelper.find_all_files(rpm_results_dir, '*.log')])
        logger.debug("logs: '%s'", str(cls.logs))

        return dict(rpm=rpms, logs=cls.logs)
