import requests
import socket

from log import logger

def my_public_ip() -> str:
  try:
    response = requests.get("https://api.ipify.org")
    response.raise_for_status()  # Raise exception for non-2xx status codes
    ipv4= response.text.strip()  # Extract and strip whitespace from response
    return ipv4
  except requests.exceptions.RequestException as e:
    print(f"Error getting public IP: {e}")
    return None

def iplookup(hostname:str) ->str:
  try:
    # Get the IP address using gethostbyname
    ip_address = socket.gethostbyname(hostname)
    return ip_address
  except socket.gaierror as e:
    logger(e)
    return None

if __name__ == "__main__":
  import sys
  from log import linux_syslog
  linux_syslog(sys.argv[0])

  hostname = '4runner.oakridge.io'

  dns_ip=iplookup(hostname)
  if dns_ip is None:
    logger.error(f"fail ip lookup for {hostname}")
    exit(1)

  public_ip = my_public_ip()
  if public_ip is None:
    logger.error("fail get my public ip")
    exit(1)
    
  if public_ip == dns_ip:
    logger.info(f'{hostname} dns ip {dns_ip} == my public ip {public_ip}')
    exit(0)

  logger.info(f'updating {hostname} dns ip {dns_ip} -> {public_ip}')

  from aws import Route53

  rt = Route53('yong.kang@iooi', 'us-west-2')
  zone_id = rt.get_zone_id_by_name('oakridge.io')
  result = rt.set_a_record(zone_id, hostname, public_ip)
  logger.info(result)