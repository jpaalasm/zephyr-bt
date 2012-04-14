
import zephyr.signal

def sign(value):
    return cmp(value, 0)

class SignalCollectorWithRRProcessing(zephyr.signal.SignalCollector):
    def __init__(self, clock_difference_correction=True):
        zephyr.signal.SignalCollector.__init__(self, clock_difference_correction)
        self.initialize_event_stream("rr_event")
        self.latest_value_sign = 0
    
    def handle_packet(self, signal_packet):
        if isinstance(signal_packet, zephyr.message.SignalPacket):
            zephyr.signal.SignalCollector.handle_packet(self, signal_packet)
            
            if signal_packet.type == "rr":
                signal_stream = self.get_signal_stream("rr")
                
                received_values_before_this_packet = len(signal_stream.signal_values) - len(signal_packet.signal_values)
                
                for sample_index, rr_value in enumerate(signal_packet.signal_values, start=received_values_before_this_packet):
                    rr_value_sign = sign(rr_value)
                    if rr_value_sign != self.latest_value_sign:
                        rr_timestamp = sample_index / signal_stream.samplerate + signal_stream.start_timestamp
                        self.append_to_event_stream("rr_event", (rr_timestamp, abs(rr_value)))
                    self.latest_value_sign = rr_value_sign
