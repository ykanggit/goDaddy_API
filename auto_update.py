import requests
from loguru import logger
from godaddy import GoDaddy

from cfg import SLACK_WEBHOOK
from slack import MSG, ChatBot


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
    target ='4runner.iooi.life'
    # on Centos just use syslog directly for cronjob write to /var/log/messages
    from syslog import syslog
    # hardcode the keys for cronjob
    g = GoDaddy ()
    gdip = g.ip_for(target)
    myip = my_current_ipv4()
    logger.debug (f"My current IP({myip}), {target} GoDaddy IP({gdip})")
    if gdip == myip:
        logger.debug ("don't need update DNS record")
    else:
        g.set_dns_A_record(dns_name=target, ipv4=myip)
        txt=f"DNS record updated: {target} -> {myip}"
        syslog (txt)
        msg = MSG(text=txt)
        bot = ChatBot(SLACK_WEBHOOK)
        bot.send (msg)
