import json
import sys
import jsonschema
import platform

__author__ = "Colby Dozier"
__license__ = ""
__version__ = "1"
__maintainer__ = "Colby Dozier"
__email__ = "colby.dozier@caci.com"
__status__ = "Development"

class ConfigCheck():
    def __init__(self):

        currPlatform = platform.system()

        with open(sys.path[0] + self.getConfigPath(currPlatform)) as configRaw:
            self.__config = json.load(configRaw)

        with open(sys.path[0] + self.getConfigSchemaPath(currPlatform)) as schemaRaw:
            self.__schema = json.load(schemaRaw)

    def getConfigPath(self, currPlatform):

        if currPlatform == 'Windows':
            return "\\config.json"
        elif currPlatform == 'Linux':
            return "/config.json"

    def getConfigSchemaPath(self, currPlatform):

        if currPlatform == 'Windows':
            return "\\configSchema.json"
        elif currPlatform == 'Linux':
            return "/configSchema.json"


    def validateConfig(self):
        v = jsonschema.Draft4Validator(self.__schema)
        errors = sorted(v.iter_errors(self.__config), key=lambda e: e.path)

        return errors

