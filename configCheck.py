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

        with 


    def hasValidFields(self):

