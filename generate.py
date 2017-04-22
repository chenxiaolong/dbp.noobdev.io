#!/usr/bin/python3

# Copyright (C) 2014-2016  Andrew Gunnerson <andrewgunnerson@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# ---

# Generate changelogs and create HTML output

import argparse
import distutils.core
import errno
import htmlmin
import jinja2
import json
import os
import shutil
import subprocess
import sys
import tempfile


class Version():
    def __init__(self, version):
        self.ver = version
        s = version.split('.')
        self.p1 = int(s[0])
        self.p2 = int(s[1])
        self.p3 = int(s[2])
        self.p4 = int(s[3][1:])
        self.commit = s[4][1:]

    def __lt__(self, other):
        if self.p1 > other.p1:
            return False
        elif self.p1 < other.p1:
            return True
        elif self.p2 > other.p2:
            return False
        elif self.p2 < other.p2:
            return True
        elif self.p3 > other.p3:
            return False
        elif self.p3 < other.p3:
            return True
        elif self.p4 > other.p4:
            return False
        elif self.p4 < other.p4:
            return True
        else:
            return False

    def __gt__(self, other):
        if self.p1 < other.p1:
            return False
        elif self.p1 > other.p1:
            return True
        elif self.p2 < other.p2:
            return False
        elif self.p2 > other.p2:
            return True
        elif self.p3 < other.p3:
            return False
        elif self.p3 > other.p3:
            return True
        elif self.p4 < other.p4:
            return False
        elif self.p4 > other.p4:
            return True
        else:
            return False

    def __le__(self, other):
        return self == other or self < other

    def __ge__(self, other):
        return self == other or self > other

    def __eq__(self, other):
        return self.p1 == other.p1 \
            and self.p2 == other.p2 \
            and self.p3 == other.p3 \
            and self.p4 == other.p4

    def __str__(self):
        return self.ver

    def __hash__(self):
        return hash(self.ver)


def j2_max(arg):
    return max(*arg)


def j2_min(arg):
    return min(*arg)


def j2_download_page(page_number):
    if page_number == 1:
        return 'index.html'
    else:
        return 'page%d.html' % page_number


# From http://code.activestate.com/recipes/577081-humanized-representation-of-a-number-of-bytes/
def j2_human_size(numbytes, precision=1):
    abbrevs = (
        (1 << 80, 'YiB'),
        (1 << 70, 'ZiB'),
        (1 << 60, 'EiB'),
        (1 << 50, 'PiB'),
        (1 << 40, 'TiB'),
        (1 << 30, 'GiB'),
        (1 << 20, 'MiB'),
        (1 << 10, 'KiB'),
        (1,       'bytes')
    )
    if numbytes == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if numbytes >= factor:
            break
    return '%.*f %s' % (precision, numbytes / factor, suffix)


def get_builds(git_dir, files_dir):
    # List of patcher files and versions
    versions = list()

    for f in os.listdir(files_dir):
        if not os.path.isdir(os.path.join(files_dir, f)):
            print('Skipping ' + f)
            continue

        versions.append(Version(f))

    versions.sort(reverse=True)

    # List of builds
    builds = list()

    # Get file list and changelog
    for i, version in enumerate(versions):
        version_dir = os.path.join(files_dir, versions[i].ver)

        # Get commit log
        process = subprocess.Popen(
            ['git', 'show', '-s', '--format="%cD"', version.commit],
            stdout=subprocess.PIPE,
            cwd=git_dir,
            universal_newlines=True
        )
        timestamp = process.communicate()[0].split('\n')[0]
        timestamp = timestamp.replace('"', '')

        if not timestamp:
            raise Exception('Failed to determine timestamp for commit: %s'
                            % version.commit)

        build = dict()
        build['version'] = str(version)
        build['timestamp'] = timestamp
        build['files'] = list()
        build['commits'] = list()

        # Get list of files
        for variant in os.listdir(version_dir):
            variant_dir = os.path.join(version_dir, variant)

            for f in os.listdir(variant_dir):
                full_path = os.path.join(variant_dir, f)
                rel_path = os.path.relpath(full_path, files_dir)
                splitext = os.path.splitext(f)

                # Skip checksum files
                if splitext[1].endswith('sum'):
                    continue

                file_info = dict()
                file_info['variant'] = variant
                file_info['path'] = rel_path
                file_info['name'] = f
                file_info['size'] = os.path.getsize(full_path)

                checksums = dict()

                for c in ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']:
                    if os.path.exists(full_path + '.' + c + 'sum'):
                        checksums[c] = rel_path + '.' + c + 'sum'

                file_info['checksums'] = checksums

                build['files'].append(file_info)

        # Get list of commits
        if i < len(versions) - 1:
            new_commit = version.commit
            old_commit = versions[i + 1].commit

            # Get commit log
            process = subprocess.Popen(
                ['git', 'log', '--pretty=format:%H\n%s',
                    '%s..%s' % (old_commit, new_commit)],
                stdout=subprocess.PIPE,
                cwd=git_dir,
                universal_newlines=True
            )
            log = process.communicate()[0].split('\n')

            if len(log) <= 1:
                raise Exception('Failed to get commit list between %s and %s'
                                % (old_commit, new_commit))

            for j in range(0, len(log) - 1, 2):
                commit = log[j]
                subject = log[j + 1]

                if sys.version_info.major == 2:
                    subject = subject.decode('UTF-8')

                build['commits'].append({
                    'id': commit,
                    'short_id': commit[0:7],
                    'message': subject
                })

        # Sort by variant and then the name
        build['files'].sort(key=lambda x: (x['variant'], x['name']))

        print('Found version %s (%s) with %d files and %d commits' %
              (build['version'], build['timestamp'], len(build['files']),
               len(build['commits'])))

        builds.append(build)

    return builds


def makedirs_if_not_exist(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e


def generate_tree(git_dir=None, script_dir=None, files_dir=None,
                  target_dir=None, devices_file=None, items_per_page=10,
                  minify=True):
    if not all([git_dir, script_dir, files_dir, target_dir, devices_file]):
        raise ValueError('Missing arguments')

    templates_dir = os.path.join(script_dir, 'tree', 'templates')

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir),
                             undefined=jinja2.StrictUndefined)
    env.filters['max'] = j2_max
    env.filters['min'] = j2_min
    env.filters['download_page'] = j2_download_page
    env.filters['human_size'] = j2_human_size

    # Get list of builds
    if os.path.exists(files_dir):
        builds = get_builds(git_dir, files_dir)
    else:
        builds = list()

    # Get supported devices
    with open(devices_file, 'r') as f:
        devices = json.load(f)

    # Generate index.html
    with open(os.path.join(target_dir, 'index.html'), 'wb') as f:
        template = env.get_template('index.html.j2')
        html = template.render(builds=builds, devices=devices)
        if minify:
            html = htmlmin.minify(html, remove_comments=True)
        f.write(html.encode('UTF-8'))

    # Create downloads directory
    downloads_dir = os.path.join(target_dir, 'downloads')
    makedirs_if_not_exist(downloads_dir)

    # Python does floor division, not truncation
    num_pages = -(-len(builds) // items_per_page)
    if num_pages == 0:
        num_pages = 1

    for i in range(num_pages):
        begin = items_per_page * i
        end = min(items_per_page * (i + 1), len(builds))

        page_path = os.path.join(downloads_dir, j2_download_page(i + 1))

        with open(page_path, 'wb') as f:
            template = env.get_template('download_page.html.j2')
            html = template.render(builds=builds[begin:end],
                                   page_number=(i + 1), total_pages=num_pages)
            if minify:
                html = htmlmin.minify(html, remove_comments=True)
            f.write(html.encode('UTF-8'))

    # Generate supported_devices.html
    with open(os.path.join(target_dir, 'supported_devices.html'), 'wb') as f:
        template = env.get_template('supported_devices.html.j2')
        html = template.render(builds=builds, devices=devices)
        if minify:
            html = htmlmin.minify(html, remove_comments=True)
        f.write(html.encode('UTF-8'))


def clean_old_target(target_dir):
    # Delete index.html
    try:
        os.unlink(os.path.join(target_dir, 'index.html'))
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise e

    dirs = [
        # Download listings
        'downloads',
        # Resources directory
        'res',
        # (OLD) CSS directory
        'css',
        # (OLD) Images directory
        'images',
    ]

    for d in dirs:
        try:
            shutil.rmtree(os.path.join(target_dir, d))
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise e


def check_positive(value):
    num = int(value)
    if num <= 0:
         raise argparse.ArgumentTypeError('%s is not a positive integer' % value)
    return num


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source-dir', required=True,
                        help='DualBootPatcher git repository directory')
    parser.add_argument('-t', '--target-dir', required=True,
                        help='Target HTML output directory')
    parser.add_argument('-d', '--devices-file', required=True,
                        help='Device definitions file')
    parser.add_argument('--items-per-page', type=check_positive, default=10,
                        help='Builds per download page')
    parser.add_argument('--no-minify', action='store_true', default=False,
                        help='Don\'t minify HTML output')

    args = parser.parse_args()

    script_dir = sys.path[0] or '.'
    files_dir = os.path.join(args.target_dir, 'files')

    # Create temporary directory for output
    temp_dir = tempfile.mkdtemp()

    try:
        # Generate target tree in temporary directory
        generate_tree(git_dir=args.source_dir,
                      script_dir=script_dir,
                      files_dir=files_dir,
                      target_dir=temp_dir,
                      devices_file=args.devices_file,
                      items_per_page=args.items_per_page,
                      minify=not args.no_minify)

        # Copy resources
        distutils.dir_util.copy_tree(
                os.path.join(script_dir, 'tree', 'files'), temp_dir)

        # Create target directory
        makedirs_if_not_exist(args.target_dir)

        # Clean up old files
        clean_old_target(args.target_dir)

        # Copy temp directory to target
        distutils.dir_util.copy_tree(temp_dir, args.target_dir)
    finally:
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    main()
