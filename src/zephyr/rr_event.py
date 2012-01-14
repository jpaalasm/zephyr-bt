
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
    def __init__(self, rr_samplerate):
        zephyr.signal.SignalCollector.__init__(self)
        self.rr_event_parser = RREventParser(rr_samplerate)
        self.rr_events = []
    
    def handle_signal(self, signal_type, signal_values, message_timestamp):
        zephyr.signal.SignalCollector.handle_signal(self, signal_type, signal_values, message_timestamp)
        
        if signal_type == "rr":
            rr_signal_start_timestamp = self.signal_streams["rr"].start_timestamp
            for relative_rr_event_timestamp, rr_event_value in self.rr_event_parser.handle_values(signal_values):
                rr_event_timestamp = relative_rr_event_timestamp + rr_signal_start_timestamp
                
                self.rr_events.append((rr_event_timestamp, rr_event_value))
