#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A simple GUI for moodlescrapr3."""

from gooey import Gooey, GooeyParser

from moodlescrapr3 import main


@Gooey(program_name='moodlescrapr', default_size=(810, 530))
def arg_parse():
    """Argument parser."""

    parser = GooeyParser(description='ACBT moodle scraper (by chehanr)')
    auth_group = parser.add_argument_group('Authentication')
    auth_group.add_argument('-u', '--username', action='store', dest='username',
                            help='moodle username', required=True)
    auth_group.add_argument('-p', '--password', action='store', dest='password',
                            help='moodle password', required=True,  widget='PasswordField')
    optional_group = parser.add_argument_group('Optional Arguments')
    optional_group.add_argument('-s', '--subject', action='store', dest='subject',
                                help='scrape only specific subject (comma separated)', required=False)
    optional_group.add_argument('-w', '--week', action='store', dest='week',
                                help='scrape only specific week number (comma separated)', required=False)
    optional_group.add_argument('-l', '--list-subjects', action='store_true', dest='list_subjects',
                                help='list available subjects', required=False)
    results = parser.parse_args()

    return results


if __name__ == '__main__':
    args = arg_parse()
    main(args.username, args.password,
         args.subject, args.week, args.list_subjects)
