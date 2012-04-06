
import collections

import zephyr.util


HxMMessage = collections.namedtuple("HxMMessage", ["heart_rate", "heartbeat_number",
                                                   "heartbeat_timestamps", "distance",
                                                   "speed", "strides"])


def parse_hxm_message(payload):
    heart_rate, heartbeat_number = payload[9:11]
    
    heartbeat_timestamp_bytes = payload[11:41]
    
    movement_data_bytes = payload[47:53]
    
    distance, speed, strides = tuple(zephyr.util.parse_uint16_values_from_bytes(movement_data_bytes))
    
    distance = distance / 16.0
    speed = speed / 256.0
    
    heartbeat_timestamps = [t / 1000.0 for t in zephyr.util.parse_uint16_values_from_bytes(heartbeat_timestamp_bytes)]
    
    hxm_message = HxMMessage(heart_rate=heart_rate, heartbeat_number=heartbeat_number,
                             heartbeat_timestamps=heartbeat_timestamps, distance=distance,
                             speed=speed, strides=strides)
    return hxm_message
