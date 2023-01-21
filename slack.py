import requests
from pydantic import BaseModel

class MSG (BaseModel):
    '''https://api.slack.com/reference/messaging/payload
    '''
    text:str
    blocks:list = None
    attachments:list = None
    thread_ts:str = None
    mrkdwn:bool = None

class ChatBot():
    '''
    chatbot per <channel>
    '''
    def __init__ (self, webhook):
        self.channel_url = webhook

    def send (self, msg:MSG, timeout:int=5):
        ''' <msg>  can be plain text or slack's <mrkdwn>
            https://api.slack.com/messaging/composing/formatting
        '''
        requests.post (
            self.channel_url,
            headers = {'Content-Type': 'application/json'},
            data = msg.json(),
            timeout=timeout
        )