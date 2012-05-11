import sys, os, pdb

from fragman import __version__, configuration_name, find_configuration, ConfigurationNotFound


def help(*a):
    """Prints help."""
    print("help!")


def init(*a):
    """Initialize a fragments repository."""
    try:
        configuration_path = find_configuration()
    except ConfigurationNotFound, exc:
        configuration_parent = os.path.split(os.getcwd())[0]
        if os.access(configuration_parent, os.R_OK|os.W_OK):
            configuration_path = os.path.join(configuration_parent, configuration_name)
            os.mkdir(configuration_path)
        else:
            sys.exit("Could not create fragments directory in %s, aborting.\n(Do you have the correct permissions?)" % configuration_parent)
    else:
        sys.exit("Current fragments directory found at %s, aborting." % configuration_path)


if __name__ == '__main__':
    print "%s version %s.%s.%s" % ((__package__,) + __version__)
    locals().get(sys.argv[1], help)(sys.argv[2:])

