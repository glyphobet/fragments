import os, sys, json
from . import FragmanError

configuration_file_name = 'config.json'
configuration_directory_name = 'fragments'


class ConfigurationError(FragmanError): pass
class ConfigurationDirectoryNotFound(ConfigurationError): pass
class ConfigurationFileNotFound(ConfigurationError): pass
class ConfigurationFileCorrupt(ConfigurationError): pass


def find_configuration(current=None):
    current = current or os.getcwd()
    path = current
    while True:
        configuration_path = os.path.join(path, configuration_directory_name)
        if os.path.exists(path) and os.path.exists(configuration_path):
            return configuration_path
        path, oldpath = os.path.split(path)[0], path
        if oldpath == path:
            raise ConfigurationDirectoryNotFound("Could not find fragments configuration directory in %r or any parent directories" % current)


class FragmanConfig(dict):

    defaults = {
        'files': (),
    }

    def __init__(self, directory=None, autoload=True):
        if directory is None:
            directory = find_configuration()
        self.path = os.path.join(directory, configuration_file_name)
        self.update(FragmanConfig.defaults)
        if autoload:
            self.load()

    def load(self):
        if os.access(self.path, os.R_OK|os.W_OK):
            file_contents = open(self.path, 'r').read()
            parsed_json = json.loads(file_contents)
            self.update(parsed_json)
        else:
            raise ConfigurationFileNotFound("Could not access %r, if the file exists, check its permissions" % self.path)

    def dump(self):
        file(self.path, 'w').write(json.dumps(self, sort_keys=True, indent=4))
