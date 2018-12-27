import os, sys
import json
import pprint
import subprocess

__author__ = "Colby Dozier"
__license__ = ""
__version__ = "1"
__maintainer__ = "Colby Dozier"
__email__ = "colby.dozier@caci.com"
__status__ = "Development"

class awsManager():
    def __init__(self):
        self.__region_list = []
        self.__elb_query = "aws elb describe-tags --region <REGION> --load-balancer-names <ElbName>"

        self.__elb_version = 'elb'

    @property
    def regionList(self):
        return self.__region_list

    @regionList.setter
    def regionList(self, regionList):
        self.__region_list = regionList

    @property
    def elbVersion(self):
        return self.__elb_version

    @elbVersion.setter
    def elbVersion(self, elbVersion):
        self.__elb_version = elbVersion

    def queryElb(self, region="us-east-1", elbName=None):
        if region == None and elbName == None:
            return json.loads(subprocess.check_output(("aws {} describe-load-balancers").format(self.elbVersion), shell=True))

        elif region != None and elbName == None:
            return json.loads(subprocess.check_output(("aws {} describe-load-balancers --region {}").format(self.elbVersion, region), shell=True))

        elif elbName != None and region == None:
            return json.loads(subprocess.check_output(("aws {} describe-load-balancers --load-balancer-name {}").format(self.elbVersion, elbName), shell=True))

        else:
            return json.loads(subprocess.check_output(("aws {} describe-load-balancers --region {} --load-balancer-name {}").format(self.elbVersion, region, elbName), shell=True))


    def queryRds(self, region="us-east-1", dbName=None):


        if region == None and dbName == None:
            return json.loads(subprocess.check_output(("aws rds describe-db-instances"), shell=True))

        elif region != None and dbName == None:
            return json.loads(subprocess.check_output(("aws rds describe-db-instances --region {}").format(region), shell=True))

        elif dbName != None and region == None:
            return json.loads(subprocess.check_output(("aws rds describe-db-instances --db-instance-identifier {}").format(dbName),shell=True))

        else:
            return json.loads(subprocess.check_output(("aws rds describe-db-instances --region {} --db-instance-identifier {}").format(region, dbName),shell=True))


    def queryEc2(self, region="us-east-1", instanceId=None):

        if region == None and instanceId == None:
            return json.loads(subprocess.check_output("aws ec2 describe-instances", shell=True))

        elif region != None and instanceId == None:
            return json.loads(subprocess.check_output(("aws ec2 describe-instances --region {}").format(region), shell=True))

        elif instanceId != None and region == None:
            return json.loads(subprocess.check_output(("aws ec2 describe-instances --instance-id {}").format(instanceId), shell=True))

        else:
            return json.loads(subprocess.check_output(("aws ec2 describe-instances --region {}--instance-id {}").format(region, instanceId), shell=True))

    def listStacks(self, region):
        return json.loads(subprocess.check_output(("aws cloudformation list-stacks --region {}").format(region), shell=True))


    def describeStacks(self, region, stackName=None):

        if stackName is None:
            return json.loads(subprocess.check_output(("aws cloudformation describe-stacks --region {}").format(region), shell=True))

        else:
            return json.loads(subprocess.check_output(("aws cloudformation describe-stacks --stack-name {} --region {}").format(stackName, region), shell=True))


    def queryAsg(self, region,asgNames=None):

        if asgNames is None:
            return json.loads(subprocess.check_output(("aws autoscaling describe-auto-scaling-groups --region {}").format(region), shell=True))

        else:
            return json.loads(subprocess.check_output(("aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name {} --region {}").format(asgNames, region), shell=True))

    def getAllElbs(self):
    
        allElbsDict = {}       

        for region in self.__region_list:
            allElbsDict[region] = self.queryElb(region=region)

        return allElbsDict

    def getActiveResourcesByRegion(self, region):

        resources = {}

        resources['RDS'] = self.getActiveRDS(region)
        resources['EC2'] = self.getActiveEc2(region)
        resources['ELB'] = self.getElbsByRegion(region)

        return resources

    def getAllActiveResources(self):

        allResources = {}

        for region in self.regionList:
            allResources[region] = self.getActiveResourcesByRegion(region)

        return allResources

    def getAllActiveResourcesNames(self):

        allResourcesNames = {}

        for region in self.regionList:
            print(region)
            allResourcesNames[region] = self.getActiveResourcesNamesByRegion(region)

        return allResourcesNames

    def getRdsTags(self, instanceArn, region):

        tags = []
        results = json.loads(subprocess.check_output(("aws rds list-tags-for-resource --resource-name {} --region {}").format(instanceArn, region), shell=True))

        for tag in results['TagList']:
            tags.append(tag)

        print("DBS list-tags query failed.")

        return tags


    def getActiveResourcesNamesByRegion(self, region):

        resources = {'RDS': [], 'EC2': [], 'ELB': [], 'STACKS': [], 'ASG': []}
        tempResources = {}

        tempResources['RDS'] = self.getActiveRDS(region)
        tempResources['EC2'] = self.getActiveEc2(region)
        tempResources['ELB'] = self.getElbsByRegion(region)
        tempResources['STACKS'] = self.getActiveStacksByRegion(region)
        tempResources['ASG'] = self.getActiveAsgByRegion(region)

        if tempResources['RDS']:
            for instance in tempResources['RDS']:
                tempRDS = {}
                tempRDS['Name'] = instance['DBInstanceIdentifier']
                tempRDS['tags'] = self.getRdsTags(instance['DBInstanceArn'], region)
                resources['RDS'].append(tempRDS)

        if tempResources['EC2']:
            for instance in tempResources['EC2']:
                tempEC2 = {}
                try:
                    tempEC2['tags'] = instance['Tags']
                except:
                    tempEC2['tags'] = None
                tempEC2['instanceId'] = instance["InstanceId"]
                tempEC2['Name'] = instance['PrivateDnsName']
                resources['EC2'].append(tempEC2)

        if tempResources['ELB']:
            for instance in tempResources['ELB']['LoadBalancerDescriptions']:
                tempELB = {}
                tempELB['tags'] = self.getElbTagsByElbName(instance['LoadBalancerName'], region)
                tempELB['Name'] = instance['LoadBalancerName']
                resources['ELB'].append(tempELB)

        if tempResources['STACKS']:
            for stack in tempResources['STACKS']:
                tempStacks = {}
                tempStacks['Name'] = stack['StackName']
                tempStacks['tags'] = self.getStackTags(stack['StackName'], region)
                resources['STACKS'].append(tempStacks)

        if tempResources['ASG']:
            for asg in tempResources['ASG']:
                tempAsg = {}
                try:
                    tempAsg['tags'] = self.getAsgTags(asg['AutoScalingGroupName'], region)

                except:
                    tempAsg['tags'] = None

                tempAsg['Name'] = asg['AutoScalingGroupName']
                resources['ASG'].append(tempAsg)


        return resources

    def getActiveRDS(self, region=None):

        if region == None:
            rdsInfo = self.queryRds(region=None)

        else:
            rdsInfo = self.queryRds(region=region)

        rdsInstances = []

        for instance in rdsInfo["DBInstances"]:
            if instance["DBInstanceStatus"] == "available":
                rdsInstances.append(instance)

        return rdsInstances

    def getActiveEc2(self, region=None):

        if region == None:
            ec2 = self.queryEc2(region=None)

        else:
            ec2 = self.queryEc2(region=region)

        instances = []

        for reservation in ec2["Reservations"]:
            for instance in reservation['Instances']:

                if instance['State']['Name'] == "running":
                    instances.append(instance)

        return instances

    def getElbsByRegion(self, region):
        return self.queryElb(region=region)
                

    def getInstancesByElb(self, elbName, region=None):
        
        if region == None:
            elbInfo = self.queryElb(region=None, elbName=elbName)       

        else:
            elbInfo = self.queryElb(region=region, elbName=elbName)

        instances = []
        
        for elb in elbInfo["LoadBalancerDescriptions"]:
            for instance in elb['Instances']:
                instances.append(instance)

        return instances 
        


    def getElbInfo(self, describeElbDict=None, region=None):
       
       loadBalancerDict = {}

       if describeElbDict == None:
          describeElbDict = self.queryElb(region)

       for loadBalancer in describeElbDict['LoadBalancerDescriptions']: 
           loadBalancerDict[loadBalancer['LoadBalancerName']] = {}
           loadBalancerDict[loadBalancer['LoadBalancerName']]['region'] = loadBalancer['AvailabilityZones'][0][:-1]
           

       return loadBalancerDict

    def getAllElbTags(self):
   
        elbTagsDict = {}
        for region in self.__region_list:
            elbTagsDict[region] = self.getElbTagsByRegion(region)
            elbTagsDict[region].update(self.getElbsByRegion(region))

        return elbTagsDict 


    def getElbTagsByRegion(self, region):
           
        elbTagsDict = {}
  
        elbInfo = self.getElbInfo(region=region)
        for loadBalancer in elbInfo:
            parsedElbQuery = self.__elb_query.replace("<REGION>", region)
            parsedElbQuery = parsedElbQuery.replace("<ElbName>", loadBalancer)
            queryResults = json.loads(subprocess.check_output( parsedElbQuery, shell=True ))
            elbTagsDict[loadBalancer] = self.parseElbTags(queryResults)
    
        return elbTagsDict 


    def parseElbTags(self, elbTagsDict):
    
        tagList = []

        try:
            for tagDesc in elbTagsDict['TagDescriptions']:
                for tag in tagDesc['Tags']:
                    tagList.append(tag)

        except:
            print("tagList not populated in parseElbTags. No tags exist")

        return tagList
      
      

    def getElbTagsByElbName(self, elbName, region=None):

        if region == None:
            allElbsDict = self.getAllElbTags()
            
            for awsRegion in allElbsDict:
                if elbName in allElbsDict[awsRegion]:
                    return allElbsDict[awsRegion][elbName]

        else:
            elbsDict = self.getElbTagsByRegion(region)
            
            for elb in elbsDict:
                if elbName in elbsDict:
                    return elbsDict[elbName]



    def getAllCfStacksInRegion(self, stackStatusFilter="CREATE_COMPLETE"):

        stacks = {}
        pprint.pprint(self.regionList)
        for region in self.regionList:
            stacks[region] = {}
            stacks[region].update(self.listStacks(region))

        return stacks

    def getStackTags(self, stackName, region):
        #pprint.pprint("wat: " + str(self.describeStacks(region, stackName=stackName)))

        try:

            stacks = self.describeStacks(region, stackName)
            for stack in stacks['Stacks']:
                return stack['Tags']

        except:
            return None

    def getStacks(self):

        stacks = {}
        try:
            for region in self.regionList:
                stacks[region] = {}
                stacks[region].update(self.describeStacks(region))

        except:
            return None

        return stacks


    def getActiveStacksByRegion(self, region):

        stacks = self.describeStacks(region)
        activeStacks = []

        for stack in stacks['Stacks']:
            if stack['StackStatus'] == "CREATE_COMPLETE":
                activeStacks.append(stack)

        return activeStacks

    def getActiveAsgByRegion(self, region):

        asgs = self.queryAsg(region)
        activeAsgs = []

        for asg in asgs['AutoScalingGroups']:
            activeAsgs.append(asg)

        return activeAsgs

    def getAsgTags(self, asgName, region):

        try:
            asgs = self.queryAsg(region, asgName)
            for asg in asgs['AutoScalingGroups']:
                return asg['Tags']

        except:
            return None


test = awsManager()
with open(os.getcwd() + "/config.json") as config:
    config = json.load(config)

test.regionList = config['focusRegions']
stacks = (test.getAllCfStacksInRegion())
pprint.pprint(stacks)

#pprint.pprint(test.getAllActiveResourcesNames())

test.getActiveAsgByRegion('us-east-1')

for region in test.regionList:
    pprint.pprint(test.getActiveResourcesNamesByRegion(region))

#for region in stacks:
 #   for stackSummary in stacks[region]:
  #      for stack in stacks[region][stackSummary]:
   #         pprint.pprint(test.getStackTags(stack['StackName'], "us-east-2"))

