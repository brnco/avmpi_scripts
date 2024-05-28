'''
logging functions for AVMPI
'''
import logging
import re
import pathlib
import time
import sys


def init_log(logfile=False, loglevel_print=logging.INFO, conf=None):
    '''
    initializes log actions
    '''
    logger = logging.getLogger('main_logger')
    message_format = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
    '''
    if logfile:
        logfile_name = pathlib.Path(
                "log_" + time.strftime(
                    "%Y-%m-%d_%H:%M:%S",
                    time.localtime())
                + ".txt")
        if not conf:
            print("loading log location from config.ini...")
            conf = config.init()
        logfile_parent_dir = conf['log_dir']
        logfile_path = str(logfile_parent_sir / logfile_name)
        log_handler = logging.FileHandler(logfile_path)
        log_handler.setFormatter(message_format)
        log_handler.setLevel(logging.DEBUG)
        logger.addHandler(log_handler)
    '''
    '''
    make a handler for printing to terminal
    '''
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(message_format)
    stream_handler.setLevel(loglevel_print)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)
    logger.info("initializing logs...")
    return logger


def close_handlers():
    '''
    for use in interactive sessions and testing
    '''
    logger.logging.getLogger(__name__)
    handlers = logger.handlers
    for handler in handlers:
        logger.removeHandler(handler)
        handler.close()
