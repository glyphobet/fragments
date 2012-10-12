# -*- coding: utf-8
from __future__ import unicode_literals

import os
import codecs

__version__ = (1,2,2)

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

def _smart_open(path, mode='r'):
    return codecs.open(path, mode=mode, encoding='utf8')
