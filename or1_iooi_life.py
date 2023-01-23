#!/usr/bin/python3
import validators
import os

import boto3
from botocore.exceptions import ClientError
from requests.models import Response
from loguru import logger


from godaddy import GoDaddy
from cfg import IOOI

class MyEc2Instance:
    def __init__(self) -> None:
        self.instance_id = IOOI.INST_ID
        self.hostname = IOOI.HOSTNAME
        self.region='us-west-2'
        self.session = boto3.Session (aws_access_key_id = IOOI.AWS_KEY, aws_secret_access_key = IOOI.AWS_SEC, region_name=self.region)
        self.client = self.session.client('ec2')
        self.resource = self.session.resource('ec2')
    
    @property
    def instance(self):
        return self.resource.Instance(self.instance_id)
    
    @property
    def public_ipv4(self) -> str:
        return self.instance.public_ip_address
    
    @property
    def allocatio_ID(self) -> str:
        ''' elastic-IP allocatin ID '''
        filters = [ {'Name': 'domain', 'Values': ['vpc']} ]
        response = self.client.describe_addresses(Filters=filters)
        alloc_id = None
        for a in response['Addresses']:
            if a['InstanceId'] == self.instance_id:
                alloc_id = a['AllocationId']
        return alloc_id
    
    def update_ipv4_and_dns(self, g=GoDaddy()) -> None:
        old_alloc_id = self.allocatio_ID
        try:
            eip = self.client.allocate_address (Domain='vpc')
            logger.debug (f"allocate new EIP {eip['PublicIp']}")
            res = self.client.associate_address (AllocationId=eip['AllocationId'], InstanceId=self.instance_id)
            logger.debug (f"associate {eip['PublicIp']} with instance {self.instance_id}")
        except ClientError as e:
            raise Exception(f"{e}")
        try:
            response = self.client.release_address(AllocationId=old_alloc_id)
            logger.debug (f"old EIP released")
        except ClientError as e:
            raise(f"{e}")
        new_ip = self.public_ipv4
        g.set_dns_A_record (dns_name=self.hostname, ipv4=new_ip)


if __name__ == '__main__':
    ec2 = MyEc2Instance()
    ec2.update_ipv4_and_dns()
    from slack import MSG, ChatBot
    from cfg import SLACK_WEBHOOK
    msg = MSG(text=f"{ec2.hostname} update to {ec2.public_ipv4}")
    bot = ChatBot(SLACK_WEBHOOK)
    bot.send (msg)