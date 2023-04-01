import requests
import os, sys
import validators
import time

from time import sleep
from loguru import logger

# set up authentication credentials
api_key = os.environ['GODADDY_API_KEY']
api_secret = os.environ['GODADDY_API_SECRET']

def is_available (domain) -> bool:
    hdrs = {
        "Authorization": f"sso-key {api_key}:{api_secret}",
        "Content-Type": "application/json"
    }
    cnt=1
    while True:
        sys.stdout.write('.')
        sys.stdout.flush()
        while cnt:
            time.sleep(0.1)
            cnt -= 1
        response = requests.get(
            f"https://api.godaddy.com/v1/domains/available?domain={domain}",
            headers=hdrs
        )
        if response.status_code == 200:
            response_json = response.json()
            if response_json["available"]:
                logger.info (f"'{domain}' YES")
                return True
            return False
        else:
            logger.error (f"Error checking availability for domain '{domain}': {response.text}")
            rj = response.json()
            if 'retryAfterSec' in rj:
                logger.debug (f"API request backoff {rj['retryAfterSec']} second")
                cnt = rj['retryAfterSec'] * 10


if __name__ == '__main__':
    logger.remove()
    logger.add (sys.stdout, level="DEBUG")
    ok=[]
    for l1 in range(ord('a'), ord('z') + 1):
        for l2 in range(ord('a'), ord('z') + 1):
            domain = chr(l1)+chr(l2)+".ai"
            if is_available  (domain):
                ok.append (domain)
    print (ok)
    from slack import MSG, ChatBot
    from cfg import SLACK_WEBHOOK
    bot = ChatBot(SLACK_WEBHOOK)
    bot.send (f"{ok}")