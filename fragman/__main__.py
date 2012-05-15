import sys, os, uuid
import pdb

from fragman import __version__, FragmanError
from fragman.config import FragmanConfig, configuration_directory_name, find_configuration, ConfigurationFileCorrupt, ConfigurationFileNotFound, ConfigurationDirectoryNotFound

class ExecutionError(FragmanError): pass

def help(*a):
    """Prints help."""
    return "help!"


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
    return "Fragments configuration created in %r" % config.path


def stat(*a):
    """Get status of a fragments repository."""
    config = FragmanConfig()
    return repr(config)


def track(*args):
    """Add files to fragments tracking."""
    config = FragmanConfig()
    prefix = os.path.split(config.directory)[0]
    random_uuid = uuid.uuid4()
    for filename in set(args):
        fullpath = os.path.join(os.getcwd(), filename)
        if fullpath.startswith(prefix):
            if os.access(fullpath, os.W_OK|os.R_OK):
                file_path = fullpath[len(prefix)+1:]
                if file_path in config['files']:
                    # file already tracked
                    continue
                file_uuid = uuid.uuid5(random_uuid, file_path)
                config['files'][file_path] = file_uuid
    config.dump()


def forget(*args):
    """Remove files from fragments tracking"""
    config = FragmanConfig()
    prefix = os.path.split(config.directory)[0]
    for filename in set(args):
        fullpath = os.path.realpath(filename)
        if fullpath.startswith(prefix):
            key = fullpath[len(prefix)+1:]
            if key in config['files']:
                uuid = config['files'][key]
                os.unlink(os.path.join(config.directory, uuid))
                del config['files'][key]
            else:
                pass # trying to forget an untracked file
        else:
            pass # trying to forget a file outside the repository
    config.dump()


def commit(*args):
    """Commit changes to fragments repository"""
    config = FragmanConfig()
    prefix = os.path.split(config.directory)[0]
    cwd = os.getcwd()

    if args:
        iterate = (os.path.join(cwd, a) for a in args)
    else:
        iterate = (os.path.join(prefix, f) for f in config['files'])

    for curr_path in iterate:
        key = curr_path[len(prefix)+1:]
        if key not in config['files']:
            continue # trying to commit an untracked file
        uuid = config['files'][key]

        repo_path = os.path.join(config.directory, uuid)
        if os.access(repo_path, os.R_OK|os.W_OK):
            repo_mtime = os.stat(repo_path)[8]
        else:
            repo_mtime = -1 # committing a file for the first time

        if os.access(curr_path, os.R_OK|os.W_OK):
            curr_atime, curr_mtime = os.stat(curr_path)[7:9]
        else:
            continue # trying to commit a nonexistent file

        if repo_mtime < curr_mtime:
            repo_file = file(repo_path, 'w')
            repo_file.write(file(curr_path, 'r').read())
            repo_file.close()
            os.utime(repo_path, (curr_atime, curr_mtime))


if __name__ == '__main__':
    print "%s version %s.%s.%s" % ((__package__,) + __version__)
    if len(sys.argv) > 1:
        try:
            cmd = locals()[sys.argv[1]]
        except KeyError, exc:
            print(help())
        except ExecutionError, exc:
            sys.exit(exc.message)
        else:
            if callable(cmd):
                print(cmd(sys.argv[2:]))
            else:
                print(help())
    else:
        print(help())
