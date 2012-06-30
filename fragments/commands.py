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

from . import __version__, FragmentsError, _iterate_over_files, _smart_open
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
            configuration_parent = os.path.split(os.getcwd())[0]
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
            for repo_line, curr_line in zip(open(repo_path, 'r').readlines(), open(curr_path, 'r').readlines()):
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
    parser.add_argument('FILENAME', help="files to show status for", nargs="*")
    parser.add_argument('-l', '--limit', type=str, dest="STATUS", default=None, action="store", help="limit to files in STATUS")
    args = parser.parse_args(args)

    config = FragmentsConfig()
    if not args.STATUS:
        yield "%s configuration version %s.%s.%s" % ((__package__,) + config['version'])
        yield "stored in %s" % config.directory
    for curr_path in _iterate_over_files(args.FILENAME, config):
        s = _file_status(config, curr_path)
        if not args.STATUS or s in args.STATUS.upper():
            yield _status_to_color.get(s, str)('%s\t%s' % (s, os.path.relpath(curr_path)))


def follow(*args):
    """Start following changes to one or more FILENAME(s)."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, follow.__name__), description=follow.__doc__)
    parser.add_argument('FILENAME', help="files to follow", nargs="+")
    args = parser.parse_args(args)

    config = FragmentsConfig()
    for filename in set(args.FILENAME):
        fullpath = os.path.realpath(filename)
        if fullpath.startswith(config.root):
            key = os.path.relpath(fullpath, config.root)
            if key in config['files']:
                yield "'%s' is already being followed" % os.path.relpath(filename)
                continue
            if os.access(fullpath, os.W_OK|os.R_OK):
                file_sha = hashlib.sha256(('%s:%s' % (__package__, key)).encode('utf8')).hexdigest()
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
    for filename in set(args.FILENAME):
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
    """Rename OLD_FILENAME to NEW_FILENAME, moving the actual file on disk if it has not already been moved."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, rename.__name__), description=rename.__doc__)
    parser.add_argument('OLD_FILENAME', help="old file name")
    parser.add_argument('NEW_FILENAME', help="new file name")
    args = parser.parse_args(args)

    old_name, new_name = os.path.relpath(args.OLD_FILENAME), os.path.relpath(args.NEW_FILENAME)

    config = FragmentsConfig()
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
        config['files'][new_key] = config['files'][old_key]
        del config['files'][old_key]
        if os.access(old_path, os.W_OK|os.R_OK):
            os.rename(old_path, new_path)
    config.dump()


def diff(*args):
    """Show differences between committed and uncommitted versions, limited to FILENAME(s) if specified."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, diff.__name__), description=diff.__doc__)
    parser.add_argument('FILENAME', help="file(s) to show changes in", nargs="*")
    parser.add_argument('-U', '--unified', type=int, dest="NUM", default=3, action="store", help="number of lines of context to show")
    args = parser.parse_args(args)

    config = FragmentsConfig()

    for curr_path in _iterate_over_files(args.FILENAME, config):
        key = os.path.relpath(curr_path, config.root)
        if key not in config['files']:
            yield "Could not diff '%s', it is not being followed" % os.path.relpath(curr_path)
            continue

        s = _file_status(config, curr_path)
        if s in 'MAD':
            repo_lines = []
            curr_lines = []
            if s in 'MA':
                curr_lines = _smart_open(curr_path, 'r').readlines()
            if s in 'MD':
                repo_lines = _smart_open(os.path.join(config.directory, config['files'][key]), 'r').readlines()
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
    parser.add_argument('FILENAME', help="file(s) to commit", nargs="*")
    args = parser.parse_args(args)

    config = FragmentsConfig()

    for curr_path in _iterate_over_files(args.FILENAME, config):
        key = os.path.relpath(curr_path, config.root)
        if key not in config['files']:
            yield "Could not commit '%s' because it is not being followed" % os.path.relpath(curr_path)
            continue

        s = _file_status(config, curr_path)
        if s in 'MA':
            repo_path = os.path.join(config.directory, config['files'][key])
            with _smart_open(repo_path, 'w') as repo_file:
                repo_file.write(_smart_open(curr_path, 'r').read())
            os.utime(repo_path, os.stat(curr_path)[7:9])
            yield "'%s' committed" % os.path.relpath(curr_path)
        elif s == 'D':
            yield "Could not commit '%s' because it has been removed, instead revert or forget it" % os.path.relpath(curr_path)
        elif s == ' ':
            yield "Could not commit '%s' because it has not been changed" % os.path.relpath(curr_path)


def revert(*args):
    """Revert changes to the fragments repository, limited to FILENAME(s) if specified."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, revert.__name__), description=revert.__doc__)
    parser.add_argument('FILENAME', help="file(s) to revert", nargs="*")
    args = parser.parse_args(args)

    config = FragmentsConfig()

    for curr_path in _iterate_over_files(args.FILENAME, config):
        key = os.path.relpath(curr_path, config.root)
        if key not in config['files']:
            yield "Could not revert '%s' because it is not being followed" % os.path.relpath(curr_path)
            continue

        s = _file_status(config, curr_path)
        if s in 'MD':
            repo_path = os.path.join(config.directory,  config['files'][key])
            with _smart_open(curr_path, 'w') as curr_file:
                curr_file.write(_smart_open(repo_path, 'r').read())
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
    for old_name in args.SOURCE_FILENAME:
        old_path = os.path.realpath(old_name)
        old_key = os.path.relpath(old_path, config.root)
        if os.access(old_path, os.R_OK|os.W_OK):
            old_filenames.append(old_path)
            if old_key not in config['files']:
                yield "Warning, '%s' not being followed" % os.path.relpath(old_path)
        else:
            yield "Skipping '%s' while forking, it does not exist" % os.path.relpath(old_path)

    if not old_filenames:
        yield "Could not fork; no valid source files specified"
        return

    weave = Weave()

    new_lines = _smart_open(old_filenames[0], 'r').readlines()
    previous_revision = 1
    weave.add_revision(previous_revision, new_lines, [])
    for old_name in old_filenames[1:]:
        current_revision = previous_revision + 1
        weave.add_revision(current_revision, _smart_open(old_name, 'r').readlines(), [])
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


try:
    raw_input
except NameError: # pragma: no cover # Python 3 support
    raw_input = input

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
                        response = raw_input(l)
                        l = command_generator.send(response.strip())
                    print(str(l))
                except StopIteration:
                    break
        except FragmentsError as exc:
            sys.exit(exc.args[0])
        except KeyboardInterrupt:
            pass

__all__ = ['help', 'init', 'status', 'follow', 'forget', 'rename', 'diff', 'commit', 'revert', 'fork', 'apply']
