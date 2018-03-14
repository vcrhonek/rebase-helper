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

import rebasehelper.utils


class LoggerHelper(object):
    """
    Helper class for setting up a logger
    """

    @staticmethod
    def get_basic_logger(logger_name, level=logging.DEBUG):
        """
        Sets-up a basic logger without any handler

        :param logger_name: Logger name
        :param level: severity level
        :return: created logger
        """
        basic_logger = logging.getLogger(logger_name)
        basic_logger.setLevel(level)
        return basic_logger

    @staticmethod
    def add_stream_handler(logger_object, level=None, formatter_object=None):
        """
        Adds console handler with given severity.

        :param logger_object: logger object to add the handler to
        :param level: severity level
        :param formatter_object: formatter object used to format logged messages
        :return: created handler object
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
        """
        Adds FileHandler to a given logger

        :param logger_object: Logger object to which the file handler will be added
        :param path: Path to file where the debug log will be written
        :return: None
        """
        file_handler = logging.FileHandler(path, 'w')
        if level:
            file_handler.setLevel(level)
        if formatter_object:
            file_handler.setFormatter(formatter_object)
        logger_object.addHandler(file_handler)

    @staticmethod
    def add_logging_level(level_name, level_number, method_name=None):
        if method_name is None:
            method_name = level_name.lower()

        if hasattr(logging, level_name):
            raise AttributeError('{} already defined in logging module'.format(level_name))
        if hasattr(logging, method_name):
            raise AttributeError('{} already defined in logging module'.format(method_name))
        if hasattr(logging.getLoggerClass(), method_name):
            raise AttributeError('{} already defined in logger class'.format(method_name))

        def log_level(self, message, *args, **kwargs):
            if self.isEnabledFor(level_number):
                self._log(level_number, message, args, **kwargs)  # pylint: disable=protected-access

        logging.addLevelName(level_number, level_name)
        setattr(logging, level_name, level_number)
        setattr(logging.getLoggerClass(), method_name, log_level)


LoggerHelper.add_logging_level('SUCCESS', logging.INFO + 5)
LoggerHelper.add_logging_level('HEADING', logging.INFO + 6)
LoggerHelper.add_logging_level('IMPORTANT', logging.INFO + 7)


class ColorizingStreamHandler(logging.StreamHandler):
    level_map = {
        logging.DEBUG: {'fg': 'brightblack', 'bg': 'default', 'style': None},
        logging.INFO: {'fg': 'default', 'bg': 'default', 'style': None},
        logging.SUCCESS: {'fg': 'green', 'bg': 'default', 'style': None},  # pylint: disable=no-member
        logging.HEADING: {'fg': 'yellow', 'bg': 'default', 'style': None},  # pylint: disable=no-member
        logging.IMPORTANT: {'fg': 'red', 'bg': 'default', 'style': None},  # pylint: disable=no-member
        logging.WARNING: {'fg': 'yellow', 'bg': 'default', 'style': None},
        logging.ERROR: {'fg': 'red', 'bg': 'default', 'style': 'bold'},
        logging.CRITICAL: {'fg': 'white', 'bg': 'red', 'style': 'bold'},
    }

    def emit(self, record):
        try:
            message = self.format(record)
            rebasehelper.utils.ConsoleHelper.cprint(message, **self.level_map.get(record.levelno, None))
            self.flush()
        except Exception:  # pylint: disable=broad-except
            self.handleError(record)


#  the main rebase-helper logger
logger = LoggerHelper.get_basic_logger('rebase-helper')
#  logger for output tool
logger_output = LoggerHelper.get_basic_logger('output-tool', logging.INFO)
logger_report = LoggerHelper.get_basic_logger('rebase-helper-report', logging.INFO)
logger_upstream = LoggerHelper.get_basic_logger('rebase-helper-upstream')
LoggerHelper.add_stream_handler(logger_output)
formatter = logging.Formatter("%(levelname)s: %(message)s")
