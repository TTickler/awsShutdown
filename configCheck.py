import json
import sys
import jsonschema

__author__ = "Colby Dozier"
__license__ = ""
__version__ = "1"
__maintainer__ = "Colby Dozier"
__email__ = "colby.dozier@caci.com"
__status__ = "Development"

class ConfigCheck():
    def __init__(self):
        with open(sys.path[0] + '/config.json') as configRaw:
            self.__config = json.load(configRaw)

        with open(sys.path[0] + '/configSchema.json') as schemaRaw:
            self.__schema = json.load(schemaRaw)


    def validateConfig(self):
        v = jsonschema.Draft4Validator(self.__schema)
        errors = sorted(v.iter_errors(self.__config), key=lambda e: e.path)

        return errors

