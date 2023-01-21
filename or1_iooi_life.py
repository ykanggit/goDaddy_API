#!/usr/bin/python3
import validators

from godaddy import GoDaddy
from cfg import GODADDY

def set_iooi_ipv4 (ipv4:str):
    DNSNAME='or1.iooi.life'
    if not validators.ipv4(ipv4):
        raise Exception(f"Invalid IPv4 <{ipv4}>")
    g = GoDaddy (api_key=GODADDY.API_KEY, api_secret=GODADDY.API_SECRET)
    g.set_dns_A_record (dns_name=DNSNAME, ipv4=ipv4)
    return g.get_dns_A_records (dns_name=DNSNAME)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <ipv4>")
    response = set_iooi_ipv4 (sys.argv[1])
    sys.exit(f"{response.json()}")
    
