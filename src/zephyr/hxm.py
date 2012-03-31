
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
import collections


HxMMessage = collections.namedtuple("HxMMessage", ["heart_rate", "heartbeat_number",
                                                   "heartbeat_timestamps", "distance",
                                                   "speed", "strides"])


def parse_uint16_values_from_bytes(byte_values):
    assert not len(byte_values) % 2
    
    byte_iterator = iter(byte_values)
    
    while True:
        byte1 = byte_iterator.next()
        byte2 = byte_iterator.next()
        yield byte1 + (byte2 << 8)


class HxMMessageParser:
    def __init__(self, callback):
        self.callback = callback
    
    def handle_message(self, message):
        if message.message_id != 0x26:
            logging.error("This is not an HxM message")
            return
        
        payload = message.payload
        heart_rate, heartbeat_number = payload[9:11]
        
        heartbeat_timestamp_bytes = payload[11:41]
        
        movement_data_bytes = payload[47:53]
        
        distance, speed, strides = tuple(parse_uint16_values_from_bytes(movement_data_bytes))
        
        distance = distance / 16.0
        speed = speed / 256.0
        
        heartbeat_timestamps = [t / 1000.0 for t in parse_uint16_values_from_bytes(heartbeat_timestamp_bytes)]
        
        hxm_message = HxMMessage(heart_rate=heart_rate, heartbeat_number=heartbeat_number,
                                 heartbeat_timestamps=heartbeat_timestamps, distance=distance,
                                 speed=speed, strides=strides)
        
        self.callback(hxm_message)
