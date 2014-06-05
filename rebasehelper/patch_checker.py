# -*- coding: utf-8 -*-

import os
import sys
import random
import string

from rebasehelper.utils import ProcessHelper
from rebasehelper.logger import logger
from rebasehelper.diff_helper import *
from rebasehelper import settings
from rebasehelper.utils import get_rebase_name, get_temporary_name, get_content_temp

patch_tools = {}

def get_path_to_patch(patch):
    return os.path.join('..', '..', patch)

def register_patch_tool(patch_tool):
    patch_tools.setdefault(patch_tool.shortcut, [])
    patch_tools[patch_tool.shortcut].append(patch_tool)
    return patch_tool

class PatchTool(object):
    """ Class used for using several patching command tools, ...
        Each method should overwrite method like run_check
    """

    helpers = {}

    @classmethod
    def match(cls):
        """
            Method checks whether it is usefull patch method
        """
        return NotImplementedError()

    @classmethod
    def run_patch(cls, **kwargs):
        """
            Method will check all patches in relevant package
        """
        return NotImplementedError()

@register_patch_tool
class FedoraPatchTool(PatchTool):
    shortcut = 'fedora_patch'
    c_patch = 'patch'

    @classmethod
    def run_patch(self, **kwargs):
        """
        The function can be used for patching one
        directory against another
        """
        pass


class Patch(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.patches = kwargs.get('patches', '')
        self.old_sources = kwargs.get('old_dir', None)
        self.new_sources = kwargs.get('new_dir', None)
        self.output_data = []
        self.patched_files = []
        print self.kwargs

    def patch_command(self, patch_name, patch_flags, output=None):
        """
        Patch command whom patches as the
        """
        cmd = ['/usr/bin/patch']
        cmd.append(patch_flags)
        if self.suffix:
            cmd.append('-b ')
            cmd.append('--suffix .' + self.suffix)
        cmd.append(" < ")
        cmd.append(patch_name)
        temp_name = get_temporary_name()
        logger.debug('patch_command(): ' + ' '.join(cmd))
        ret_code = ProcessHelper.run_subprocess_cwd(' '.join(cmd),
                                                    output=temp_name,
                                                    shell=True)
        self.output_data = get_content_temp(temp_name)
        return ret_code

    def get_failed_patched_files(self, patch_name):
        cmd = 'lsdiff {0}'.format(patch_name)
        temp_name = get_temporary_name()
        ret_code = ProcessHelper.run_subprocess_cwd(cmd,
                                                    output=temp_name,
                                                    shell=True)
        if ret_code != 0:
            return None
        self.patched_files = get_content_temp(temp_name)
        failed_files = []
        applied_rules = ['succeeded']
        source_file = ""
        for data in self.output_data:
            if data.startswith('patching file'):
                patch, file_text, source_file = data.strip().split()
                continue
            result = [x for x in applied_rules if x in data ]
            if result:
                continue
            file_list = [x for x in self.patched_files if source_file in x ]
            if source_file in failed_files:
                continue
            failed_files.append(source_file)
        return failed_files

    def apply_patch(self, patch, source_dir):
        """
        Function applies a patch to a old/new sources
        """
        os.chdir(source_dir)
        if source_dir == self.old_sources:
            # for new_sources we want the same suffix as for old_sources
            self.suffix = ''.join(random.choice(string.ascii_letters) for _ in range(6))
        logger.debug('Applying patch {0} to {1}...'.format(patch[0], source_dir))
        ret_code = self.patch_command(get_path_to_patch(patch[0]), patch[1])
        if ret_code != 0:
            logger.error('Patch failed with return code {0}. Updating patch with some diff programs continues.'.format(ret_code))
            patched_files = self.get_failed_patched_files(patch[0])
            if not patched_files:
                logger.error('We are not able to get a list of failed files')
                raise Exception
            patch[0] = get_rebase_name(patch[0])
            self.kwargs['suffix'] = self.suffix
            self.kwargs['failed_files'] = patched_files
            diff = Diff(self.kwargs.get('diff_tool', None))
            ret_code = diff.diff(**self.kwargs)
            # gendiff new_source + self.suffix > patch[0]
            logger.info("Generating patch by gendiff")
            cmd = ['gendiff']
            cmd.append(self.new_sources)
            cmd.append('.'+self.suffix)
            cmd.append('>')
            cmd.append(patch[0])
            temp_name = get_temporary_name()
            print cmd
            ret_code = ProcessHelper.run_subprocess_cwd(' '.join(cmd),
                                                        output=temp_name,
                                                        shell=True)
            gen_diff_output = get_content_temp(temp_name)
            print gen_diff_output
            if ret_code != 0:
                return None

        return patch

    def run_patch(self):
        cwd = os.getcwd()
        for order in sorted(self.patches):
            self.apply_patch(self.patches[order], self.old_sources)
            try:
                patch = self.apply_patch(self.patches[order], self.new_sources)
            except Exception:
                raise Exception
            self.patches[order] = patch
        os.chdir(cwd)
        return self.patches



