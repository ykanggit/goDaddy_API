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
    while True:
        response = requests.get(
            f"https://api.godaddy.com/v1/domains/available?domain={domain}",
            headers=hdrs
        )
        if response.status_code == 200:
            sys.stdout.write('.')
            sys.stdout.flush()
            response_json = response.json()
            if response_json["available"]:
                logger.info (f"'{domain}' YES")
                return True
            return False
        else:
            sys.stdout.write('x')
            sys.stdout.flush()
            rj = response.json()
            logger.error (f"{response.status_code} for '{domain}': {rj}")
            if 'retryAfterSec' in rj:
                sleep (rj['retryAfterSec'])
            else:
                return False



if __name__ == '__main__':
    logger.remove()
    logger.add (sys.stdout, level="DEBUG")
    ok=[]
    suffix=['ai','io','com']
    for s in suffix:
        for l1 in range(ord('a'), ord('z') + 1):
            for l2 in range(ord('a'), ord('z') + 1):
                for l3 in range(ord('a'), ord('z') + 1):
                    domain = chr(l1)+chr(l2)+chr(l3)+f".{s}"
                    if is_available  (domain):
                        ok.append (domain)
    print (ok)
    from slack import MSG, ChatBot
    from cfg import SLACK_WEBHOOK
    msg = MSG(text=f"{ok}")
    bot = ChatBot(SLACK_WEBHOOK)
    bot.send (msg)
