
import zephyr.signal


def sign(value):
    return cmp(value, 0)


class SignalCollectorWithEventProcessing(zephyr.signal.SignalCollector):
    def __init__(self, clock_difference_correction=True):
        zephyr.signal.SignalCollector.__init__(self, clock_difference_correction)
        
        self.latest_value_sign = 0
        self._event_streams = {}
        self.summary_packets = []
        
        self.initialize_event_stream("rr_event")
    
    def initialize_event_stream(self, stream_name):
        assert stream_name not in self._event_streams
        self._event_streams[stream_name] = []
    
    def append_to_event_stream(self, stream_name, value):
        self._event_streams[stream_name].append(value)
    
    def get_event_stream(self, stream_type):
        event_stream = self._event_streams[stream_type]
        return event_stream
    
    def iterate_event_streams(self):
        return self._event_streams.iteritems()
    
    def handle_packet(self, signal_packet):
        zephyr.signal.SignalCollector.handle_packet(self, signal_packet)
        
        if isinstance(signal_packet, zephyr.message.SummaryMessage):
            self.summary_packets.append(signal_packet)
        
        if isinstance(signal_packet, zephyr.message.SignalPacket) and signal_packet.type == "rr":
            signal_stream = self.get_signal_stream("rr")
            
            samples_received_before_this_packet = len(signal_stream.signal_values) - len(signal_packet.signal_values)
            
            for sample_index, rr_value in enumerate(signal_packet.signal_values, start=samples_received_before_this_packet):
                rr_value_sign = sign(rr_value)
                if rr_value_sign != self.latest_value_sign:
                    rr_timestamp = sample_index / signal_stream.samplerate + signal_stream.start_timestamp
                    self.append_to_event_stream("rr_event", (rr_timestamp, abs(rr_value)))
                self.latest_value_sign = rr_value_sign
