from typing import List
import json
from datetime import datetime

import boto3
from boto3.session import Session
from log import logger



def convert_dict_values(data):
    """
        Recursively converts string values in a dictionary to dictionaries.
        Args: data: The input dictionary.
        Returns: A new dictionary with converted values.
    """
    if isinstance(data, dict):
        return {key: convert_dict_values(value) for key, value in data.items()}
    elif isinstance(data, str):
        try: # Attempt to convert the string to a dictionary using eval
            return eval(data)
        except (NameError, SyntaxError): # If conversion fails, return the original string
            return data
    else:
        return data


class AWS:
    def __init__(self, profile, region='us-west-2') -> None:
        self.session = boto3.Session(profile_name=profile, region_name=region)

    def __str__(self) -> str:
        return f'{self.session.profile_name}({self.session.region_name})'

class SNS(AWS):
    def __init__(self, profile, region) -> None:
        super().__init__(profile, region)
        self.client = self.session.client('sns')

    def __str__(self) -> str:
        return f"{super().__str__()} -> SNS"

    def create_topic (self, name:str) -> str:
        try:
            resp = self.client.create_topic(Name=name)
            topic_arn = resp['TopicArn']
            logger.info(f"SNS topic created successfully: {topic_arn}")
            return topic_arn
        except Exception as e:
            logger.error(e)
            return None

    def delete_topic (self, topic_arn:str):
        try:
            resp = self.client.delete_topic(TopicArn=topic_arn)
            logger.info(f"{topic_arn} deleted:{resp}")
        except Exception as e:
            logger.error(e)

    def topics (self)-> List[str]:

        result=[]

        def append_topics (topics):
            for topic in topics:
                result.append(topic['TopicArn'])

        try:
            response = self.client.list_topics()
            next_token = response.get('NextToken')
            append_topics(response['Topics'])
            while next_token:
                response = self.client.list_topics(NextToken=next_token)
                next_token = response.get('NextToken')
                append_topics(response['Topics'])
            return result

        except Exception as e:
            logger.error(e)
            return None

    def one_topic(self, topic_arn) -> dict:
        try:
            response = self.client.get_topic_attributes(TopicArn=topic_arn)
            return convert_dict_values(response['Attributes'])
        except Exception as e:
            logger.error(e)
            return None

    def subscribe (self, topic_arn, protocol, endpoint):
        '''
            sns_client.subscribe(
                TopicArn="arn:aws:sns:us-west-2:598139847569:Kaamel_GuardDuty_to_Email",
                Protocol="email",
                Endpoint="sec@kaamel.com"
            )
        '''
        try:
            sns_client = self.session.client('sns')
            resp = sns_client.subscribe(
                TopicArn=topic_arn,
                Protocol=protocol,
                Endpoint=endpoint
            )
            logger.info(resp)
        except Exception as e:
            logger.error(e)
            return None

class Event(AWS):
    def __init__(self, profile, region) -> None:
        super().__init__(profile, region)
        self.client = self.session.client('events')

    def __str__(self) -> str:
        return f"{super().__str__()} -> EventBridge"

    def put_rule(self, rule_name:str, pattern:dict, descriptoin:str):
        try:
            resp = self.client.put_rule(
                Name=rule_name,
                Description=descriptoin,
                EventPattern=json.dumps(pattern)
            )
            logger.info(resp)
        except Exception as e:
            logger.error(e)

    def delete_rule(self, rule_name:str):
        try:
            resp = self.client.delete_rule(Name=rule_name)
            logger.info(resp)
        except Exception as e:
            logger.error(e)

    def list_rules(self) -> list:
        result = []
        try:
            resp = self.client.list_rules()
            return resp['Rules']
        except Exception as e:
            logger.error(e)

    def list_targets_by_rule(self, name:str) -> list:
        try:
            resp = self.client.list_targets_by_rule(Rule=name)
            return resp.get('Targets', [])
        except Exception as e:
            logger.error(e)
            return None

    def put_target(self, rule_name:str, target_arn:str, id:str='1'):
        try:
            resp = self.client.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        'Id': id,
                        'Arn': target_arn
                    }
                ]
            )
            logger.info (resp)
        except Exception as error:
            logger.error(error)

    def remove_target(self, rule_name:str, id:str):
        try:
            resp = self.client.remove_targets( Rule=rule_name, Ids=[id])
            logger.info (resp)
        except Exception as error:
            logger.error(error)

class EC2(AWS):
    # cached region list
    _regions = None

    def __init__(self, profile, region) -> None:
        super().__init__(profile, region)
        self.client = self.session.client('ec2')

    def __str__(self) -> str:
        return f"{super().__str__()} -> EC2"

    @classmethod
    def regions(cls)->List[str]:
        if cls._regions is None:
            s = Session()
            cls._regions = s.get_available_regions('ec2')
        return cls._regions

    def enable_flow_logs(self, vpc_id:str, log_group_name:str, role_arn:str):
        """ Enables VPC flow logs for the specified VPC.
            Args:
            vpc_id (str): ID of the VPC for which to enable flow logs.
            log_destination_type (str, optional): Destination for flow logs (cloud-watch-logs, s3, kinesis-firehose). Defaults to "cloud-watch-logs".
            log_group_name (str, optional): Name of the CloudWatch log group for flow logs (required if log_destination_type is "cloud-watch-logs").
        """
        try:
            # Describe VPC to check if flow logs are already enabled
            describe_response = self.client.describe_flow_logs(Filters=[{'Name': 'resource-id', 'Values': [vpc_id]}])
            if describe_response['FlowLogs']:
                logger.info(f"Flow logs are already enabled for VPC {vpc_id}.")
                return

            # Enable flow logs for the VPC
            self.client.create_flow_logs(
                ResourceIds=[vpc_id],
                ResourceType="VPC",
                TrafficType="REJECT",                       # Adjust traffic type (ALL, ACCEPT, REJECT)
                LogDestinationType="cloud-watch-logs",
                LogGroupName=log_group_name,
                DeliverLogsPermissionArn=role_arn
            )

            '''
            flow_log_params = {
                'TrafficType': 'REJECT',  # You can choose 'ALL' or 'ACCEPT' or 'REJECT'
                'LogDestinationType': "cloud-watch-logs",
                'LogGroupName': log_group_name
            }
            #self.client.create_flow_logs(ResourceIds=[vpc_id], **flow_log_params)
            '''
            logger.info(f"{self} enabled flow logs for VPC {vpc_id} Role {role_arn} write to {log_group_name}")
        except Exception as e:
            logger.error(e)

    def instances(self, filter=None) -> List[tuple]:
        # Describe EC2 instances
        result = []
        try:
            if filter is None:
                response = self.client.describe_instances()
            else:
                response = self.client.describe_instances(Filters=filter)
            reservations = response.get('Reservations', [])
            # Loop through reservations and print instance details
            for reservation in reservations:
                for instance in reservation['Instances']:
                    result.append((instance['InstanceId'],instance['InstanceType']))
            return result
        except Exception as e:
            logger.error(e)

    def running_instances(self) -> List[tuple]:
        # Filter by instance state
        filters = [{'Name': 'instance-state-name', 'Values': ['running']}]
        return self.instances(filter=filters)

    def get_instance_tags (self, instanceID)->List[tuple]:
        filters = [{'Name': 'resource-id', 'Values': [instanceID]}]
        result=[]
        try:
            response = self.client.describe_tags(Filters=filters)
            tags = response.get('Tags', [])
            for i in tags:
                result.append((i.get('Key',''), i.get('Value','')))
            return result
        except Exception as e:
            logger.error(e)

    def set_instance_tags (self, instanceID:str, tags:List[dict]):
        # tags = [{"Key": "Name", "Value": "My Web Server"}, {"Key": "Environment", "Value": "Production"}]
        try:
            response = self.client.create_tags(Resources=[instanceID], Tags=tags)
            logger.info(f"Successfully tagged instance {instanceID}: {tags}")
        except Exception as e:
            logger.error(e)

class IAM(AWS):
    def __init__(self, profile, region) -> None:
        super().__init__(profile, region)
        self.client = self.session.client('iam')

    def __str__(self) -> str:
        return f"{super().__str__()} -> IAM"

    def create_role (self, name:str, trustee:dict) -> dict:
        ''' return role object '''
        try:
            resp = self.client.create_role(
                RoleName=name,
                AssumeRolePolicyDocument=json.dumps(trustee)
            )
            return resp['Role']
        except Exception as e:
            logger.error(e)
            return None

    def delete_role (self, name:str):
        try:
            self.client.delete_role(RoleName=name)
        except Exception as e:
            logger.error(e)

    def attach_role_policy (self, role_name:str, policy_arn:str):
        try:
            self.client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            logger.info(f"Police({policy_arn}) -> Role({role_name})")
        except Exception as e:
            logger.error(e)

    def create_policy (self, name:str, policy:dict, description:str) -> dict:
        ''' return Policy obj'''
        try:
            resp = self.client.create_policy(
                PolicyName=name,
                PolicyDocument=json.dumps(policy),
                Description=description
            )
            return resp['Policy']
        except Exception as e:
            logger.error(e)

    def delete_policy (self, arn):
        try:
            self.client.delete_policy(PolicyArn=arn)
        except Exception as e:
            logger.error(e)

    def list_policies (self, prefix:str=None) -> list:
        try:
            paginator = self.client.get_paginator('list_policies')
            page_iterator = paginator.paginate()
            policies = []
            for page in page_iterator:
                policies.extend(page['Policies'])
            if prefix is None:
                return policies
            result = []
            for p in policies:
                if prefix.lower() in p['PolicyName'].lower():
                    result.append(p)
            return result
        except Exception as e:
            logger.error(e)

    def list_roles (self, prefix:str=None) -> list:
        try:
            paginator = self.client.get_paginator('list_roles')
            page_iterator = paginator.paginate()
            roles = []
            for page in page_iterator:
                roles.extend(page['Roles'])
            if prefix is None:
                return roles
            result = []
            for r in roles:
                if prefix.lower() in r['RoleName'].lower():
                    result.append(r)
            return result
        except Exception as e:
            logger.error(e)

class Logs(AWS):
    def __init__(self, profile, region) -> None:
        super().__init__(profile, region)
        self.client = self.session.client('logs')

    def __str__(self) -> str:
        return f"{super().__str__()} -> Logs"

    def list_log_groups(self, prefix:str = None) -> list:
        result = []
        try:
            resp = self.client.describe_log_groups()
            for group in resp['logGroups']:
                if prefix is None or prefix.lower() in group['logGroupName'].lower():
                    result.append(
                        {
                        'Name': group['logGroupName'],
                        'ARN': group['arn'],
                        'Creation': group['creationTime']
                        }
                    )
            return result
        except Exception as e:
            logger.error(e)

    def describe_one_log_group(self, name:str):
        try:
            resp = self.client.describe_log_groups(logGroupNamePrefix=name)
            # Check if log group exists (handle empty response)
            if not resp['logGroups']:
                logger.debug('{name} not exist in {self}')
                return

            # Access information from the first log group (assuming it's the only one)
            return resp['logGroups'][0]
        except Exception as e:
            logger.error(e)

    def create_log_group(self, name:str):
        try:
            resp = self.client.create_log_group(logGroupName=name)
            logger.info(f'{name} created')
        except Exception as e:
            logger.error(e)

    def delete_log_group(self, name:str):
        try:
            resp = self.client.delete_log_group(logGroupName=name)
            logger.info(f'{name} deleted')
        except Exception as e:
            logger.error(e)

class Route53(AWS):
    def __init__(self, profile, region) -> None:
        super().__init__(profile, region)
        self.client = self.session.client('route53')

    def __str__(self) -> str:
        return f"{super().__str__()} -> Route53"

    def get_zone_id_by_name(self, zone_name:str) -> str:
        ''' e.g: oakridge.io. '''
        if zone_name[-1] != '.':
            zone_name=zone_name+'.'
        try:
            # Get a list of all hosted zones
            paginator = self.client.get_paginator('list_hosted_zones')
            for page in paginator.paginate():
                for zone in page['HostedZones']:
                    if zone['Name'] == zone_name:
                        return zone['Id'].split('/')[-1]  # Zone ID found, return it
            return None  # Zone not found in any page
        except Exception as e:
            logger.error(e)
            return None

    def get_a_record(self, hosted_zone_id, record_name) -> dict:
        ''' e.g: 4runner.oakridge.io '''
        try:
            # Get resource record set using list_resource_record_sets with filtering
            response = self.client.list_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                StartRecordName=record_name,
                StartRecordType='A'
            )

            # Check if record set exists in the response
            if "ResourceRecordSets" in response and response["ResourceRecordSets"]:
                record_set = response["ResourceRecordSets"][0]
                # Return only relevant A record details
                return record_set
                {
                    "Name": record_set["Name"],
                    "Type": record_set["Type"],
                    "TTL": record_set["TTL"],
                    "Values": record_set["ResourceRecords"][0]["Value"]  # Assuming single value
                }
            else:
                return None  # Record not found

        except Exception as e:
            logger.error(e)
        return None

    def set_a_record(self, hosted_zone_id:str, record_name:str, new_value:str, comments:str=f'Updated at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'):
        """
        Args:
            hosted_zone_id: The ID of the Route53 hosted zone.
            record_name: The DNS name of the record to update (e.g., "www.example.com").
            new_value: The new IP address value for the A record.
        Returns:
            A dictionary containing the response from Route53 on successful update, 
            or None if update fails.
        """
        try:
            # Define the change details
            change_batch = {
                "Changes": [
                    {
                        "Action": "UPSERT",  # Update or create the record if it doesn't exist
                        "ResourceRecordSet": {
                            "Name": record_name,
                            "Type": "A",
                            "TTL": 300,  # Time to Live (seconds) - You can adjust this value
                            "ResourceRecords": [
                                {"Value": new_value}
                            ]
                        }
                    }
                ],
                "Comment": comments
            }

            # Send the update request to Route53
            response = self.client.change_resource_record_sets(HostedZoneId=hosted_zone_id, ChangeBatch=change_batch)
            logger.debug(f'{record_name} new value {new_value}')
            return response
        except Exception as e:
            logger.error(e)
            return None
