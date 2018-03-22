import six
import os

from rebasehelper.output_tool import BaseOutputTool
from rebasehelper.exceptions import RebaseHelperError
from rebasehelper.logger import LoggerHelper, logger, logger_report
from rebasehelper.results_store import results_store
from rebasehelper.checker import checkers_runner


class TextOutputTool(BaseOutputTool):

    """ Text output tool. """

    NAME = "text"
    EXTENSION = 'txt'
    DEFAULT = True

    @classmethod
    def match(cls, cmd=None):
        """
        Checks if the given string matches the output tool

        :param cmd: output tool name
        :return: True if the name matches
        """
        if cmd == cls.NAME:
            return True
        else:
            return False

    @classmethod
    def get_name(cls):
        return cls.NAME

    @classmethod
    def get_extension(cls):
        """
        Get extension of the output_tool

        :return: output_tool extension
        """
        return cls.EXTENSION

    @classmethod
    def print_success_message(cls):
        """Print result message"""
        results = cls.results_store.get_result_message()
        if 'success' in results:
            logger_report.info(results['success'])
        else:
            logger_report.info(results['fail'])

    @classmethod
    def print_changes_patch(cls):
        """Print info about the location of changes.patch"""
        patch = cls.results_store.get_changes_patch()
        if patch is not None:
            logger_report.info('\nPatch with differences between old and new version source files:')
            logger_report.info(cls.prepend_results_dir_name(os.path.basename(patch['changes_patch'])))

    @classmethod
    def print_message_and_separator(cls, message="", separator='='):
        logger_report.info(message)
        logger_report.info(separator * (len(message) - 1))

    @classmethod
    def print_patches(cls, patches):
        cls.print_message_and_separator("\nDownstream Patches")
        if not patches:
            logger_report.info("Patches were neither modified nor deleted.")
            return

        logger_report.info("Rebased patches are located in %s", cls.prepend_results_dir_name('rebased-sources'))
        logger_report.info("Legend:")
        logger_report.info("[-] = already applied, patch removed")
        logger_report.info("[*] = merged, patch modified")
        logger_report.info("[!] = conflicting or inapplicable, patch skipped")
        logger_report.info("[ ] = patch untouched")

        patches_out = list()
        for patch_type, patch_list in sorted(six.iteritems(patches)):
            if patch_list:
                symbols = dict(deleted='-', modified='*', inapplicable='!')
                for patch in sorted(patch_list):
                    patches_out.append(' * {0:40} [{1}]'.format(os.path.basename(patch),
                                                                symbols.get(patch_type, ' ')))
        logger_report.info('\n'.join(sorted(patches_out)))

    @classmethod
    def print_rpms_and_logs(cls, rpms, version):
        """
        Prints information about location of RPMs and logs created during rebase
        :param rpms: dictionary of (S)RPM paths
        :param version: new/old version string
        :return:
        """
        pkgs = ['srpm', 'rpm']
        if not rpms.get('rpm', None):
            return
        message = '\n{} packages'.format(version)
        cls.print_message_and_separator(message=message, separator='-')
        for type_rpm in pkgs:
            srpm = rpms.get(type_rpm, None)
            if not srpm:
                continue

            if type_rpm == 'srpm':
                message = "\nSource packages and logs are in directory %s:"
            else:
                message = "\nBinary packages and logs are in directory %s:"

            if isinstance(srpm, str):
                # Print SRPM path
                dirname = os.path.dirname(srpm)
                logger_report.info(message, cls.prepend_results_dir_name(version.lower() + '-build', 'SRPM'))
                logger_report.info(" - %s", os.path.basename(srpm))
                # Print SRPM logs
                cls.print_build_logs(rpms, dirname)

            else:
                # Print RPMs paths
                dirname = os.path.dirname(srpm[0])
                logger_report.info(message, cls.prepend_results_dir_name(version.lower() + '-build', 'RPM'))
                for pkg in sorted(srpm):
                    logger_report.info(" - %s", os.path.basename(pkg))
                # Print RPMs logs
                cls.print_build_logs(rpms, dirname)

    @classmethod
    def print_build_logs(cls, rpms, dirpath):
        """Function is used for printing rpm build logs"""
        if rpms.get('logs', None) is None:
            return
        for logs in sorted(rpms.get('logs', None)):
            if dirpath not in logs:
                # Skip logs that do not belong to curent rpms(and version)
                continue
            logger_report.info(' - %s', os.path.basename(logs))

    @classmethod
    def print_summary(cls, path, results):
        """Function is used for printing summary information"""
        if results.get_summary_info():
            for key, value in six.iteritems(results.get_summary_info()):
                logger.info("%s %s\n", key, value)

        try:
            LoggerHelper.add_file_handler(logger_report, path)
        except (OSError, IOError):
            raise RebaseHelperError("Can not create results file '{}'".format(path))

        cls.results_store = results

        cls.print_success_message()
        logger_report.info("Rebase helper results are located in %s", os.path.dirname(path))

        cls.print_changes_patch()

        cls.print_checkers_text_output(results.get_checkers())

        if results.get_patches():
            cls.print_patches(results.get_patches())

        cls.print_message_and_separator("\nRPMS")
        for pkg_version in ['old', 'new']:
            pkg_results = results.get_build(pkg_version)
            if pkg_results:
                cls.print_rpms_and_logs(pkg_results, pkg_version.capitalize())

    @classmethod
    def print_checkers_text_output(cls, checkers_results):
        """Function prints text output for every checker"""
        if checkers_results:
            for check_tool in six.itervalues(checkers_runner.plugin_classes):
                for check, data in sorted(six.iteritems(checkers_results)):
                    if check == check_tool.get_checker_name():
                        logger_report.info('\n'.join(check_tool.format(data)))

    @classmethod
    def run(cls, logs, app):  # pylint: disable=unused-argument
        cls.print_summary(cls.get_report_path(app), results_store)
