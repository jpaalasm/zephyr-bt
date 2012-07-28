
import os
import logging
from time import time as system_time
from time import sleep as system_sleep

def configure_root_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    log_file_path = os.path.join(os.path.expanduser("~"), "pyzephyr.log")
    file_handler = logging.FileHandler(log_file_path, mode="w")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logging.info("Logging to %s", log_file_path)

# pyzephyr has its own time function so that it can be mocked for testing purposes
def time():
    return system_time()

def sleep(seconds):
    system_sleep(seconds)
