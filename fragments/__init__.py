import os

__version__ = (0,0,3)

class FragmentsError(Exception): pass

def _iterate_over_files(args, config):
    if args:
        return (os.path.realpath(a) for a in set(args))
    else:
        return sorted(os.path.join(config.root, f) for f in config['files'])
