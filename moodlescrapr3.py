#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A simple (improved + 1) ACBT scraper to download course files (by /u/chehanr)."""

import getpass
import os
import urllib
from argparse import ArgumentParser

import requests
from bs4 import BeautifulSoup, SoupStrainer

CWD = os.getcwd()


class Download:
    """Download resource files.

    :param session: Current session,
    :param username: Username,
    :param subject_name: Subject Name,
    :param week: Week number
    """

    def __init__(self, session, username, subject_name, week):
        self.session = session
        self.username = username
        self.subject_name = subject_name
        self.week = week
        self.path = '%s/scrape2/%s/%s/Week %s/' % (
            CWD, self.username.upper(), self.subject_name, self.week)

    def resource(self, resource_uri, resource_title):
        """Downloading the resource files."""

        resource_url = 'https://learning.acbt.lk/moodle/mod/resource/%s' % (
            resource_uri)
        if urllib.request.getproxies():
            os.system('wget --load-cookies "%s/cookies.txt" --content-disposition --show-progress --progress=bar:force -N -c "%s" -P "%s" -e use_proxy=yes -e http_proxy="%s" -e https_proxy="%s"' %
                      (CWD, resource_url, self.path, urllib.request.getproxies().get('http'), urllib.request.getproxies().get('https')))
        else:
            os.system('wget --load-cookies "%s/cookies.txt" --content-disposition --show-progress --progress=bar:force -N -c "%s" -P "%s"' %
                      (CWD, resource_url, self.path))


class Scrape:
    """Initial scrape.

    :param session: Current session
    """

    def __init__(self, session):
        self.session = session

    def subjects(self):
        """Returns subject list."""
        response = self.session.get('https://learning.acbt.lk/moodle')
        strainer = SoupStrainer(
            'div', attrs={'class': 'block_course_list sideblock'})
        soup = BeautifulSoup(
            response.content, 'lxml', parse_only=strainer)

        subjects_list = []
        for _ in soup.find_all('div', attrs={'class': 'content'}):
            for _ in _.find_all('ul', attrs={'class': 'list'}):
                for li_subject in _.find_all('li'):
                    for subject in li_subject.find_all('div', attrs={'class': 'column c1'}):
                        _subject_name = subject.text
                        _subject_code = subject.find('a')['title']
                        subject_url = subject.find('a')['href']
                        subject_id = subject_url.split('id=', 1)[1]

                        subject_name = '%s (%s)' % (
                            _subject_code.upper(), _subject_name)

                        subjects_list.append(
                            (subject_name, subject_url, subject_id))

        return subjects_list

    def resources(self, subject_id):
        """Returns resources list."""

        resources_list = []
        week = 0

        params = {'id': subject_id}
        response = self.session.get(
            'https://learning.acbt.lk/moodle/mod/resource/index.php', params=params)
        strainer = SoupStrainer(
            'table', attrs={'class': 'generaltable boxaligncenter'})
        soup = BeautifulSoup(response.content, 'lxml', parse_only=strainer)

        for row in soup.find_all('tr'):
            week_td = row.find_all('td', attrs={'class': 'cell c0'})
            resource_td = row.find_all('td', attrs={'class': 'cell c1'})

            for _week in week_td:
                try:
                    week = int(_week.get_text().strip())
                except:
                    pass
            for resource in resource_td:
                resource_uri = resource.find('a')['href']
                resource_title = resource.get_text().strip()
                if 'view.php?id=' in resource_uri:
                    resources_list.append(
                        (week, resource_uri, resource_title))

        return resources_list


def subject_list(subjects):
    """Returns the list of subjects."""

    _subjects = 'available subjects:\n'
    for i, subject in enumerate(subjects):
        subject_name, _, _ = subject
        _subjects += '%s. %s\n' % (i + 1, subject_name)

    return _subjects


def create_cookies_file(session):
    moodle_id_expire = None
    cookies = session.cookies

    for cookie in cookies:
        if cookie.name == 'MOODLEID_':
            moodle_id_expire = cookie.expires

    cookie_dict = cookies.get_dict()
    cookie_text = 'learning.acbt.lk\tTRUE\t/\tFALSE\t%s\tMOODLEID_\t%s\nlearning.acbt.lk\tTRUE\t/\tFALSE\t0\tMoodleSessionTest\t%s\nlearning.acbt.lk\tTRUE\t/\tTRUE\t0\tNVT\t%s' % (
        moodle_id_expire, cookie_dict.get('MOODLEID_'), cookie_dict.get('MoodleSessionTest'), cookie_dict.get('NVT'))

    with open(CWD + '/cookies.txt', 'w') as f:
        f.write(cookie_text)
        f.close()


def main(username, password, specific_subject, specific_week):
    """Main work."""

    if not username:
        username = input('moodle username: ')
    if not password:
        password = getpass.getpass('moodle password (hidden): ')
    try:
        params = {'username': username, 'password': password}
        session = requests.Session()
        session.post('https://learning.acbt.lk/user/login',
                     data=params, proxies=urllib.request.getproxies())
    except Exception as err:
        print(err)
    else:
        scrape = Scrape(session)
        subjects = scrape.subjects()
        create_cookies_file(session)

        if ARGS.list_subjects:
            print(subject_list(subjects))
        else:
            def _download_resources(resources, subject_name, specific_week=None):
                for resource in resources:
                    week, resource_uri, resource_title = resource
                    if specific_week is None:
                        download = Download(
                            session, username, subject_name, week)
                        download.resource(resource_uri, resource_title)
                    else:
                        if week == specific_week:
                            download = Download(
                                session, username, subject_name, week)
                            download.resource(resource_uri, resource_title)

            for subject in subjects:
                subject_name, _, subject_id = subject
                resources = scrape.resources(subject_id)
                if specific_subject and specific_week:
                    if specific_subject.upper() in subject_name.upper():
                        print('\ndownloading resources from %s in week %s' %
                              (subject_name, specific_week))
                        _download_resources(
                            resources, subject_name, specific_week)
                elif specific_subject or specific_week:
                    if specific_subject:
                        if specific_subject.upper() in subject_name.upper():
                            print('\ndownloading all resources from %s' %
                                  (subject_name))
                            _download_resources(resources, subject_name)
                    elif specific_week:
                        print('\ndownloading resources from %s in week %s' %
                              (subject_name, specific_week))
                        _download_resources(
                            resources, subject_name, specific_week)
                else:
                    print('\ndownloading all resources from %s' %
                          (subject_name))
                    _download_resources(resources, subject_name)


def arg_parse():
    """Argument parser."""

    parser = ArgumentParser(prog='moodlescrapr',
                            description='ACBT moodle scraper (by chehanr)')
    parser.add_argument('-u', '--username', action='store', dest='username',
                        help='moodle username', required=False)
    parser.add_argument('-p', '--password', action='store', dest='password',
                        help='moodle password', required=False)
    parser.add_argument('-s', '--subject', action='store', dest='subject',
                        help='scrape only specific subject', required=False)
    parser.add_argument('-w', '--week', action='store', dest='week',
                        help='scrape only specific week number (w 0 = outline)',
                        type=int, required=False)
    parser.add_argument('-l', '--list subjects', action='store_true', dest='list_subjects',
                        help='list available subjects', required=False)
    results = parser.parse_args()

    return results


ARGS = arg_parse()

if __name__ == '__main__':
    main(ARGS.username, ARGS.password,
         ARGS.subject, ARGS.week)
