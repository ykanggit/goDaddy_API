import os

import requests
from requests.models import Response
import tldextract
from loguru import logger
from rich import print
import validators

class GoDaddy:
    ''' godaddy.com API
    '''
    def __init__(self, api_key, api_secret) -> None:
        self.api = requests.Session()
        self.api.headers.update ({'Authorization': f"sso-key {api_key}:{api_secret}"})
        self.api.headers.update ({"content-type": "application/json"})

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

    def set_dns_A_record (self, dns_name:str, ipv4:str) -> None:
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
        logger.debug (f"set {ipv4} -> {dns_name}")

    def delete_dns_A_record (self, dns_name:str) -> None:
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





if __name__ == '__main__':
    g = GoDaddy (api_key=os.environ['GODADDY_API_KEY'], api_secret=os.environ['GODADDY_API_SECRET'])
    g.set_dns_A_record (dns_name='test.mydomain.com', ipv4='10.1.1.2')
    g.get_dns_A_records (dns_name='test.mydomain.com')
    g.delete_dns_A_record (dns_name='test.mydomain.com')
    g.get_dns_A_records (dns_name='test.mydomain.com')