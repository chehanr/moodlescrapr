#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A simple (improved) ACBT scraper to download course files (by /u/chehanr)."""

import getpass
import os
import re
from argparse import ArgumentParser
from os.path import basename

import requests
from bs4 import BeautifulSoup, SoupStrainer
from halo import Halo

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
        self.path = '%s/scrape/%s/%s/Week %s/' % (
            CWD, self.username.upper(), self.subject_name, self.week)
        self.spinner = Halo(text='', spinner='dots')

    def _dir(self):
        """Check path, if not create it."""
        directory = os.path.dirname(self.path)
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except Exception as err:
            print(err)

    @classmethod
    def _file_size(cls, path, file_name):
        """Return file size."""
        file_on_disk = open(path + file_name, 'rb')
        size_on_disk = len(file_on_disk.read())
        if size_on_disk:
            return size_on_disk

    def resource(self, resource_url, resource_type):
        """Downloading the resource files."""
        file_src = self.file_source(resource_url, resource_type)
        if file_src:
            self._dir()
            chunk_size = 512
            downloaded = 0
            # Removing query strings.
            file_src = file_src.split('?', maxsplit=1)[0]
            file_name = basename(file_src)
            file_extension = os.path.splitext(file_name)[1]
            d_file_name = file_name.ljust(50)[:50]
            d_week = ('week %s' % (self.week)).ljust(8)[:8]
            # d_resource_type = resource_type.ljust(8)[:8]
            d_file_extension = file_extension.ljust(8)[:8]
            if not os.path.isfile(self.path + file_name):
                try:
                    response = self.session.get(file_src, stream=True)
                    total_length = int(
                        response.headers.get('content-length', 0))
                    with open(self.path + file_name, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                downloaded += len(chunk)
                                percentage = (
                                    100 * downloaded / total_length)
                                self.spinner.start()
                                self.spinner.text = '%s | %s | %s | downloading (%s%%)' % (
                                    d_week, d_file_name, d_file_extension, round(percentage, 2))
                                file.write(chunk)
                                file.flush()
                    file_size = self._file_size(self.path, file_name)
                    self.spinner.succeed(
                        text=('%s | %s | %s | downloaded (size: %s)' % (
                            d_week, d_file_name, d_file_extension, file_size)))
                except Exception as err:
                    self.spinner.fail(
                        text=('%s | %s | %s | failed to create file (%s)' % (
                            d_week, d_file_name, d_file_extension, err)))
            else:
                response = self.session.get(file_src, stream=True)
                total_length = int(
                    response.headers.get('content-length', 0))
                file_size = self._file_size(self.path, file_name)

                def _replace_file():
                    """Replace existing files by removing existing."""
                    try:
                        os.remove(self.path + file_name)
                    except Exception as err:
                        print(err)
                    else:
                        self.resource(resource_url, resource_type)

                if file_size == total_length:
                    if ARGS.replace:
                        _replace_file()
                    else:
                        self.spinner.info(text=('%s | %s | %s | skipped (already exists)' % (
                            d_week, d_file_name, d_file_extension)))
                else:
                    self.spinner.info(text=('%s | %s | %s | file changed (size different) %s' % (
                        d_week, d_file_name, d_file_extension, 'replacing...' if ARGS.replace_changed else '')))
                    if ARGS.replace_changed:
                        _replace_file()
                    else:
                        replace_input = input(
                            '> replace file %s? (y) ' % (file_name))
                        if replace_input.lower() in ['y', 'yes']:
                            _replace_file()

    def file_source(self, resource_url, resource_type):
        """Returns file source url."""
        file_src = None
        d_resource_url = resource_url.ljust(50)[:50]
        d_week = ('week %s' % (self.week)).ljust(8)[:8]
        d_resource_type = resource_type.ljust(8)[:8]
        try:
            response = self.session.get(resource_url)
        except Exception as err:
            self.spinner.fail(text=('%s | %s | %s | failed to find source (%s)' % (
                d_week, d_resource_url, d_resource_type, err)))
        if resource_type == 'pdf':
            soup = BeautifulSoup(response.content, 'lxml')
            for pdf_urls in soup.find_all('div', attrs={'class': 'resourcepdf'}):
                file_src = pdf_urls.find('a')['href']
                return file_src
            if not file_src:
                for pdf_urls in soup.find_all('embed', attrs={
                        'type': 'application/x-google-chrome-pdf'}):
                    file_src = file_src.attrs['src']
                    return file_src
            if not file_src:
                self.file_source(resource_url, 'pdf2')
        elif resource_type == 'web':
            self.spinner.info(text=('%s | %s | %s | skipped (external website)' % (
                d_week, d_resource_url, d_resource_type)))
        elif resource_type == 'image':
            soup = BeautifulSoup(
                response.content, 'lxml')
            for img_urls in soup.find_all('div', attrs={'class': 'resourcecontent resourceimg'}):
                file_src = img_urls.find('img')['src']
                return file_src
        elif resource_type == 'html':
            self.spinner.info(text=('%s | %s | %s | skipped (html)' % (
                d_week, d_resource_url, d_resource_type)))
        elif resource_type == 'zip':
            soup = BeautifulSoup(
                response.content, 'lxml')
            for archive_urls in soup.find_all('div', attrs={'class': 'resourcepdf'}):
                file_src = archive_urls.find('a')['href']
                return file_src
        elif resource_type == 'folder':
            strainer = SoupStrainer('table', attrs={'class': 'files'})
            soup = BeautifulSoup(
                response.content, 'lxml', parse_only=strainer)
            for resource in soup.find_all('tr', attrs={'class': 'file'}):
                for resource_urls in resource.find_all('td', attrs={'class': 'name'}):
                    resource_url = resource_urls.find('a')['href']
                    resource_type = resource_urls.find(
                        'img', attrs={'class': 'icon'})['src']
                    if resource_url and resource_type:
                        file_src = self.file_source(
                            resource_url, resource_type)
                        return file_src
        elif resource_type in ['pptx', 'docx', 'xlsx', 'word', 'powerpoint', 'text', 'pdf2']:
            if response.history:
                try:
                    response = self.session.head(
                        resource_url, allow_redirects=False, stream=True)
                    file_src = response.headers['Location']
                    return file_src
                except requests.exceptions.RequestException as err:
                    print(err)
            else:
                # Assuming its another popup.
                # self.file_source(resource_url, 'popup')
                soup = BeautifulSoup(response.content, 'lxml')
                for popup_urls in soup.find_all('div', attrs={'class': 'popupnotice'}):
                    popup_url = popup_urls.find('a')['href']
                    self.file_source(popup_url, resource_type)

                # TODO fix this shit.
        else:
            self.spinner.warn(text=('%s | %s | %s | skipped (not recognized)' % (
                d_week, d_resource_url, d_resource_type)))

        # elif resource_type == 'popup':
        #     soup = BeautifulSoup(response.content, 'lxml')
        #     for popup_urls in soup.find_all('div', attrs={'class': 'popupnotice'}):
        #         popup_url = popup_urls.find('a')['href']
        #         return file_src


class Scrape:
    """Initial scrape.

    :param session: Current session
    """

    def __init__(self, session):
        self.session = session

    def reset(self, subject_id):
        """Neccessory since the moodle is trash."""
        params = {'id': subject_id, 'week': '0'}
        self.session.get(
            'https://learning.acbt.lk/moodle/course/view.php', params=params)

    def week_count(self, subject_url):
        """Returns number of weeks per subject."""
        response = self.session.get(subject_url)
        strainer = SoupStrainer('td', attrs={'class': 'content'})
        soup = BeautifulSoup(
            response.content, 'lxml', parse_only=strainer)
        return len(soup.find_all('h3', attrs={'class': 'weekdates'}))

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

    @classmethod
    def _resource_type(cls, resource_img):
        """Determine file type."""
        image_regex = r'(\w+)(\.\w+)+(?!.*(\w+)(\.\w+)+)'
        resource_img_name = re.search(image_regex, resource_img).group(1)
        return resource_img_name

    def resources(self, subject_id, week):
        """Returns resources list."""
        resources_list = []
        params = {'id': subject_id, 'week': week}
        response = self.session.get(
            'https://learning.acbt.lk/moodle/course/view.php', params=params)
        strainer = SoupStrainer('table', attrs={'class': 'weeks'})
        soup = BeautifulSoup(
            response.content, 'lxml', parse_only=strainer)
        for section in soup.find_all('tr', attrs={'id': 'section-' + str(week)}):
            for resource_urls in section.find_all('li', attrs={'class': 'activity resource'}):
                resource_url = resource_urls.find('a')['href']
                if '/resource/' in resource_url:
                    resource_img = resource_urls.find(
                        'img', attrs={'class': 'activityicon'})['src']
                    resource_type = self._resource_type(resource_img)
                    if resource_type:
                        resources_list.append(
                            (week, resource_url, resource_type))
        return resources_list


def print_subjects(subjects):
    for subject in subjects:
        subject_name, _, _ = subject
        print(subject_name)


def main(username, password, specific_subject, specific_week):
    """Main work."""

    if not username:
        username = input('Moodle username: ')
    if not password:
        password = getpass.getpass('Moodle password (hidden): ')
    try:
        params = {'username': username, 'password': password}
        session = requests.Session()
        session.post('https://learning.acbt.lk/user/login', data=params)
    except requests.exceptions.RequestException as err:
        print(err)
    else:
        scrape = Scrape(session)
        subjects = scrape.subjects()

        if ARGS.list_subjects:
            print_subjects(subjects)
            exit()

        def _download_resources(resources, subject_name):
            for resource in resources:
                week, resource_url, resource_type = resource
                download = Download(session, username, subject_name, week)
                download.resource(resource_url, resource_type)
        for subject in subjects:
            subject_name, subject_url, subject_id = subject
            scrape.reset(subject_id)
            if specific_subject and specific_week:
                if specific_subject.upper() in subject_name:
                    print('\ndownloading resources from %s in week %s' %
                          (subject_name, specific_week))
                    resources = scrape.resources(subject_id, specific_week)
                    _download_resources(resources, subject_name)
            elif specific_subject or specific_week:
                if specific_subject:
                    if specific_subject.upper() in subject_name:
                        print('\ndownloading all resources from %s' %
                              (subject_name))
                        week_count = scrape.week_count(subject_url)
                        for week in range(week_count):
                            resources = scrape.resources(subject_id, week)
                            _download_resources(resources, subject_name)
                elif specific_week:
                    print('\ndownloading resources from %s in week %s' %
                          (subject_name, specific_week))
                    resources = scrape.resources(subject_id, specific_week)
                    _download_resources(resources, subject_name)
            else:
                print('\ndownloading all resources from %s' % (subject_name))
                week_count = scrape.week_count(subject_url)
                for week in range(week_count):
                    resources = scrape.resources(subject_id, week)
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
    parser.add_argument('-r', '--replace', action='store_true', dest='replace',
                        help='force replace existing files', required=False)
    parser.add_argument('-rc', '--replace changed', action='store_true', dest='replace_changed',
                        help='force replace changed files', required=False)
    parser.add_argument('-l', '--list subjects', action='store_true', dest='list_subjects',
                        help='list available subjects', required=False)
    results = parser.parse_args()

    return results


ARGS = arg_parse()

if __name__ == '__main__':
    main(ARGS.username, ARGS.password,
         ARGS.subject, ARGS.week)
