import os
from typing import List, Union
import requests
from pydantic import BaseModel
from slack_sdk import WebClient

from log import logger

class MSG (BaseModel):
    '''https://api.slack.com/reference/messaging/payload
    '''
    text:str
    blocks:list = None
    attachments:list = None
    thread_ts:str = None
    mrkdwn:bool = None

class Bot():

    def __init__(self, token:str=os.environ.get("SLACK_4RUNNER_TOKEN", "")) -> None:
        if token == "":
            raise Exception("Error: environment var SLACK_4RUNNER_TOKEN not set")
        self.token_last4 = token[-4:]
        self.webclient = WebClient(token=token)

    def __str__(self):
        return f"slack_sdk.WebClient(token=...{self.token_last4})"
    
    def list_channels (self) -> List[dict]:
        result = self.webclient.conversations_list()
        channels = result.get("channels", [])
        return channels
    
    def list_users(self, include_deleted=False, include_bot=False, only_return_name=True) -> Union[List[dict], List[str]]:
        '''
            by default list only active users
        '''
        all_users = []
        cursor = None  # Pagination cursor, initially None
        while True:
            result = self.webclient.users_list(cursor=cursor)
            users = result.get("members", [])  # Extract user list
            all_users.extend(users)
            cursor = result.get("next_cursor")
            if not cursor:
                break
        if include_deleted is False:
            all_users = [i for i in all_users if i.get('deleted', False) is not True]
        if include_bot is False:
            all_users = [i for i in all_users if i.get('is_bot', False) is not True]
        if only_return_name:
            all_users = [i.get('name') for i in all_users]
        return all_users
        
    def username2id(self, name:str) -> str:
        # only search active usrs
        usernames = self.list_users(only_return_name=False)
        for i in usernames:
            if i.get('name',None) == name:
                return i.get('id',None)
        return None
        
    def send_msg_to_channel (self, channelID:str, msg:str) -> dict:
        '''
            if not in channel, exception will be raised
            <return> a dict of result, just for ref not really affect the msg delivery
        '''
        result = self.webclient.chat_postMessage(
            channel=channelID,
            text=msg
        )
        return result
    
    def send_dm_to_user (self, username:str, msg:str):
        userID=self.username2id(username)
        if userID is None:
            raise Exception(f'Error: can not find username: {username}')

        # Open a DM channel with the user
        result = self.webclient.conversations_open(users=[userID])
        channel = result.get("channel")
        channel_id = channel.get("id")

        # Send the message
        resp = self.webclient.chat_postMessage(
            channel=channel_id,
            text=msg
        )
        return resp
