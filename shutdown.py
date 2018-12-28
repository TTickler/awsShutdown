import json
import awsSdk
import subprocess
import sys
import importlib
import string
import pprint
from difflib import SequenceMatcher

__author__ = "Colby Dozier"
__license__ = ""
__version__ = "1"
__maintainer__ = "Colby Dozier"
__email__ = "colby.dozier@caci.com"
__status__ = "Development"

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

    def suspendAsg(self, asgGroupName, region):
        try:
            subprocess.check_output('aws autoscaling suspend-processes --auto-scaling-group-name {} --region {}'.format(asgGroupName, region), shell=True)
        except:
            print("Failed to suspend ASG: {} in {}".format(asgGroupName, region))
    def terminateStack(self, stackName, region):
        try:
            subprocess.check_output('aws cloudformation delete-stack --stack-name {} --region {}'.format(stackName, region), shell=True)
        except:
            print("Failed to terminate stack: " + str(stackName))
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

        elif resourceType == "STACKS":
            for tag in resource['tags']:
                if tag['Key'] == self.config['shutdownKey'] and tag['Value'] != 'false':
                    if Environment.asgAction == 'terminate':
                        self.terminateStack(resource['Name'], region)

        elif resourceType == "ASG":
            for tag in resource['tags']:
                if tag['Key'] == self.config['shutdownKey'] and tag['Value'] != 'false':
                    if Environment.asgAction == 'suspend':
                        self.suspendAsg(resource['Name'], region)



        elif resourceType == "RDS":
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

''''''
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

    @property
    def asgAction(self):
        return self.__asgAction

    @asgAction.setter
    def asgAction(self, asgAction):
        self.__asgAction = asgAction


''''''
class DevEnvironment(Environment):
    def __init__(self, config,awsSdk):

        Environment.__init__(self)
        self.test = 5
        self.__awsSdk = awsSdk
        self.__config = config
        self.__shutdown = Shutdown()

    def run(self):
        activeResources = self.__awsSdk.getAllActiveResourcesNames()
        pprint.pprint(activeResources)

        managementInfo = None

        Environment.asgAction = self.__shutdown.config['environmentDetails']['asgAction']

        for region in activeResources:
            for resourceType in activeResources[region]:
                for resource in activeResources[region][resourceType]:
                    shutdownOutput = self.__shutdown.shutdown(resource, resourceType, region)

                    if shutdownOutput is not None:
                        managementInfo = shutdownOutput

        if managementInfo is not None and self.__config['shutManagementDown'] == True:
            self.__shutdown.shutdownManagement(managementInfo['managementInstanceId'], managementInfo['managementAmiRegion'])

''''''
#class TestEnvironment():
 #   def __init__(self, config):
  #      self.test = 5

   # def run(self):


#Main method of shutdown.py
if __name__ == "__main__":


    '''List of allowed environments. These are strings that 
        correlate to either the Test or Dev environment.'''
    allowedTestEnvironments = ['test']
    allowedDevEnvironments = ['dev', 'development']

    shutdown = Shutdown()
    awsSdk = awsSdk.awsManager()
    config = shutdown.config
    environment = string.lower(shutdown.config['environment'])

    awsSdk.regionList = shutdown.config['focusRegions']
    module = importlib.import_module("shutdown")

    shutdown.environment = environment

    if environment in allowedDevEnvironments:
        class_name = "DevEnvironment"

    elif environment in allowedTestEnvironments:
        class_name = "TestEnvironment"

    #creates object of either DevEnvironment or TestEnvironment based on configuration
    environmentClass = getattr(module, class_name, awsSdk)

    instance = environmentClass(config, awsSdk)


    instance.scriptHost = shutdown.config['scriptHost']

    #Sets the asgAction property equal to what populates the asgAction in the shutdown configuration
    instance.asgAction = shutdown.config['environmentDetails']['asgAction']

    instance.run()



