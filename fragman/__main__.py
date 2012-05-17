import sys, os, uuid, difflib
import pdb

from fragman import __version__, FragmanError
from fragman.config import FragmanConfig, configuration_directory_name, find_configuration, ConfigurationFileCorrupt, ConfigurationFileNotFound, ConfigurationDirectoryNotFound
from fragman.apply import apply_changes

class ExecutionError(FragmanError): pass

def help(*a):
    """Prints help."""
    yield "help!"


def init(*a):
    """Initialize a fragments repository."""
    try:
        config = FragmanConfig()
    except ConfigurationFileCorrupt, exc:
        config = FragmanConfig(autoload=False)
        os.rename(config.path, config.path + '.corrupt')
        config.dump()
    except ConfigurationFileNotFound, exc:
        config = FragmanConfig(autoload=False)
        config.dump()
    except ConfigurationDirectoryNotFound, exc:
        configuration_parent = os.path.split(os.getcwd())[0]
        if os.access(configuration_parent, os.R_OK|os.W_OK):
            configuration_path = os.path.join(configuration_parent, configuration_directory_name)
            os.mkdir(configuration_path)
            config = FragmanConfig(configuration_path, autoload=False)
            config.dump()
        else:
            raise ExecutionError("Could not create fragments directory in %r, aborting.\n(Do you have the correct permissions?)" % configuration_parent)
    else:
        raise ExecutionError("Current fragments configuration found in %r, aborting." % config.path)
    yield "Fragments configuration created in %r" % config.path


def stat(*a):
    """Get status of a fragments repository."""
    config = FragmanConfig()
    yield repr(config)


def follow(*args):
    """Add files to fragments following."""
    config = FragmanConfig()
    random_uuid = uuid.uuid4()
    for filename in set(args):
        fullpath = os.path.realpath(filename)
        if fullpath.startswith(config.root):
            key = fullpath[len(config.root)+1:]
            if key in config['files']:
                yield "%r is already being followed" % filename
                continue
            if os.access(fullpath, os.W_OK|os.R_OK):
                file_uuid = uuid.uuid5(random_uuid, key)
                config['files'][key] = file_uuid
                yield "%r is now being followed, UUID %r" % (filename, file_uuid)
            else:
                yield "Could not access %r to follow it" % filename
        else:
            yield "Could not follow %r; it is outside the repository" % filename
    config.dump()


def forget(*args):
    """Remove files from fragments following"""
    config = FragmanConfig()
    for filename in set(args):
        fullpath = os.path.realpath(filename)
        if fullpath.startswith(config.root):
            key = fullpath[len(config.root)+1:]
            if key in config['files']:
                file_uuid = config['files'][key]
                uuid_path = os.path.join(config.directory, file_uuid)
                if os.access(os.path.join(config.directory, file_uuid), os.W_OK|os.R_OK):
                    os.unlink(uuid_path)
                    yield "%r is no longer being followed" % filename
                else:
                    yield "%r was never committed and will not be followed" % filename
                del config['files'][key]
            else:
                yield "Could not forget %r, it was not being followed" % filename
        else:
            yield "Could not forget %r; it is outside the repository" % filename
    config.dump()


def _iterate_over_files(args, config):
    if args:
        return (os.path.realpath(a) for a in set(args))
    else:
        return (os.path.join(config.root, f) for f in config['files'])


def diff(*args):
    """Show differences between committed and uncommitted versions"""
    config = FragmanConfig()

    for curr_path in _iterate_over_files(args, config):
        key = curr_path[len(config.root)+1:]
        if key not in config['files']:
            yield "Could not diff %r, it is not being followed" % key
            continue

        uuid = config['files'][key]
        repo_path = os.path.join(config.directory, uuid)

        if os.access(repo_path, os.R_OK|os.W_OK):
            repo_mtime = os.stat(repo_path)[8]
            repo_lines = file(repo_path, 'r').readlines()
        else:
            repo_mtime = -1 # diffing an uncommitted file
            repo_lines = []

        if os.access(curr_path, os.R_OK|os.W_OK):
            curr_mtime = os.stat(curr_path)[8]
            curr_lines = file(curr_path, 'r').readlines()
        else:
            curr_mtime = float('+Inf') # trying to diff a file that's been removed
            curr_lines =[]

        if repo_mtime < curr_mtime:
            for dl in difflib.unified_diff(repo_lines, curr_lines, fromfile=key, tofile=key):
                yield dl


def commit(*args):
    """Commit changes to fragments repository"""
    config = FragmanConfig()

    for curr_path in _iterate_over_files(args, config):
        key = curr_path[len(config.root)+1:]
        if key not in config['files']:
            yield "Could not commit %r because it is not being followed" % key
            continue
        uuid = config['files'][key]

        repo_path = os.path.join(config.directory, uuid)
        if os.access(repo_path, os.R_OK|os.W_OK):
            repo_mtime = os.stat(repo_path)[8]
        else:
            repo_mtime = -1 # committing a file for the first time

        if os.access(curr_path, os.R_OK|os.W_OK):
            curr_atime, curr_mtime = os.stat(curr_path)[7:9]
        else:
            yield "Could not commit %r because it has been removed, try reverting it first" % key
            continue

        if repo_mtime < curr_mtime:
            repo_file = file(repo_path, 'w')
            repo_file.write(file(curr_path, 'r').read())
            repo_file.close()
            os.utime(repo_path, (curr_atime, curr_mtime))
            yield "%r committed"


def revert(*args):
    """Revert changes to fragments repository"""
    config = FragmanConfig()

    for curr_path in _iterate_over_files(args, config):
        key = curr_path[len(config.root)+1:]
        if key not in config['files']:
            yield "Could not revert %r because it is not being followed" % key
            continue
        uuid = config['files'][key]

        repo_path = os.path.join(config.directory, uuid)
        if os.access(repo_path, os.R_OK|os.W_OK):
            repo_atime, repo_mtime = os.stat(repo_path)[7:9]
        else:
            yield "Could not revert %r because it has never been committed" % key
            continue

        if os.access(curr_path, os.R_OK|os.W_OK):
            curr_atime, curr_mtime = os.stat(curr_path)[7:9]
        else:
            curr_mtime = float('+Inf') # trying to revert a file that's been removed

        if repo_mtime < curr_mtime:
            curr_file = file(curr_path, 'w')
            curr_file.write(file(repo_path, 'r').read())
            curr_file.close()
            os.utime(curr_path, (repo_atime, repo_mtime))
            yield "%r reverted" % key


def apply(*args):
    """Revert changes to fragments repository"""
    config = FragmanConfig()

    for path in _iterate_over_files(args, config):
        for q in apply_changes(path, config):
            yield q


if __name__ == '__main__': # pragma: no cover
    print "%s version %s.%s.%s" % ((__package__,) + __version__)
    if len(sys.argv) > 1 and sys.argv[1][0] != '_':
        try:
            cmd = locals()[sys.argv[1]]
        except KeyError, exc:
            print(help())
        except ExecutionError, exc:
            sys.exit(exc.message)
        else:
            if callable(cmd):
                for l in cmd(sys.argv[2:]):
                    print(l)
            else:
                print(help())
    else:
        print(help())
