import os, sys, json

defaults = {
    'files': (),
}
name = 'config.json'

class FragmanConfig(dict):
    def __init__(self, directory):
        self.path = os.path.join(directory, name)
        self.update(defaults)
        if os.access(self.path, os.R_OK|os.W_OK):
            self.update(json.loads(open(self.path, 'r').read()))
        else:
            sys.exit("Could not access %r, check permissions" % self.path)

    def save(self):
        file(self.path, 'w').write(json.dumps(self, sort_keys=True, indent=4))
