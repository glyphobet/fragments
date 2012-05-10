import sys, os, pdb

from fragman import __version__, find_configuration, ConfigurationNotFound


def help(*a):
    print "help!"


def init(*a):
    find_configuration()


if __name__ == '__main__':
    print "%s version %s.%s.%s" % ((__package__,) + __version__)
    locals().get(sys.argv[1], help)(sys.argv[2:])

