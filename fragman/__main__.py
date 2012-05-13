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


def add(*args): # Also could be called track
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
