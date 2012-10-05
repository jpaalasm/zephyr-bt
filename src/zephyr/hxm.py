
import collections

import zephyr.message


class CalculationHistoryOverflow(Exception):
    pass


class MonotonicSequenceModuloCorrection:
    def __init__(self, modulo):
        self.modulo = modulo
        self.correction = 0
        self.previous_value = None
    
    def process(self, value):
        if self.previous_value is not None:
            while value + self.correction < self.previous_value:
                self.correction += self.modulo
        
        self.previous_value = value + self.correction
        
        return self.previous_value


def average(sequence):
    return float(sum(sequence)) / len(sequence)


class RelativeHeartbeatTimestampAnalysis:
    def __init__(self):
        self.previous_heartbeat_number = None
        self.previous_timestamp = None
        self.instantaneous_offset_deque = collections.deque(maxlen=30)
        self.offset_calculation_deque = collections.deque(maxlen=5)
        self.offset = None
        
        self.monotonic_correction = MonotonicSequenceModuloCorrection(2**16)
    
    def calculate_offset(self, timestamps):
        if len(timestamps):
            latest_timestamp = timestamps[-1]
            latest_offset = zephyr.time() - latest_timestamp
            
            self.instantaneous_offset_deque.append(latest_offset)
            self.offset_calculation_deque.append(min(self.instantaneous_offset_deque))
            self.offset = average(self.offset_calculation_deque)
    
    def get_new_heartbeat_timestamps(self, packet):
        history_cache_length = len(packet.heartbeat_milliseconds)
        
        if self.previous_heartbeat_number is not None:
            heartbeat_increment = (packet.heartbeat_number - self.previous_heartbeat_number) % 256
        else:
            heartbeat_increment = 1
        
        if heartbeat_increment > history_cache_length:
            raise CalculationHistoryOverflow("The calculation needs to be reset")
        
        new_heartbeat_timestamps = packet.heartbeat_milliseconds[:heartbeat_increment][::-1]
        return new_heartbeat_timestamps
    
    def process(self, packet):
        new_cyclical_millisecond_timestamps = self.get_new_heartbeat_timestamps(packet)
        
        new_relative_timestamps = [self.monotonic_correction.process(timestamp) / 1000.0
                                   for timestamp in new_cyclical_millisecond_timestamps]
        
        self.calculate_offset(new_relative_timestamps)
        
        for relative_timestamp in new_relative_timestamps:
            timestamp = relative_timestamp + self.offset
            
            if self.previous_timestamp is not None:
                heartbeat_interval = timestamp - self.previous_timestamp
                yield timestamp, heartbeat_interval
            
            self.previous_timestamp = timestamp
        
        self.previous_heartbeat_number = packet.heartbeat_number


class HxMPacketAnalysis:
    def __init__(self, event_callbacks):
        self.event_callbacks = event_callbacks
        self.heartbeat_analysis = RelativeHeartbeatTimestampAnalysis()
    
    def handle_packet(self, packet):
        if isinstance(packet, zephyr.message.HxMMessage):
            current_timestamp = zephyr.time()
            
            try:
                results = list(self.heartbeat_analysis.process(packet))
            except CalculationHistoryOverflow:
                self.heartbeat_analysis = RelativeHeartbeatTimestampAnalysis()
                results = list(self.heartbeat_analysis.process(packet))
            
            for timestamp, heartbeat_interval in results:
                for event_callback in self.event_callbacks:
                    event_callback("heartbeat_interval", (timestamp, heartbeat_interval))
            
            for event_callback in self.event_callbacks:
                event_callback("heart_rate", (current_timestamp, packet.heart_rate))
                event_callback("activity", (current_timestamp, packet.speed / 3.0))
                event_callback("strides", (current_timestamp, packet.strides))
