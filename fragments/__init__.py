# -*- coding: utf-8
from __future__ import unicode_literals

import os
import codecs

__version__ = (1,2,4)

class FragmentsError(Exception): pass


def _file_status(config, curr_path):
    key = curr_path[len(config.root)+1:]
    if key not in config['files']:
        return '?' # unfollowed

    repo_path = os.path.join(config.directory, config['files'][key])

    repo_exists = os.access(repo_path, os.R_OK|os.W_OK)
    curr_exists = os.access(curr_path, os.R_OK|os.W_OK)

    if repo_exists and curr_exists:
        if os.stat(repo_path)[6] != os.stat(curr_path)[6]:
            return 'M' # current and repo versions have different sizes: file has been modified
        else:
            with open(repo_path, 'r') as repo_file:
                with open(curr_path, 'r') as curr_file:
                    for repo_line, curr_line in zip(repo_file.readlines(), curr_file.readlines()):
                        if len(repo_line) != len(curr_line):
                            return 'M' # corresponding lines have different length: file has been modified
                        if repo_line != curr_line:
                            return 'M' # corresponding lines are different: file has been modified
                    return ' ' # current and repo versions are the same size, corresponding lines are all the same length and all match: file is unmodified
    elif repo_exists:
        return 'D' # deleted
    elif curr_exists:
        return 'A' # added
    else:
        return 'E' # error. this should never happen - both files on disk are missing, but file is being followed


def _expand(dirpath):
    for path, dirs, files in os.walk(dirpath):
        for filename in files:
            yield os.path.join(path, filename)


def _files_by_status(config, dirpath, statuses='MDAE '):
    for path in _expand(dirpath):
        status = _file_status(config, path)
        if status in statuses:
            yield (status, path)


def _iterate_over_files(args, config, statuses='MDAE '):
    seen = set()
    for a in sorted(args):
        if a not in seen:
            seen.add(a)
            path = os.path.realpath(a)
            if os.path.isdir(path):
                for status, path in sorted(_files_by_status(config, path, statuses=statuses)):
                    yield status, path
            else:
                yield _file_status(config, path), path


def _smart_open(path, mode='r'):
    return codecs.open(path, mode=mode, encoding='utf8')
