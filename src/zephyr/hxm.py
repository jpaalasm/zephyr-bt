
#Specification of HxM payload bytes:
#Firmware ID
#Firmware Version
#Hardware ID
#Hardware Version
#Battery Charge Indicator
#Heart Rate
#Heart Beat Number
#Heart Beat Timestamp #1 (Oldest)
#Heart Beat Timestamp #2
#...
#Heart Beat Timestamp #14
#Heart Beat Timestamp #15 (Oldest)
#Reserved
#Reserved
#Reserved
#Distance
#Instantaneous speed
#Strides
#Reserved
#Reserved

import logging

import zephyr.message


class HxMMessageParser:
    def __init__(self, callback):
        self.callback = callback
    
    def handle_message(self, message):
        if message.message_id != 0x26:
            logging.error("This is not an HxM message")
            return
        
        hxm_message = zephyr.message.parse_hxm_message(message.payload)
        self.callback(hxm_message)
