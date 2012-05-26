import sys, os, uuid, difflib
import pdb

from . import __version__, FragmentsError, Prompt
from .config import FragmentsConfig, configuration_directory_name, find_configuration, ConfigurationFileCorrupt, ConfigurationFileNotFound, ConfigurationDirectoryNotFound
from .diff import _full_diff
from .apply import apply
from .precisecodevillemerge import Weave


class ExecutionError(FragmentsError): pass

def help(*a):
    """Prints help."""
    yield "help!"


def init(*a):
    """Initialize a fragments repository."""
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
            raise ExecutionError("Could not create fragments directory in %r, aborting.\n(Do you have the correct permissions?)" % configuration_parent)
    else:
        raise ExecutionError("Current fragments configuration found in %r, aborting." % config.path)
    yield "Fragments configuration created in %r" % config.path


def _iterate_over_files(args, config):
    if args:
        return (os.path.realpath(a) for a in set(args))
    else:
        return (os.path.join(config.root, f) for f in config['files'])


def _file_stat(config, curr_path):
    key = curr_path[len(config.root)+1:]
    if key not in config['files']:
        return '?' # unfollowed

    uuid = config['files'][key]
    repo_path = os.path.join(config.directory, uuid)

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
    """Get status of a fragments repository."""
    config = FragmentsConfig()
    yield "%s configuration version %s.%s.%s" % ((__package__,) + config['version'])
    yield "stored in %s" % config.directory
    for curr_path in _iterate_over_files(args, config):
        yield '%s\t%s' % (_file_stat(config, curr_path), curr_path[len(config.root)+1:])


def follow(*args):
    """Add files to fragments following."""
    config = FragmentsConfig()
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
                yield "%r is now being followed, UUID %s" % (filename, file_uuid)
            else:
                yield "Could not access %r to follow it" % filename
        else:
            yield "Could not follow %r; it is outside the repository" % filename
    config.dump()


def forget(*args):
    """Remove files from fragments following"""
    config = FragmentsConfig()
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


def rename(old_name, new_name):
    """Rename one file to another"""
    config = FragmentsConfig()
    old_path = os.path.realpath(old_name)
    old_key = old_path[len(config.root)+1:]
    new_path = os.path.realpath(new_name)
    new_key = new_path[len(config.root)+1:]
    if old_key not in config['files']:
        yield "Could not rename %r, it is not being tracked" % old_name
    elif new_key in config['files']:
        yield "Could not rename %r to %r, %r is already being tracked" % (old_name, new_name, new_name)
    elif os.access(old_path, os.W_OK|os.R_OK) and os.access(new_path, os.W_OK|os.R_OK):
        yield "Could not rename %r to %r, both files already exist" % (old_name, new_name)
    elif not os.access(old_path, os.W_OK|os.R_OK) and not os.access(new_path, os.W_OK|os.R_OK):
        yield "Could not rename %r to %r, neither file exists" % (old_name, new_name)
    else:
        config['files'][new_key] = config['files'][old_key]
        del config['files'][old_key]
        if os.access(old_path, os.W_OK|os.R_OK):
            os.rename(old_path, new_path)
    config.dump()


def diff(*args):
    """Show differences between committed and uncommitted versions"""
    config = FragmentsConfig()
    context_line_count = 3 # TODO: specify with -U N, --unified N

    for curr_path in _iterate_over_files(args, config):
        key = curr_path[len(config.root)+1:]
        if key not in config['files']:
            yield "Could not diff %r, it is not being followed" % key
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
            for l in _full_diff(weave.merge(1, 2), key, context_lines=3):
                yield l
            # for dl in difflib.unified_diff(repo_lines, curr_lines, fromfile=key, tofile=key):
            #     yield dl


def commit(*args):
    """Commit changes to fragments repository"""
    config = FragmentsConfig()

    for curr_path in _iterate_over_files(args, config):
        key = curr_path[len(config.root)+1:]
        if key not in config['files']:
            yield "Could not commit %r because it is not being followed" % key
            continue

        s = _file_stat(config, curr_path)
        if s in 'MA':
            repo_path = os.path.join(config.directory, config['files'][key])
            repo_file = file(repo_path, 'w')
            repo_file.write(file(curr_path, 'r').read())
            repo_file.close()
            os.utime(repo_path, os.stat(curr_path)[7:9])
            yield "%r committed" % key
        elif s in 'D':
            yield "Could not commit %r because it has been removed, instead revert or remove it" % key


def revert(*args):
    """Revert changes to fragments repository"""
    config = FragmentsConfig()

    for curr_path in _iterate_over_files(args, config):
        key = curr_path[len(config.root)+1:]
        if key not in config['files']:
            yield "Could not revert %r because it is not being followed" % key
            continue

        s = _file_stat(config, curr_path)
        if s in 'MD':
            repo_path = os.path.join(config.directory,  config['files'][key])
            curr_file = file(curr_path, 'w')
            curr_file.write(file(repo_path, 'r').read())
            curr_file.close()
            os.utime(curr_path, os.stat(repo_path)[7:9])
            yield "%r reverted" % key
        elif s in 'A':
            yield "Could not revert %r because it has never been committed" % key


def _main(): # pragma: no cover
    from . import commands
    print("%s version %s.%s.%s" % ((__package__,) + __version__))
    if (len(sys.argv) > 1              and  # command was specified
        sys.argv[1][0] != '_'          and  # command does not start with _
        sys.argv[1] in dir(commands)   and  # command exists in commands module
        callable(getattr(commands, sys.argv[1]))):  # command is callable
        try:
            command_generator = getattr(commands, sys.argv[1])(*sys.argv[2:])
            while True:
                try:
                    l = next(command_generator)
                    if isinstance(l, Prompt):
                        response = raw_input(l + ' ')
                        l = command_generator.send(response.strip())
                    print(l)
                except StopIteration:
                    break
        except ExecutionError as exc:
            sys.exit(exc.message)
    else:
        for l in help():
            print(l)
