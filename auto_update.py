import os
import requests
from loguru import logger
from godaddy import GoDaddy
from rich import print


def my_current_ipv4 () -> str:
    resp = requests.get('http://ipwho.is/')
    if not resp.ok:
        raise
    return resp.json()['ip']

def godaddy_ip_for (hostname:str):
    resp = g.get_dns_A_records(hostname)
    record_list = resp.json()
    if len(record_list):
        logger.debug (f"DNS record for {hostname}: {record_list}")
        return record_list[0]['data']
    else:
        logger.debug (f"no DNS record for {hostname}")
        return None


def setup_syslog():
    import platform
    from logging import handlers
    if platform.system() == 'Linux':
        logger.debug("Linux logging to /dev/log")
        hdl = handlers.SysLogHandler(address='/dev/log')
        logger.add(hdl, format="kaamel_gdpr_case_scraper | {level} | {file}:{line}:{function} | {message}")


if __name__ == "__main__":
    target ='host.mydomain.com'
    setup_syslog()
    g = GoDaddy (api_key=os.environ['GODADDY_API_KEY'], api_secret=os.environ['GODADDY_API_SECRET'])
    gdip = g.ip_for(target)
    myip = my_current_ipv4()
    logger.debug (f"My current IP({myip}), {target} GoDaddy IP({gdip})")
    if gdip == myip:
        logger.debug ("don't need update DNS record")
        pass
    else:
        g.set_dns_A_record(dns_name=target, ipv4=myip)