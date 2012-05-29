import os
import sys
import uuid
import argparse
#import difflib

from . import __version__, FragmentsError, Prompt, _iterate_over_files
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
    """Initialize a new fragments repository, in a directory named _fragments/."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, init.__name__), description=init.__doc__)
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


def _file_stat(config, curr_path):
    key = curr_path[len(config.root)+1:]
    if key not in config['files']:
        return '?' # unfollowed

    repo_path = os.path.join(config.directory, config['files'][key])

    repo_exists = os.access(repo_path, os.R_OK|os.W_OK)
    curr_exists = os.access(curr_path, os.R_OK|os.W_OK)

    if repo_exists and curr_exists:
        repo_mtime = os.stat(repo_path)[8]
        curr_mtime = os.stat(curr_path)[8]
        if curr_mtime > repo_mtime:
            return 'M' # modified
        else:
            return ' ' # unmodified
    elif repo_exists:
        return 'D' # deleted
    elif curr_exists:
        return 'A' # added
    else:
        return 'E' # error. this should never happen - both files on disk are missing, but file is being followed


def stat(*args):
    """Get the current status of the fragments repository, limited to FILENAME(s) if specified."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, stat.__name__), description=stat.__doc__)
    parser.add_argument('FILENAME', help="files to show status for", nargs="*")
    args = parser.parse_args(args)

    config = FragmentsConfig()
    yield "%s configuration version %s.%s.%s" % ((__package__,) + config['version'])
    yield "stored in %s" % config.directory
    for curr_path in _iterate_over_files(args.FILENAME, config):
        yield '%s\t%s' % (_file_stat(config, curr_path), os.path.relpath(curr_path))


def follow(*args):
    """Start following changes to one or more FILENAME(s)."""
    parser = argparse.ArgumentParser(prog="%s %s" % (__package__, follow.__name__), description=follow.__doc__)
    parser.add_argument('FILENAME', help="files to follow", nargs="+")
    args = parser.parse_args(args)

    config = FragmentsConfig()
    random_uuid = uuid.uuid4()
    for filename in set(args.FILENAME):
        fullpath = os.path.realpath(filename)
        if fullpath.startswith(config.root):
            key = os.path.relpath(fullpath, config.root)
            if key in config['files']:
                yield "'%s' is already being followed" % os.path.relpath(filename)
                continue
            if os.access(fullpath, os.W_OK|os.R_OK):
                file_uuid = uuid.uuid5(random_uuid, key)
                config['files'][key] = file_uuid
                yield "'%s' is now being followed, UUID %s" % (os.path.relpath(filename), file_uuid)
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
                file_uuid = config['files'][key]
                uuid_path = os.path.join(config.directory, file_uuid)
                if os.access(os.path.join(config.directory, file_uuid), os.W_OK|os.R_OK):
                    os.unlink(uuid_path)
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

        s = _file_stat(config, curr_path)
        if s in 'MAD':
            repo_lines = []
            curr_lines = []
            if s in 'MA':
                curr_lines = open(curr_path, 'r').readlines()
            if s in 'MD':
                repo_lines = open(os.path.join(config.directory, config['files'][key]), 'r').readlines()
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

        s = _file_stat(config, curr_path)
        if s in 'MA':
            repo_path = os.path.join(config.directory, config['files'][key])
            with file(repo_path, 'w') as repo_file:
                repo_file.write(open(curr_path, 'r').read())
            os.utime(repo_path, os.stat(curr_path)[7:9])
            yield "'%s' committed" % os.path.relpath(curr_path)
        elif s in 'D':
            yield "Could not commit '%s' because it has been removed, instead revert or forget it" % os.path.relpath(curr_path)


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

        s = _file_stat(config, curr_path)
        if s in 'MD':
            repo_path = os.path.join(config.directory,  config['files'][key])
            with file(curr_path, 'w') as curr_file:
                curr_file.write(open(repo_path, 'r').read())
            os.utime(curr_path, os.stat(repo_path)[7:9])
            yield "'%s' reverted" % key
        elif s in 'A':
            yield "Could not revert '%s' because it has never been committed" % os.path.relpath(curr_path)


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

    new_lines = open(old_filenames[0], 'r').readlines()
    previous_revision = 1
    weave.add_revision(previous_revision, new_lines, [])
    for old_name in old_filenames[1:]:
        current_revision = previous_revision + 1
        weave.add_revision(current_revision, open(old_name, 'r').readlines(), [])
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

    with file(new_path, 'w') as new_file:
        new_file.writelines(new_lines)
    yield "Forked new file in '%s', remember to follow and commit it" % os.path.relpath(args.TARGET_FILENAME)
    config.dump()


def _main(): # pragma: no cover
    from . import commands
    print("%s version %s.%s.%s" % ((__package__,) + __version__))
    if (sys.argv[1] in __all__): # command is legit
        try:
            command_generator = getattr(commands, sys.argv[1])(*sys.argv[2:])
            while True:
                try:
                    l = next(command_generator)
                    if isinstance(l, Prompt):
                        response = raw_input(color.colorize(l, color=color.YELLOW)  + ' ')
                        l = command_generator.send(response.strip())
                    print(color.colorize(l))
                except StopIteration:
                    break
        except ExecutionError as exc:
            sys.exit(exc.message)
    else:
        for l in help():
            print(l)


__all__ = ['help', 'init', 'stat', 'follow', 'forget', 'rename', 'diff', 'commit', 'revert', 'fork', 'apply']
