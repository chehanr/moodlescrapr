#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import getpass
import os
from argparse import ArgumentParser
from os.path import basename

import requests
from bs4 import BeautifulSoup, SoupStrainer
from clint.textui import progress

SESSION = requests.Session()
CWD = os.getcwd()


def reset(subject_id):
    """Neccessory since the moodle is trash."""
    payload = {'id': subject_id, 'week': '0#section-1'}
    SESSION.get('https://learning.acbt.lk/moodle/course/view.php',
                params=payload)


def dir_exist(path):
    """Check path, if not create it."""
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_file_src(username, subject_name, week_id, file_url):
    """A very hacky way to get redirected download urls."""
    response = SESSION.get(file_url, stream=True)
    if response.history:
        """Retrieves docx/pptx/xlsx files mostly. TODO fix this, its too slow."""
        try:
            response = SESSION.head(
                file_url, allow_redirects=False, stream=True)
            file_src = response.headers['Location']
            download(username, subject_name, week_id, file_src)
        except requests.exceptions.RequestException as err:
            print(err)
    else:
        """Assuming its another popup."""
        get_popup_url(username, subject_name, week_id, file_url)


def download(username, subject_name, week_id, file_url):
    """Downloading the files."""
    path = CWD + '\\scrape' + '\\' + username.upper() + '\\' + subject_name + '\\' + \
        'Week ' + str(week_id) + '\\'
    if '/file.php/' in file_url:
        dir_exist(path)
        file_name = basename(file_url)
        print(file_name + ':')
        if not os.path.isfile(path + file_name):
            try:
                response = SESSION.get(file_url, stream=True)
                total_length = int(
                    response.headers.get('content-length', 0))
                with open(path + file_name, 'wb') as file:
                    for chunk in progress.bar(response.iter_content(chunk_size=1024), expected_size=(total_length / 1024) + 1):
                        if chunk:
                            file.write(chunk)
                            file.flush()
                file_on_disk = open(path + file_name, 'rb')
                size_on_disk = len(file_on_disk.read())
                print('[DOWNLOADED] (size on disk:', str(size_on_disk) + ')')
            except:
                print('[ERROR] (failed to create file)')
        else:
            print('[SKIPPED] (already exists)')

    elif '/view.php?' in file_url:
        get_file_src(username, subject_name, week_id, file_url)
    else:
        print(file_url, '[ERROR] (error retrieving direct link)')


def write_content(username, subject_name, week_id, content):
    """
        Create txt file with text from the section.
        TODO replace with markdown.
    """
    path = CWD + '\\scrape' + '\\' + username.upper() + '\\' + subject_name + '\\' + \
        'Week ' + str(week_id) + '\\'
    file_name = 'content_week_' + str(week_id) + '.txt'
    dir_exist(path)
    try:
        with open(path + file_name, 'w') as text_file:
            text_file.write(content)
            text_file.close()
    except:
        print('[ERROR] (failed to write content file)')


def get_popup_url(username, subject_name, week_id, file_url):
    """Retrieve popup urls."""
    if '/file.php/' in file_url:
        download(username, subject_name, week_id, file_url)
    else:
        response = SESSION.get(file_url)
        soup = BeautifulSoup(
            response.content, 'html.parser')
        for popup_urls in soup.find_all('div', attrs={'class': 'popupnotice'}):
            popup_url = popup_urls.find('a')['href']
            download(username, subject_name, week_id, popup_url)


def get_txt(username, subject_name, week_id, file_url):
    """Retrieve text files."""
    if '/file.php/' in file_url:
        download(username, subject_name, week_id, file_url)
    else:
        response = SESSION.get(file_url)
        txt_src = response.url
        if txt_src.endswith('.txt'):
            download(username, subject_name, week_id, txt_src)
        else:
            print(txt_src, '[ERROR] (error retrieving text file)')


def get_image(username, subject_name, week_id, file_url):
    """Retrieve images."""
    if '/file.php/' in file_url:
        download(username, subject_name, week_id, file_url)
    else:
        response = SESSION.get(file_url)
        soup = BeautifulSoup(
            response.content, 'html.parser')
        for img_urls in soup.find_all('div', attrs={'class': 'resourcecontent resourceimg'}):
            img_src = img_urls.find('img')['src']
            download(username, subject_name, week_id, img_src)


def get_pdf(username, subject_name, week_id, file_url):
    """Retrieve pdfs."""
    if '/file.php/' in file_url:
        download(username, subject_name, week_id, file_url)
    else:
        response = SESSION.get(file_url)
        soup = BeautifulSoup(
            response.content, 'html.parser')
        for pdf_urls in soup.find_all('div', attrs={'class': 'resourcepdf'}):
            pdf_src = pdf_urls.find('a')['href']
            download(username, subject_name, week_id, pdf_src)


def get_external_site(file_url):
    """Handle external links. TODO add funtionality."""
    print(file_url, '[IGNORED] (external site)')


def get_archive(username, subject_name, week_id, file_url):
    """Retrieve arhives."""
    if '/file.php/' in file_url:
        download(username, subject_name, week_id, file_url)
    else:
        response = SESSION.get(file_url)
        soup = BeautifulSoup(
            response.content, 'html.parser')
        for archive_urls in soup.find_all('div', attrs={'class': 'resourcepdf'}):
            archive_src = archive_urls.find('a')['href']
            download(username, subject_name, week_id, archive_src)


def get_folder_file(username, subject_name, week_id, file_url):
    """Iterate inside folders."""
    response = SESSION.get(file_url)
    strainer = SoupStrainer('table', attrs={'class': 'files'})
    soup = BeautifulSoup(
        response.content, 'html.parser', parse_only=strainer)
    for file in soup.find_all('tr', attrs={'class': 'file'}):
        for file_urls in file.find_all('td', attrs={'class': 'name'}):
            file_url = file_urls.find('a')['href']
            file_type = file_urls.find(
                'img', attrs={'class': 'icon'})['src']
            if '/file.php/' in file_url:
                download(username, subject_name, week_id, file_url)
            else:
                get_file_type(username, subject_name,
                              week_id, file_type, file_url)


def get_file_type(username, subject_name, week_id, file_type, file_url):
    """
        Determine file type.
        TODO add support for other file types. 
    """
    if file_type == 'https://learning.acbt.lk/moodle/pix/f/pdf.gif':
        get_pdf(username, subject_name, week_id, file_url)
    elif file_type == 'https://learning.acbt.lk/moodle/pix/f/pptx.gif':
        download(username, subject_name, week_id, file_url)
    elif file_type == 'https://learning.acbt.lk/moodle/pix/f/powerpoint.gif':
        download(username, subject_name, week_id, file_url)
    elif file_type == 'https://learning.acbt.lk/moodle/pix/f/docx.gif':
        download(username, subject_name, week_id, file_url)
    elif file_type == 'https://learning.acbt.lk/moodle/pix/f/word.gif':
        download(username, subject_name, week_id, file_url)
    elif file_type == 'https://learning.acbt.lk/moodle/pix/f/xlsx.gif':
        download(username, subject_name, week_id, file_url)
    elif file_type == 'https://learning.acbt.lk/moodle/pix/f/web.gif':
        get_external_site(file_url)
    elif file_type == 'https://learning.acbt.lk/moodle/pix/f/text.gif':
        get_txt(username, subject_name, week_id, file_url)
    elif file_type == 'https://learning.acbt.lk/moodle/pix/f/image.gif':
        get_image(username, subject_name, week_id, file_url)
    elif file_type == 'https://learning.acbt.lk/moodle/pix/f/html.gif':
        get_external_site(file_url)
    elif file_type == 'https://learning.acbt.lk/moodle/pix/f/zip.gif':
        get_archive(username, subject_name, week_id, file_url)
    elif file_type == 'https://learning.acbt.lk/moodle/pix/f/folder.gif':
        get_folder_file(username, subject_name, week_id, file_url)
    else:
        file_type_found_ext = basename(file_type).rsplit('.', 1)[0]
        print(file_url, '[ERROR] (cannot recognize file type',
              '".' + file_type_found_ext + '")')


def get_file(username, subject_name, subject_id, week_id):
    """Retrieve resource urls."""
    print('\n' + 'Downloading files from', subject_name,
          'in week', str(week_id))
    payload = {'id': subject_id, 'week': week_id}
    response = SESSION.get(
        'https://learning.acbt.lk/moodle/course/view.php', params=payload)
    strainer = SoupStrainer('table', attrs={'class': 'weeks'})
    soup = BeautifulSoup(
        response.content, 'html.parser', parse_only=strainer)
    for section in soup.find_all('tr', attrs={'id': 'section-' + str(week_id)}):
        write_content(username, subject_name, week_id, section.text)
        for file_urls in section.find_all('li', attrs={'class': 'activity resource'}):
            file_url = file_urls.find('a')['href']
            if '/resource/' in file_url:
                file_type = file_urls.find(
                    'img', attrs={'class': 'activityicon'})['src']
                get_file_type(username, subject_name,
                              week_id, file_type, file_url)
                reset(subject_id)
    # reset(subject_id)


def scrape(username, specific_subject, specific_week):
    """Initial scrape."""
    response = SESSION.get('https://learning.acbt.lk/moodle')
    strainer = SoupStrainer('div', attrs={'class': 'coursebox clearfix'})
    soup = BeautifulSoup(response.content, 'html.parser', parse_only=strainer)

    if specific_subject:
        specific_subject = specific_subject.upper()

    weeks = []

    if specific_subject and specific_week:
        print('\nScraping week', specific_week, 'files of', specific_subject)
        for subject in soup.find_all('div', attrs={'class': 'name'}):
            subject_name = subject.text
            if subject_name.startswith(specific_subject + ' '):
                subject_url = subject.find('a')['href']
                subject_id = subject_url.split('id=', 1)[1]
                get_file(username, subject_name, subject_id, specific_week)

    elif specific_subject or specific_week:

        if specific_subject:
            print('\nScraping all files of subject', specific_subject)
            for subject in soup.find_all('div', attrs={'class': 'name'}):
                subject_name = subject.text
                if subject_name.startswith(specific_subject + ' '):
                    subject_url = subject.find('a')['href']
                    subject_id = subject_url.split('id=', 1)[1]
                    response = SESSION.get(subject_url)
                    strainer = SoupStrainer('td', attrs={'class': 'content'})
                    soup = BeautifulSoup(
                        response.content, 'html.parser', parse_only=strainer)
                    for _ in soup.find_all('h3', attrs={'class': 'weekdates'}):
                        weeks.append(None)
                        week_id = len(weeks)
                        get_file(username, subject_name, subject_id, week_id)

        if specific_week:
            print('\nScraping all files of week', specific_week)
            for subject in soup.find_all('div', attrs={'class': 'name'}):
                subject_name = subject.text
                subject_url = subject.find('a')['href']
                subject_id = subject_url.split('id=', 1)[1]
                get_file(username, subject_name, subject_id, specific_week)

    else:
        print('\nScraping all files')
        for subject in soup.find_all('div', attrs={'class': 'name'}):
            subject_name = subject.text
            subject_url = subject.find('a')['href']
            subject_id = subject_url.split('id=', 1)[1]
            response = SESSION.get(subject_url)
            strainer = SoupStrainer('td', attrs={'class': 'content'})
            soup = BeautifulSoup(
                response.content, 'html.parser', parse_only=strainer)
            for _ in soup.find_all('h3', attrs={'class': 'weekdates'}):
                weeks.append(None)
                week_id = len(weeks)
                # reset(subject_id)
                get_file(username, subject_name, subject_id, week_id)
            del weeks[:]


def auth(username, password, specific_subject, specific_week):
    """Log into moodle."""
    if not username:
        username = input('Moodle username: ')
    if not password:
        password = getpass.getpass('Moodle password (hidden): ')
    try:
        auth = {'username': username, 'password': password}
        SESSION.post('https://learning.acbt.lk/user/login', data=auth)
        return scrape(username, specific_subject, specific_week)
    except requests.exceptions.RequestException as err:
        print(err)


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
                        help='scrape only specific week number (w 0 = outline)', required=False)
    results = parser.parse_args()
    auth(results.username, results.password, results.subject, results.week)


if __name__ == '__main__':
    arg_parse()
