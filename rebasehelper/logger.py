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

import logging
import six

import rebasehelper.utils


class CustomLogger(logging.Logger):

    TRACE = logging.DEBUG + 1
    SUCCESS = logging.INFO + 5
    HEADING = logging.INFO + 6
    IMPORTANT = logging.INFO + 7

    _nameToLevel = {
        'TRACE': TRACE,
        'SUCCESS': SUCCESS,
        'HEADING': HEADING,
        'IMPORTANT': IMPORTANT,
    }

    def __init__(self, name, level=logging.NOTSET):
        super(CustomLogger, self).__init__(name, level)

        for lev, severity in six.iteritems(self._nameToLevel):
            logging.addLevelName(severity, lev)

    def __getattr__(self, level):
        severity = self._nameToLevel.get(level.upper())

        def log(message, *args, **kwargs):
            if self.isEnabledFor(severity):
                self._log(severity, message, args, **kwargs)

        if severity:
            return log

        raise AttributeError


class LoggerHelper(object):
    """
    Helper class for setting up a logger
    """

    @staticmethod
    def get_basic_logger(logger_name, level=logging.DEBUG):
        """Sets up a basic logger without any handler.

        Args:
            logger_name (str): Logger name.
            level (int): Severity threshold.

        Returns:
            logging.Logger: Created logger instance.

        """
        basic_logger = logging.getLogger(logger_name)
        basic_logger.setLevel(level)
        return basic_logger

    @staticmethod
    def add_stream_handler(logger_object, level=None, formatter_object=None):
        """Adds stream handler to the given logger.

        Args:
            logger_object (logging.Logger): Logger object to add the handler to.
            level (int): Severity threshold.
            formatter_object (logging.Formatter): Formatter object used to format logged messages.

        Returns:
            logging.StreamHandler: Created stream handler instance.

        """
        console_handler = ColorizingStreamHandler()
        if level:
            console_handler.setLevel(level)
        if formatter_object:
            console_handler.setFormatter(formatter_object)
        logger_object.addHandler(console_handler)
        return console_handler

    @staticmethod
    def add_file_handler(logger_object, path, formatter_object=None, level=None):
        """Adds file handler to the given logger.

        Args:
            logger_object (logging.Logger): Logger object to add the handler to.
            path (str): Path to a log file.
            formatter_object (logging.Formatter): Formatter object used to format logged messages.
            level (int): Severity threshold.

        Returns:
            logging.FileHandler: Created file handler instance.

        """
        file_handler = logging.FileHandler(path, 'w')
        if level:
            file_handler.setLevel(level)
        if formatter_object:
            file_handler.setFormatter(formatter_object)
        logger_object.addHandler(file_handler)
        return file_handler


class ColorizingStreamHandler(logging.StreamHandler):
    colors = {
        'dark': {
            logging.DEBUG: {'fg': 'brightblack', 'bg': 'default', 'style': None},
            CustomLogger.TRACE: {'fg': 'red', 'bg': 'default', 'style': None},
            logging.INFO: {'fg': 'default', 'bg': 'default', 'style': None},
            CustomLogger.SUCCESS: {'fg': 'green', 'bg': 'default', 'style': None},
            CustomLogger.HEADING: {'fg': 'yellow', 'bg': 'default', 'style': None},
            CustomLogger.IMPORTANT: {'fg': 'red', 'bg': 'default', 'style': None},
            logging.WARNING: {'fg': 'yellow', 'bg': 'default', 'style': None},
            logging.ERROR: {'fg': 'red', 'bg': 'default', 'style': 'bold'},
            logging.CRITICAL: {'fg': 'white', 'bg': 'red', 'style': 'bold'},
        },
        'light': {
            logging.DEBUG: {'fg': 'brightblack', 'bg': 'default', 'style': None},
            CustomLogger.TRACE: {'fg': 'red', 'bg': 'default', 'style': None},
            logging.INFO: {'fg': 'default', 'bg': 'default', 'style': None},
            CustomLogger.SUCCESS: {'fg': 'green', 'bg': 'default', 'style': None},
            CustomLogger.HEADING: {'fg': 'blue', 'bg': 'default', 'style': None},
            CustomLogger.IMPORTANT: {'fg': 'red', 'bg': 'default', 'style': None},
            logging.WARNING: {'fg': 'blue', 'bg': 'default', 'style': None},
            logging.ERROR: {'fg': 'red', 'bg': 'default', 'style': 'bold'},
            logging.CRITICAL: {'fg': 'white', 'bg': 'red', 'style': 'bold'},
        },
    }

    terminal_background = 'dark'

    def set_terminal_background(self, background):
        if background == 'auto':
            self.terminal_background = rebasehelper.utils.ConsoleHelper.detect_background()
        else:
            self.terminal_background = background

    def emit(self, record):
        try:
            message = self.format(record)
            level_settings = self.colors[self.terminal_background].get(record.levelno, {})
            rebasehelper.utils.ConsoleHelper.cprint(message, **level_settings)
            self.flush()
        except Exception:  # pylint: disable=broad-except
            self.handleError(record)


logging.setLoggerClass(CustomLogger)
#  the main rebase-helper logger
logger = LoggerHelper.get_basic_logger('rebase-helper')
#  logger for output tool
logger_output = LoggerHelper.get_basic_logger('output-tool', logging.INFO)
logger_report = LoggerHelper.get_basic_logger('rebase-helper-report', logging.INFO)
logger_upstream = LoggerHelper.get_basic_logger('rebase-helper-upstream')
output_tool_handler = LoggerHelper.add_stream_handler(logger_output)
formatter = logging.Formatter("%(levelname)s: %(message)s")
main_handler = LoggerHelper.add_stream_handler(logger, logging.DEBUG, formatter)
