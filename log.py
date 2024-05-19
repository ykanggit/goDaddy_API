import platform
from logging import handlers

from loguru import logger

def linux_syslog (name:str):
    ''' for Linux system, call this function to add <name> leading logs into syslog utility '''
    if platform.system() == 'Linux':
        hdl = handlers.SysLogHandler(address='/dev/log')
        logger.add (hdl, format=f"{name} | " + "{level} | {file}:{line}:{function} | {message}")
    else:
        logger.info(f"not write to syslog with {name} on platform {platform.system()}")