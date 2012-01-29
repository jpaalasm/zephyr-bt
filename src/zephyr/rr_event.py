
import zephyr.signal

def sign(value):
    return cmp(value, 0)

class RREventParser:
    def __init__(self, samplerate):
        self.samplerate = float(samplerate)
        self.received_value_count = 0
        self.latest_value_sign = 0
    
    def handle_values(self, values):
        for value in values:
            value_sign = sign(value)
            if value_sign != self.latest_value_sign:
                yield self.received_value_count / self.samplerate, abs(value)
            
            self.received_value_count += 1
            self.latest_value_sign = value_sign

class SignalCollectorWithRRProcessing(zephyr.signal.SignalCollector):
    def __init__(self):
        zephyr.signal.SignalCollector.__init__(self)
        
        self.initialize_event_stream("rr_event")
        self.rr_event_parser = None
    
    def handle_packet(self, signal_packet):
        zephyr.signal.SignalCollector.handle_packet(self, signal_packet)
        
        if signal_packet.type == "rr":
            if self.rr_event_parser is None:
                self.rr_event_parser = RREventParser(signal_packet.samplerate)
            
            rr_signal_start_timestamp = self.signal_streams["rr"].start_timestamp
            for relative_rr_event_timestamp, rr_event_value in self.rr_event_parser.handle_values(signal_packet.signal_values):
                rr_event_timestamp = relative_rr_event_timestamp + rr_signal_start_timestamp
                
                self.event_streams["rr_event"].append((rr_event_timestamp, rr_event_value))
