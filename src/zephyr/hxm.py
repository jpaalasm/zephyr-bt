
import time

import zephyr.message


class HxMHelper:
    def __init__(self, packet):
        latest_heartbeat_timestamp = packet.heartbeat_timestamps[0]
        self.previous_heartbeat_number = packet.heartbeat_number
        self.offset = zephyr.time() - latest_heartbeat_timestamp
        self.previous_relative_timestamp = latest_heartbeat_timestamp
    
    def fix_relative_timestamps(self, timestamps):
        for timestamp in timestamps:
            while timestamp < self.previous_relative_timestamp:
                timestamp += 2**16 * 0.001
            
            heartbeat_interval = timestamp - self.previous_relative_timestamp
            
            self.previous_relative_timestamp = timestamp
            
            yield timestamp + self.offset, heartbeat_interval
    
    def process(self, packet):
        history_cache_length = len(packet.heartbeat_timestamps)
        
        heartbeat_increment = (packet.heartbeat_number - self.previous_heartbeat_number) % 256
        
        if heartbeat_increment > history_cache_length:
            raise ValueError("")
        
        new_timestamps = reversed(packet.heartbeat_timestamps[:heartbeat_increment])
        for heartbeat_timestamp, heartbeat_interval in self.fix_relative_timestamps(new_timestamps):
            yield heartbeat_timestamp, heartbeat_interval
        
        self.previous_heartbeat_number = packet.heartbeat_number


class HxMPacketAnalysis:
    def __init__(self, event_callbacks):
        self.event_callbacks = event_callbacks
        
        self.helper = None
    
    def handle_packet(self, packet):
        if isinstance(packet, zephyr.message.HxMMessage):
            current_timestamp = zephyr.time()
            
            if self.helper is None:
                self.helper = HxMHelper(packet)
            else:
                for timestamp, heartbeat_interval in self.helper.process(packet):
                    for event_callback in self.event_callbacks:
                        event_callback("heartbeat_interval", (timestamp, heartbeat_interval))
            
            for event_callback in self.event_callbacks:
                event_callback("heart_rate", (current_timestamp, packet.heart_rate))
                event_callback("activity", (current_timestamp, packet.speed / 3.0))
                event_callback("strides", (current_timestamp, packet.strides))
