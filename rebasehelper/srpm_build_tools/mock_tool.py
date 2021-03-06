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

from rebasehelper.logger import logger
from rebasehelper.build_helper import SRPMBuildToolBase, SourcePackageBuildError, MockTemporaryEnvironment
from rebasehelper.utils import PathHelper
from rebasehelper.utils import ProcessHelper


class MockSRPMBuildTool(SRPMBuildToolBase):

    CMD = "mock"
    DEFAULT = False
    logs = []

    @classmethod
    def get_build_tool_name(cls):
        return cls.CMD

    @classmethod
    def is_default(cls):
        return cls.DEFAULT

    @classmethod
    def _build_srpm(cls, spec, workdir, results_dir, srpm_results_dir, srpm_builder_options):
        """
        Build SRPM using mock.

        :param spec: abs path to SPEC file inside the rpmbuild/SPECS in workdir.
        :param workdir: abs path to working directory with rpmbuild directory
                        structure, which will be used as HOME dir.
        :param results_dir: abs path to dir where the log should be placed.
        :param srpm_results_dir: path to directory where SRPM will be placed.
        :param srpm_builder_options: list of additional options for mock build tool(eg. '-r fedora-XX-x86_64').
        :return:  abs path to built SRPM.
        """
        logger.info("Building SRPM")
        spec_loc = os.path.dirname(spec)
        output = os.path.join(results_dir, "build.log")

        path_to_sources = os.path.join(workdir, 'SOURCES')

        cmd = ['mock', '--old-chroot', '--buildsrpm']
        if srpm_builder_options is not None:
            cmd.extend(srpm_builder_options)
        cmd.extend(['--spec', spec])
        cmd.extend(['--sources', path_to_sources])
        cmd.extend(['--resultdir', results_dir])

        ret = ProcessHelper.run_subprocess_cwd_env(cmd,
                                                   cwd=spec_loc,
                                                   env={'HOME': workdir},
                                                   output_file=output)

        build_log_path = os.path.join(srpm_results_dir, 'build.log')
        mock_log_path = os.path.join(srpm_results_dir, 'mock_output.log')
        root_log_path = os.path.join(srpm_results_dir, 'root.log')

        if ret == 0:
            return PathHelper.find_first_file(workdir, '*.src.rpm')
        if ret == 1:
            if not os.path.exists(build_log_path) and os.path.exists(mock_log_path):
                logfile = mock_log_path
            else:
                logfile = build_log_path
        else:
            logfile = root_log_path
        cls.logs = [l for l in PathHelper.find_all_files(srpm_results_dir, '*.log')]
        raise SourcePackageBuildError("Building SRPM failed!", logfile=logfile)

    @classmethod
    def build(cls, spec, results_dir, **kwargs):
        """
        Build SRPM with chosen SRPM Build Tool

        :param spec: SpecFile object
        :param results_dir: absolute path to DIR where results should be stored
        :return: absolute path to SRPM, list with absolute paths to logs
        """
        srpm_results_dir = os.path.join(results_dir, "SRPM")
        sources = spec.get_sources()
        patches = [p.get_path() for p in spec.get_patches()]
        with MockTemporaryEnvironment(sources, patches, spec.get_path(),
                                      srpm_results_dir) as tmp_env:
            srpm_builder_options = cls.get_srpm_builder_options(**kwargs)

            env = tmp_env.env()
            tmp_dir = tmp_env.path()
            tmp_spec = env.get(MockTemporaryEnvironment.TEMPDIR_SPEC)
            tmp_results_dir = env.get(
                MockTemporaryEnvironment.TEMPDIR_RESULTS)

            srpm = cls._build_srpm(tmp_spec, tmp_dir, tmp_results_dir, srpm_results_dir,
                                   srpm_builder_options=srpm_builder_options)

        logger.info("Building SRPM finished successfully")

        # srpm path in results_dir
        srpm = os.path.join(srpm_results_dir, os.path.basename(srpm))
        logger.debug("Successfully built SRPM: '%s'", str(srpm))
        # gather logs
        logs = [l for l in PathHelper.find_all_files(srpm_results_dir, '*.log')]
        logger.debug("logs: '%s'", str(logs))

        return dict(srpm=srpm, logs=logs)
