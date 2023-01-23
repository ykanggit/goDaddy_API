import os

SLACK_WEBHOOK = os.environ['SLACK_3510_WEBHOOK']

class GODADDY:
    API_KEY = os.environ['GODADDY_API_KEY']
    API_SECRET = os.environ['GODADDY_API_SECRET']

class IOOI:
    AWS_KEY = os.environ['IOOI_AWS_KEY']
    AWS_SEC = os.environ['IOOS_AWS_SEC']
    INST_ID = os.environ['IOOI_AWS_INSTANCE_ID']
    HOSTNAME = os.environ['IOOI_HOSTNAME']