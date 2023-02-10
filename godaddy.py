import requests
from requests.models import Response
import tldextract
from loguru import logger
from rich import print
import validators
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import pytz

from cfg import GODADDY

class Domain(BaseModel):
    createdAt:datetime
    deletedAt:Optional[datetime]
    domain:str
    domainId:int
    expirationProtected:bool
    expires:datetime
    exposeWhois: bool
    holdRegistrar: bool
    locked: bool
    nameServers:Optional[str]=None
    privacy:bool
    registrarCreatedAt:datetime
    renewAuto: bool
    renewable: bool
    status:str
    transferProtected: bool

    def __str__(self) -> str:
        s = f"{self.domain}" 
        now = datetime.now(pytz.utc)
        if self.expires > now:
            s += f" created({self.createdAt})"
        else:
            s += f" expired({self.expires})"
        return s

class DnsRecord (BaseModel):
    data:str
    name:str
    port:Optional[int]
    priority:Optional[int]
    protocol:Optional[str]
    service:Optional[str]
    ttl:int
    type:str
    weight:Optional[int]

    def __str__(self) -> str:
        return f"{self.type}: {self.name} ->{self.data}"

class GoDaddy:
    ''' godaddy.com API
    '''
    def __init__(self, api_key=GODADDY.API_KEY, api_secret=GODADDY.API_SECRET) -> None:
        self.api = requests.Session()
        self.api.headers.update ({'Authorization': f"sso-key {api_key}:{api_secret}"})
        self.api.headers.update ({"content-type": "application/json"})
    
    def domains(self, active_only=True)->list:
        resp = self.api.get(url=f"https://api.godaddy.com/v1/domains")
        if not resp.ok:
            raise Exception(resp.text)
        rc=[]
        for d in resp.json():
            o = Domain.parse_obj(d)
            if active_only:
                now = datetime.now(pytz.utc)
                if o.expires <= now:
                    continue
            rc.append(o)
        return rc

    @property
    def domain_strs (self) -> list:
        ''' list active domains
        '''
        rl = []
        for d in self.domains():
            rl.append(d.domain)
        return rl

    @property
    def active_domains(self)->List[Domain]:
        return self.domains()

    @property
    def all_domains(self)->List[Domain]:
        return self.domains(active_only=False)

    def list_domain_records(self,domain:str, type:str="*")->List[DnsRecord]:
        resp = self.api.get(url=f"https://api.godaddy.com/v1/domains/{domain}/records")
        if not resp.ok:
            raise Exception(resp.text)
        rc=[]
        for j in resp.json():
            r = DnsRecord.parse_obj(j)
            if type == "*" or type == r.type:
                rc.append(r)
        return rc
    
    def one_domain_detail (self, name)->dict:
        resp = self.api.get(url=f"https://api.godaddy.com/v1/domains/{name}")
        if not resp.ok:
            raise Exception(resp.text)
        return resp.json()

    def get_dns_A_records (self, dns_name:str) -> Response:
        ''' input <xyz.com>
        '''
        if not validators.domain(dns_name):
            raise (f"{dns_name} is NOT valid domain")
        tld = tldextract.extract(dns_name)
        url = f"https://api.godaddy.com/v1/domains/{tld.registered_domain}/records/A/{tld.subdomain}"
        resp = self.api.get(url=url)
        if not resp.ok:
            raise Exception(f"Fail get {dns_name} DNS record:{resp.text}")
        logger.debug (f"got {dns_name} record: {resp.json()}")
        return resp

    def set_dns_A_record (self, dns_name:str, ipv4:str, double_check=False) -> None:
        if double_check:
            ok=input(f"Are you sure want to add DNS record({dns_name}) to godaddy.com?\nInput <YES> to confirm, any key to abort:")
            if ok != "YES":
                logger.debug (f"abort adding DNS record {dns_name}")
                return
        if not validators.domain(dns_name):
            raise (f"{dns_name} is NOT valid domain")
        if not validators.ipv4(ipv4):
            raise (f"{dns_name} is NOT valid IPv4 address")
        tld = tldextract.extract(dns_name)
        url = f"https://api.godaddy.com/v1/domains/{tld.registered_domain}/records/A/{tld.subdomain}"
        payload = [{
            'data': ipv4,
            'name': tld.subdomain,
            'ttl': 1800,
            'type': 'A'
        }]
        resp = self.api.put (url=url,json=payload)
        if not resp.ok:
            raise Exception(f"Fail set {dns_name} DNS record:{resp.text}")
        logger.debug (f"set DNS record: {ipv4} -> {dns_name}")

    def delete_dns_A_record (self, dns_name:str, double_check=False) -> None:
        if double_check:
            ok=input(f"Are you sure want to delete DNS record({dns_name}) from godaddy.com?\nInput <YES> to confirm, any key to abort:")
            if ok != "YES":
                logger.debug (f"abort deleting DNS record {dns_name}")
                return
        if not validators.domain(dns_name):
            raise (f"{dns_name} is NOT valid domain")
        tld = tldextract.extract(dns_name)
        url = f"https://api.godaddy.com/v1/domains/{tld.registered_domain}/records/A/{tld.subdomain}"
        resp = self.api.delete (url=url)
        if not resp.ok:
            if resp.status_code != 404:
                raise Exception(f"Fail delete {dns_name} DNS record:return code({resp.status_code}) {resp.text}")
            logger.debug (f"{dns_name} not found")
        logger.debug (f"Done: deleting {dns_name}")

    def ip_for (self, hostname:str):
        resp = self.get_dns_A_records(hostname)
        record_list = resp.json()
        if len(record_list):
            logger.debug (f"DNS record for {hostname}: {record_list}")
            return record_list[0]['data']
        else:
            logger.debug (f"no DNS record for {hostname}")
            return None



if __name__ == '__main__':
    while True:
        test_domain_name =input("Input a domain name to test <set/get/delete> API:\n")
        if validators.domain(test_domain_name):
            break
        print (f"{test_domain_name} is not valid domain name")
    g = GoDaddy ()
    g.set_dns_A_record (dns_name=test_domain_name, ipv4='10.1.1.1', double_check= True)
    g.get_dns_A_records (dns_name=test_domain_name)
    g.delete_dns_A_record (dns_name=test_domain_name, double_check=True)
    g.get_dns_A_records (dns_name=test_domain_name)
