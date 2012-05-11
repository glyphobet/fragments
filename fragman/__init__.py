import os
__version__ = (0,0,1)

configuration_name = 'fragments'

class FragmanException(Exception): pass
class ConfigurationNotFound(FragmanException): pass


def find_configuration(current=None):
    path = current or os.getcwd()
    while True:
        configuration_path = os.path.join(path, configuration_name)
        if os.path.exists(path) and os.path.exists(configuration_path):
            return configuration_path
        path, oldpath = os.path.split(path)[0], path
        if oldpath == path:
            raise ConfigurationNotFound(current)
