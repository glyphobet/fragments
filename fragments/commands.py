# -*- coding: utf-8
from __future__ import unicode_literals

import os
import sys
import hashlib
import argparse
#import difflib

try:
    from itertools import izip as zip
except ImportError:
    pass

from . import __version__, FragmentsError, _file_status, _iterate_over_files, _smart_open
from .config import FragmentsConfig, configuration_directory_name, find_configuration, ConfigurationFileCorrupt, ConfigurationFileNotFound, ConfigurationDirectoryNotFound
from .diff import _full_diff
from .apply import apply
from .precisecodevillemerge import Weave
from . import color

class ExecutionError(FragmentsError): pass

def help(*args):
    """Prints help."""
    from . import commands
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, help.__name__), description=help.__doc__)
    parser.add_argument('COMMAND', help="command to show help for", nargs="?", choices=__all__)
    args = parser.parse_args(args)
    if args.COMMAND:
        for l in getattr(commands, args.COMMAND)('-h'):
            yield l
    else:
        parser.parse_args(['-h'])


def init(*args):
    """Initialize a new fragments repository. Repository is in a directory named _fragments/, created in either the current working directory, or FRAGMENTS_ROOT if specified."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, init.__name__), description=init.__doc__)
    parser.add_argument('FRAGMENTS_ROOT', help="root directory in which to create the _fragments/ directory", nargs="?")
    args = parser.parse_args(args)

    try:
        config = FragmentsConfig()
    except ConfigurationFileCorrupt as exc:
        config = FragmentsConfig(autoload=False)
        os.rename(config.path, config.path + '.corrupt')
        config.dump()
    except ConfigurationFileNotFound as exc:
        config = FragmentsConfig(autoload=False)
        config.dump()
    except ConfigurationDirectoryNotFound as exc:
        if args.FRAGMENTS_ROOT:
            configuration_parent = os.path.realpath(args.FRAGMENTS_ROOT)
        else:
            configuration_parent = os.getcwd()
        if os.access(configuration_parent, os.R_OK|os.W_OK):
            configuration_path = os.path.join(configuration_parent, configuration_directory_name)
            os.mkdir(configuration_path)
            config = FragmentsConfig(configuration_path, autoload=False)
            config.dump()
        else:
            raise ExecutionError("Could not create fragments directory in '%s', aborting.\n(Do you have the correct permissions?)" % configuration_parent)
    else:
        raise ExecutionError("Current fragments configuration found in '%s', aborting." % config.path)
    yield "Fragments configuration created in '%s'" % config.path


def _file_key(file_path):
    """Converts a file path into a key for storing the file's committed contents in the _fragments/ directory."""
    return hashlib.sha256(('%s:%s' % (__package__, file_path)).encode('utf8')).hexdigest()


_status_to_color = {
    '?':color.Unknown,
    'M':color.Modified,
    'D':color.Deleted,
    'A':color.Added,
    'E':color.Error,
}


def status(*args):
    """
    Get the current status of the fragments repository, limited to FILENAME(s) if specified.
    Limit output to files with status STATUS, if present.
    """
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, status.__name__), description=status.__doc__)
    parser.add_argument('FILENAME', help="files to show status for", nargs="*", default=['.',])
    parser.add_argument('-l', '--limit', type=str, dest="STATUS", default='MDAE ', action="store", help="limit to files in STATUS")
    args = parser.parse_args(args)

    config = FragmentsConfig()
    yield "%s configuration version %s.%s.%s" % ((__package__,) + config['version'])
    yield "stored in %s" % config.directory
    for s, curr_path in _iterate_over_files(args.FILENAME, config, statuses=args.STATUS):
        yield _status_to_color.get(s, str)('%s\t%s' % (s, os.path.relpath(curr_path)))


def follow(*args):
    """Start following changes to one or more FILENAME(s)."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, follow.__name__), description=follow.__doc__)
    parser.add_argument('FILENAME', help="files to follow", nargs="+")
    args = parser.parse_args(args)

    config = FragmentsConfig()
    for s, filename in _iterate_over_files(args.FILENAME, config, statuses='?'):
        fullpath = os.path.realpath(filename)
        if fullpath.startswith(config.root):
            key = os.path.relpath(fullpath, config.root)
            if key in config['files']:
                yield "'%s' is already being followed" % os.path.relpath(filename)
                continue
            if os.access(fullpath, os.W_OK|os.R_OK):
                file_sha = _file_key(key)
                config['files'][key] = file_sha
                yield "'%s' is now being followed (SHA-256: '%s')" % (os.path.relpath(filename), file_sha)
            else:
                yield "Could not access '%s' to follow it" % os.path.relpath(filename)
        else:
            yield "Could not follow '%s'; it is outside the repository" % os.path.relpath(filename)
    config.dump()


def forget(*args):
    """Stop following changes to one or more FILENAME(s)."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, forget.__name__), description=forget.__doc__)
    parser.add_argument('FILENAME', help="files to forget", nargs="+")
    args = parser.parse_args(args)

    config = FragmentsConfig()
    for s, filename in _iterate_over_files(args.FILENAME, config, statuses='MDAE '):
        fullpath = os.path.realpath(filename)
        if fullpath.startswith(config.root):
            key = os.path.relpath(fullpath, config.root)
            if key in config['files']:
                file_sha = config['files'][key]
                sha_path = os.path.join(config.directory, file_sha)
                if os.access(os.path.join(config.directory, file_sha), os.W_OK|os.R_OK):
                    os.unlink(sha_path)
                    yield "'%s' is no longer being followed" % os.path.relpath(filename)
                else:
                    yield "'%s' was never committed and will not be followed" % os.path.relpath(filename)
                del config['files'][key]
            else:
                yield "Could not forget '%s', it was not being followed" % os.path.relpath(filename)
        else:
            yield "Could not forget '%s'; it is outside the repository" % os.path.relpath(filename)
    config.dump()


def rename(*args):
    """
    Rename OLD_FILENAME to NEW_FILENAME or move OLD_FILENAME(s) to NEW_DIRECTORY

    The rename and move commands are the same.

    File(s) on disk, including unfollowed files, are moved, if they are not already in the new location.
    """
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, rename.__name__), description=rename.__doc__)
    parser.add_argument('OLD_FILENAME', help="old file name", nargs='+')
    parser.add_argument('NEW_FILENAME', help="new file name", nargs=1)
    args = parser.parse_args(args)

    def _rename(config, old_name, new_name):
        old_path = os.path.realpath(old_name)
        old_key = os.path.relpath(old_path, config.root)
        new_path = os.path.realpath(new_name)
        new_key = os.path.relpath(new_path, config.root)
        if old_key not in config['files']:
            yield "Could not rename '%s', it is not being tracked" % old_name
        elif new_key in config['files']:
            yield "Could not rename '%s' to '%s', '%s' is already being tracked" % (old_name, new_name, new_name)
        elif os.access(old_path, os.W_OK|os.R_OK) and os.access(new_path, os.W_OK|os.R_OK):
            yield "Could not rename '%s' to '%s', both files already exist" % (old_name, new_name)
        elif not os.access(old_path, os.W_OK|os.R_OK) and not os.access(new_path, os.W_OK|os.R_OK):
            yield "Could not rename '%s' to '%s', neither file exists" % (old_name, new_name)
        else:
            new_sha = _file_key(new_key)
            os.rename(os.path.join(config.directory, config['files'][old_key]), os.path.join(config.directory, new_sha))
            config['files'][new_key] = new_sha
            del config['files'][old_key]
            if os.access(old_path, os.W_OK|os.R_OK):
                os.rename(old_path, new_path)

    config = FragmentsConfig()
    dest_path = os.path.relpath(args.NEW_FILENAME[0])
    dest_isdir = os.path.isdir(dest_path)
    if len(args.OLD_FILENAME) > 1 and not dest_isdir:
        yield "Could not rename multiple files, '%s' is not a directory." % os.path.relpath(dest_path)
        return

    for src_path in args.OLD_FILENAME:
        if os.path.isdir(src_path):
            old_names = list(_iterate_over_files([src_path], config, statuses='MDA '))
            if os.access(dest_path, os.R_OK):
                os.rename(src_path, os.path.join(dest_path, src_path))
                for s, path in old_names:
                    old_name = os.path.relpath(path)
                    new_name = os.path.join(dest_path, old_name)
                    for y in _rename(config, old_name, new_name):
                        yield y
            else:
                os.rename(src_path, dest_path)
                for s, path in old_names:
                    old_name = os.path.relpath(path)
                    new_name = os.path.join(dest_path, old_name[len(src_path)+1:])
                    for y in _rename(config, old_name, new_name):
                        yield y
        else:
            old_name = os.path.relpath(src_path)
            if dest_isdir:
                new_name = os.path.join(dest_path, os.path.basename(src_path))
            else:
                new_name = dest_path
            for y in _rename(config, old_name, new_name):
                yield y

    config.dump()


def diff(*args):
    """Show differences between committed and uncommitted versions, limited to FILENAME(s) if specified."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, diff.__name__), description=diff.__doc__)
    parser.add_argument('FILENAME', help="file(s) to show changes in", nargs="*", default=['.'])
    parser.add_argument('-U', '--unified', type=int, dest="NUM", default=3, action="store", help="number of lines of context to show")
    args = parser.parse_args(args)

    config = FragmentsConfig()

    for s, curr_path in _iterate_over_files(args.FILENAME, config, statuses='MAD'):
        key = os.path.relpath(curr_path, config.root)
        if key not in config['files']:
            yield "Could not diff '%s', it is not being followed" % os.path.relpath(curr_path)
            continue

        if s in 'MAD':
            repo_lines = []
            curr_lines = []
            if s in 'MA':
                with _smart_open(curr_path, 'r') as curr_file:
                    curr_lines = curr_file.readlines()
            if s in 'MD':
                repo_path = os.path.join(config.directory, config['files'][key])
                with _smart_open(repo_path, 'r') as repo_file:
                    repo_lines = repo_file.readlines()
            weave = Weave()
            weave.add_revision(1, repo_lines, [])
            weave.add_revision(2, curr_lines, [])
            for l in _full_diff(weave.merge(1, 2), key, context_lines=args.NUM):
                yield l
            # for dl in difflib.unified_diff(repo_lines, curr_lines, fromfile=key, tofile=key):
            #     yield dl


def commit(*args):
    """Commit changes to the fragments repository, limited to FILENAME(s) if specified."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, commit.__name__), description=commit.__doc__)
    parser.add_argument('FILENAME', help="file(s) to commit", nargs="*", default=['.'])
    args = parser.parse_args(args)

    config = FragmentsConfig()

    for s, curr_path in _iterate_over_files(args.FILENAME, config, statuses='MAD'):
        key = os.path.relpath(curr_path, config.root)
        if key not in config['files']:
            yield "Could not commit '%s' because it is not being followed" % os.path.relpath(curr_path)
            continue

        if s in 'MA':
            repo_path = os.path.join(config.directory, config['files'][key])
            with _smart_open(repo_path, 'w') as repo_file:
                with _smart_open(curr_path, 'r') as curr_file:
                    repo_file.write(curr_file.read())
            os.utime(repo_path, os.stat(curr_path)[7:9])
            yield "'%s' committed" % os.path.relpath(curr_path)
        elif s == 'D':
            yield "Could not commit '%s' because it has been removed, instead revert or forget it" % os.path.relpath(curr_path)
        elif s == ' ':
            yield "Could not commit '%s' because it has not been changed" % os.path.relpath(curr_path)


def revert(*args):
    """Revert changes to the fragments repository, limited to FILENAME(s) if specified."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, revert.__name__), description=revert.__doc__)
    parser.add_argument('FILENAME', help="file(s) to revert", nargs="*", default=['.'])
    args = parser.parse_args(args)

    config = FragmentsConfig()

    for s, curr_path in _iterate_over_files(args.FILENAME, config, statuses='MAD'):
        key = os.path.relpath(curr_path, config.root)
        if key not in config['files']:
            yield "Could not revert '%s' because it is not being followed" % os.path.relpath(curr_path)
            continue

        if s in 'MD':
            repo_path = os.path.join(config.directory,  config['files'][key])
            with _smart_open(curr_path, 'w') as curr_file:
                with _smart_open(repo_path, 'r') as repo_file:
                    curr_file.write(repo_file.read())
            os.utime(curr_path, os.stat(repo_path)[7:9])
            yield "'%s' reverted" % key
        elif s == 'A':
            yield "Could not revert '%s' because it has never been committed" % os.path.relpath(curr_path)
        elif s == ' ':
            yield "Could not revert '%s' because it has not been changed" % os.path.relpath(curr_path)


def fork(*args):
    """
    Create a new file in TARGET_FILENAME based on one or more SOURCE_FILENAME(s).
    Large common sections are preserved;
    differing sections, and common sections shorter than NUM lines between differing sections, are replaced with one newline for each line or conflict.
    """
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, fork.__name__), description=fork.__doc__)
    parser.add_argument('SOURCE_FILENAME', help="old file names", nargs="+")
    parser.add_argument('TARGET_FILENAME', help="new file name")
    parser.add_argument('-U', '--unified', type=int, dest="NUM", default=3, action="store", help="number of lines of context to use")
    args = parser.parse_args(args)

    config = FragmentsConfig()
    new_path = os.path.realpath(args.TARGET_FILENAME)
    new_key = os.path.relpath(new_path, config.root)
    if new_key in config['files']:
        yield "Could not fork into '%s', it is already followed" % os.path.relpath(args.TARGET_FILENAME)
        return
    if os.access(new_path, os.R_OK|os.W_OK):
        yield "Could not fork into '%s', the file already exists" % os.path.relpath(args.TARGET_FILENAME)
        return

    old_filenames = []
    for s, old_name in _iterate_over_files(args.SOURCE_FILENAME, config, statuses='MA ?'):
        old_path = os.path.realpath(old_name)
        old_key = os.path.relpath(old_path, config.root)
        if s == 'D' or not os.access(old_path, os.R_OK):
            yield "Skipping '%s' while forking, it does not exist" % os.path.relpath(old_path)
        else:
            old_filenames.append(old_path)
            if s == '?':
                yield "Warning, '%s' not being followed" % os.path.relpath(old_path)

    if not old_filenames:
        yield "Could not fork; no valid source files specified"
        return

    weave = Weave()

    with _smart_open(old_filenames[0], 'r') as new_file:
        new_lines = new_file.readlines()
    previous_revision = 1
    weave.add_revision(previous_revision, new_lines, [])
    for old_name in old_filenames[1:]:
        current_revision = previous_revision + 1
        with _smart_open(old_name, 'r') as old_file:
            weave.add_revision(current_revision, old_file.readlines(), [])
        new_lines = []
        diff_output = weave.merge(previous_revision, current_revision)
        i = 0
        while i < len(diff_output):
            line_or_conflict = diff_output[i]
            if isinstance(line_or_conflict, tuple):
                old, new = line_or_conflict
                following_conflict_index = 0 # index of furthest following conflict within args.NUM lines
                for j, loc in enumerate(diff_output[i+1:i+1+args.NUM]):
                    if isinstance(loc, tuple):
                        following_conflict_index = j
                new_lines.extend(['\n'] * (following_conflict_index+1)) # add a blank line for each line and conflict we are skipping
                i += following_conflict_index
            else:
                new_lines.append(line_or_conflict)
            i += 1
        previous_revision = current_revision + 1
        weave.add_revision(previous_revision, new_lines, [])

    with _smart_open(new_path, 'w') as new_file:
        new_file.writelines(new_lines)
    yield "Forked new file in '%s', remember to follow and commit it" % os.path.relpath(args.TARGET_FILENAME)
    config.dump()

move = rename


try:
    raw_input
except NameError: # pragma: no cover # Python 3 support
    raw_input = input


def _colorize(line): # pragma: no cover
    if hasattr(line, 'colorize'):
        return line.colorize()
    return line


def _main(): # pragma: no cover
    from . import commands
    print("%s version %s.%s.%s" % ((__package__,) + __version__))
    cmd = None
    if len(sys.argv) > 1:
        if sys.argv[1] in __all__:
            cmd = sys.argv[1]
        else:
            cmds = [c for c in __all__ if c.startswith(sys.argv[1])]
            if len(cmds) == 1:
                cmd = cmds.pop()
            else:
                if len(cmds) > 1:
                    print("Command '%s' is ambiguous, did you mean:" % sys.argv[1])
                    print(' '.join(cmds))
                else:
                    print("No such command '%s'. Available commands are:" % sys.argv[1])
                    print(' '.join(__all__))
    if (cmd): # command is present and legit
        try:
            command_generator = getattr(commands, cmd)(*sys.argv[2:])
            while True:
                try:
                    l = next(command_generator)
                    if isinstance(l, color.Prompt):
                        response = raw_input(_colorize(l))
                        l = command_generator.send(response.strip())
                    print(_colorize(l))
                except StopIteration:
                    break
        except FragmentsError as exc:
            sys.exit(exc.args[0])
        except KeyboardInterrupt:
            pass

__all__ = ['help', 'init', 'status', 'follow', 'forget', 'rename', 'move', 'diff', 'commit', 'revert', 'fork', 'apply']
