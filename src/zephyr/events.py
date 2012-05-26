
import zephyr.signal


def sign(value):
    return cmp(value, 0)


class SignalCollectorWithEventProcessing(zephyr.signal.SignalCollector):
    def __init__(self):
        zephyr.signal.SignalCollector.__init__(self)
        
        self.latest_rr_value_sign = 0
        self._event_streams = {}
        
        self.initialize_event_stream("activity")
        self.initialize_event_stream("heartbeat_interval")
        self.initialize_event_stream("heart_rate")
        self.initialize_event_stream("respiration_rate")
    
    def initialize_event_stream(self, stream_name):
        assert stream_name not in self._event_streams
        self._event_streams[stream_name] = []
    
    def append_to_event_stream(self, stream_name, value):
        self._event_streams[stream_name].append(value)
    
    def get_event_stream(self, stream_type):
        event_stream = self._event_streams[stream_type]
        return event_stream
    
    def iterate_event_streams(self):
        return [(key, self.get_event_stream(key))
                 for key in self._event_streams]
    
    def handle_packet(self, message):
        zephyr.signal.SignalCollector.handle_packet(self, message)
        
        if isinstance(message, zephyr.message.SummaryMessage):
            corrected_timestamp = self.clock_difference_correction.estimate_and_correct_timestamp(message.timestamp, "summary")
            
            self.append_to_event_stream("activity", (corrected_timestamp, message.activity))
            self.append_to_event_stream("heart_rate", (corrected_timestamp, message.heart_rate))
            self.append_to_event_stream("respiration_rate", (corrected_timestamp, message.respiration_rate))
        
        if isinstance(message, zephyr.message.SignalPacket) and message.type == "rr":
            signal_stream = self.get_signal_stream("rr")
            
            samples_received_before_this_packet = len(signal_stream.signal_values) - len(message.signal_values)
            
            for rr_timestamp, rr_value in self.iterate_samples_with_timing("rr", samples_received_before_this_packet):
                rr_value_sign = sign(rr_value)
                if rr_value_sign != self.latest_rr_value_sign:
                    heartbeat_interval = abs(rr_value)
                    self.append_to_event_stream("heartbeat_interval", (rr_timestamp, heartbeat_interval))
                self.latest_rr_value_sign = rr_value_sign
