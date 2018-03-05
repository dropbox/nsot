"""
Customized base Django management command specialized for NSoT.
"""

from __future__ import absolute_import, print_function
import argparse
import logging

from django.core.management.base import BaseCommand, CommandError


__all__ = ('NsotCommand', 'CommandError')


class NsotCommand(BaseCommand):
    """Base management command for NSoT that implements a custom logger."""

    # This is here to alleviate an AttributeError when getting /admin/jsi18n/
    # Ref: https://github.com/dropbox/nsot/issues/279
    leave_locale_alone = True

    def create_parser(self, prog_name, subcommand):
        """Override default parser to include default values in help."""
        parser = super(NsotCommand, self).create_parser(
            prog_name, subcommand
        )

        # So that we can see default values in the help text.
        parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

        return parser

    def get_loglevel(self, verbosity, as_string=False):
        """Get the log-level."""
        if verbosity < 1:
            level_name = 'notset'
        elif verbosity > 1:
            level_name = 'debug'
        else:
            level_name = 'info'

        if as_string:
            return level_name
        else:
            return getattr(logging, level_name.upper())

    def set_logging(self, verbosity):
        """Set the log-level."""
        log = logging.getLogger('nsot_server')

        loglevel = self.get_loglevel(verbosity)
        log.setLevel(loglevel)

        self.log = log

    def execute(self, *args, **options):
        """Setup our logging object before execution."""
        self.set_logging(options.get('verbosity'))

        super(NsotCommand, self).execute(*args, **options)
