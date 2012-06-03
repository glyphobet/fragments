import os

__version__ = (1,0,0)

class FragmentsError(Exception): pass

def _iterate_over_files(args, config):
    if args:
        seen = set()
        for a in args:
            if a not in seen:
                yield os.path.realpath(a)
                seen.add(a)
    else:
        for f in sorted(config['files']):
            yield os.path.join(config.root, f)
