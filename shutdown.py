import json
import awsSdk
import subprocess
import sys
import importlib
import string
import pprint
from difflib import SequenceMatcher

class Shutdown():
    def __init__(self):

        with open(sys.path[0] + '/config.json') as configRaw:
            self.config = json.load(configRaw)

        self.names = []

    @property
    def environment(self):
        return self._environment

    @environment.setter
    def environment(self, environment):
        self._environment = environment

    '''Function to leverage AWS CLI to shut down RDS instance'''
    def shutdownRds(self, instanceId, region):
        return json.loads(subprocess.check_output('aws rds stop-db-instance --db-instance-identifier {} --region {}'.format(instanceId, region), shell=True))

    '''Function to leverage AWS CLI to shut down EC2 instances'''
    def shutdownEc2(self, instanceId, region):
        return json.loads(subprocess.check_output('aws ec2 stop-instances --instance-ids {} --region {}'.format(instanceId, region), shell=True))

    def checkTagExists(self, tags, key, value):
        try:
            return tags[key] == value
        except KeyError:
            return False

    def updateNamedInstances(self, name):
        self.names.append(name)

    def shutdown(self, resource, resourceType, region):


        '''Sets Management information, used later, to None to avoid referencing variables without it being instantiated'''
        managementAmiRegion = None
        managementInstanceId = None
        nameTags = []
        if resourceType == "EC2":

            try:
                for tag in resource['tags']:
                    #if self.checkTagExists()
                    # if current resource is the management AMI, save instance information for future shut down
                    # and skip shutting it down
                    if tag['Key'] == "Name" and tag['Value'] == self.config['scriptHost']:
                        managementInstanceId = resource['instanceId']
                        managementAmiRegion = region
                        continue

                    if tag['Key'] == "Name":
                        self.updateNamedInstances(tag['Value'])

                    elif tag['Key'] == self.config['shutdownKey'] and tag['Value'] != 'false':
                        self.shutdownEc2(resource["instanceId"], region)

            except:
                raise
                #print("None iterable item skipped. No key \"tags\"")

        if resourceType == "RDS":
            self.shutdownRds(resource["Name"], region)

        if managementAmiRegion is not None:
            return {"managementInstanceId": managementInstanceId, "managementAmiRegion": managementAmiRegion}
        else:
            return None



    def shutdownManagement(self, managementInstanceId, managementAmiRegion):
        try:
            shutdown.shutdownEc2(managementInstanceId, managementAmiRegion)

        except:
            print(
                "Management server is not running or tags for management server is not correct. If this is running on the management "
                "AMI, the tags are incorrect.")


#class TestEnvironment():
 #   def __init__(self, config):
  #      self.test = 5

   # def run(self):

class Environment():
    def __init__(self):
        
        self.__scriptHost = None
        self.__asgAction = None
        self.__config = None

    @property
    def scriptHost(self):
        return self.__scriptHost

    @scriptHost.setter
    def scriptHost(self, scriptHost):
        self.__scriptHost = scriptHost

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, config):
        self.__config = config

    def setAsgAction(self):



class DevEnvironment():
    def __init__(self awsSdk):
        self.test = 5
        self.__awsSdk = awsSdk
        self.__config = config

        self.__shutdown = Shutdown()

    def run(self):
        activeResources = self.__awsSdk.getAllActiveResourcesNames()

        managementInfo = None

        for region in activeResources:
            for resourceType in activeResources[region]:
                for resource in activeResources[region][resourceType]:
                    shutdownOutput = self.__shutdown.shutdown(resource, resourceType, region)

                    if shutdownOutput is not None:
                        managementInfo = shutdownOutput
        pprint.pprint(self.__shutdown.names)

        if managementInfo is not None and self.__config['shutManagementDown'] == True:
            self.__shutdown.shutdownManagement(managementInfo['managementInstanceId'], managementInfo['managementAmiRegion'])

if __name__ == "__main__":

    allowedTestEnvironments = ['test']
    allowedDevEnvironments = ['dev', 'development']

    shutdown = Shutdown()
    awsSdk = awsSdk.awsManager()
    config = shutdown.config
    environment = string.lower(shutdown.config['environment'])

    awsSdk.regionList = shutdown.config['focusRegions']
    module = importlib.import_module("shutdown")

    if environment in allowedDevEnvironments:
        class_name = "DevEnvironment"

    elif environment in allowedTestEnvironments:
        class_name = "TestEnvironment"

    environmentClass = getattr(module, class_name, awsSdk)

    instance = environmentClass(config, awsSdk)
    instance.run()



