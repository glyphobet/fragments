import sys, os, uuid, difflib
import pdb

from . import __version__, FragmentsError
from .config import FragmentsConfig, configuration_directory_name, find_configuration, ConfigurationFileCorrupt, ConfigurationFileNotFound, ConfigurationDirectoryNotFound
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
    except ConfigurationFileCorrupt, exc:
        config = FragmentsConfig(autoload=False)
        os.rename(config.path, config.path + '.corrupt')
        config.dump()
    except ConfigurationFileNotFound, exc:
        config = FragmentsConfig(autoload=False)
        config.dump()
    except ConfigurationDirectoryNotFound, exc:
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


def stat(*a):
    """Get status of a fragments repository."""
    config = FragmentsConfig()
    yield repr(config)


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
                yield "%r is now being followed, UUID %r" % (filename, file_uuid)
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


def _iterate_over_files(args, config):
    if args:
        return (os.path.realpath(a) for a in set(args))
    else:
        return (os.path.join(config.root, f) for f in config['files'])


def _visible_in_diff(merge_result, context_lines=3):
    """Collects the set of lines that should be visible in a diff with a certain number of context lines"""
    i = old_line = new_line = 0
    while i < len(merge_result):
        line_or_tuple = merge_result[i]
        if isinstance(line_or_tuple, tuple):
            yield old_line, new_line, line_or_tuple
            old_line += len(line_or_tuple[0])
            new_line += len(line_or_tuple[1])
        else:
            should_yield = False
            for ibefore in range(max(0, i-context_lines), i): # look behind
                if isinstance(merge_result[ibefore], tuple):
                    should_yield = True
                    break
            for iafter in range(i+1, min(len(merge_result), i+1+context_lines)): # look ahead
                if isinstance(merge_result[iafter], tuple):
                    should_yield = True
                    break
            if should_yield:
                yield old_line, new_line, line_or_tuple
            else:
                yield None
            old_line += 1
            new_line += 1
        i += 1
    yield None


def _split_diff(merge_result, context_lines=3):
    """Split diffs and context lines into groups based on None sentinel"""
    collect = []
    for item in _visible_in_diff(merge_result, context_lines=context_lines):
        if item is None:
            if collect:
                yield collect
            collect = []
        else:
            collect.append(item)


def _diff_group_position(group):
    """Generate a unified diff position line for a diff group"""
    old_start = group[0][0]
    new_start = group[0][1]
    old_length = new_length = 0
    for old_line, new_line, line_or_tuple in group:
        if isinstance(line_or_tuple, tuple):
            old, new = line_or_tuple
            old_length += len(old)
            new_length += len(new)
        else:
            old_length += 1
            new_length += 1
    if old_length:
        old_start += 1
    if new_length:
        new_start += 1

    return '@@ -%s,%s +%s,%s @@\n' % (old_start, old_length, new_start, new_length)


def _diff_group(group):
    """Generate a diff section for diff group"""
    yield _diff_group_position(group)

    for old_line, new_line, line_or_tuple in group:
        if isinstance(line_or_tuple, tuple):
            old, new = line_or_tuple
            for o in old:
                yield '-' + o
            for n in new:
                yield '+' + n
        else:
            yield ' ' + line_or_tuple


def _full_diff(merge_result, key, context_lines=3):
    """Generate a full diff based on a Weave merge result"""
    header_printed = False
    for group in _split_diff(merge_result, context_lines=context_lines):
        if not header_printed:
            header_printed = True
            yield '--- %s\n' % key
            yield '+++ %s\n' % key

        for l in _diff_group(group):
            yield l


def diff(*args):
    """Show differences between committed and uncommitted versions"""
    config = FragmentsConfig()
    context_line_count = 3 # TODO: specify with -U N, --unified N

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
        uuid = config['files'][key]

        repo_path = os.path.join(config.directory, uuid)
        if os.access(repo_path, os.R_OK|os.W_OK):
            repo_mtime = os.stat(repo_path)[8]
        else:
            repo_mtime = -1 # committing a file for the first time

        if os.access(curr_path, os.R_OK|os.W_OK):
            curr_atime, curr_mtime = os.stat(curr_path)[7:9]
        else:
            yield "Could not commit %r because it has been removed, instead revert or remove it" % key
            continue

        if repo_mtime < curr_mtime:
            repo_file = file(repo_path, 'w')
            repo_file.write(file(curr_path, 'r').read())
            repo_file.close()
            os.utime(repo_path, (curr_atime, curr_mtime))
            yield "%r committed"


def revert(*args):
    """Revert changes to fragments repository"""
    config = FragmentsConfig()

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


def _main(): # pragma: no cover
    print "%s version %s.%s.%s" % ((__package__,) + __version__)
    if (len(sys.argv) > 1              and  # command was specified
        sys.argv[1][0] != '_'          and  # command does not start with _
        sys.argv[1] in locals()        and  # command exists in namespace
        callable(locals()[sys.argv[1]]) ):  # command is callable
        try:
            for l in cmd(sys.argv[2:]):
                print(l)
        except ExecutionError, exc:
            sys.exit(exc.message)
    else:
        for l in help():
            print l
