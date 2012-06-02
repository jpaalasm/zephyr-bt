

class SignalStream:
    def __init__(self, signal_packet):
        self.samplerate = signal_packet.samplerate
        self.samples = []
        
        self.end_timestamp = None
        self.append_signal_packet(signal_packet)
    
    def append_signal_packet(self, signal_packet):
        assert signal_packet.samplerate == self.samplerate
        
        self.samples.extend(signal_packet.samples)
        self.end_timestamp = signal_packet.timestamp + len(signal_packet.samples) / float(signal_packet.samplerate)
    
    @property
    def start_timestamp(self):
        return self.end_timestamp - len(self.samples) / float(self.samplerate)


class MeasurementCollector:
    def __init__(self):
        self._signal_streams = {}
        self._event_streams = {}
        
        self.initialize_event_stream("activity")
        self.initialize_event_stream("heart_rate")
        self.initialize_event_stream("respiration_rate")
        
        self.initialize_event_stream("heartbeat_interval")
    
    def get_signal_stream(self, stream_type):
        return self._signal_streams[stream_type]
    
    def get_event_stream(self, stream_type):
        return self._event_streams[stream_type]
    
    def iterate_signal_streams(self):
        return self._signal_streams.items()
    
    def iterate_event_streams(self):
        return self._event_streams.items()
    
    def initialize_event_stream(self, stream_name):
        assert stream_name not in self._event_streams
        self._event_streams[stream_name] = []
    
    def handle_signal(self, signal_packet, starts_new_stream):
        if starts_new_stream:
            del self._signal_streams[signal_packet.type]
        
        signal_stream = self._signal_streams.get(signal_packet.type)
        if signal_stream is None:
            signal_stream = SignalStream(signal_packet)
            self._signal_streams[signal_packet.type] = signal_stream
        
        signal_stream.append_signal_packet(signal_packet)
    
    def handle_event(self, stream_name, value):
        self._event_streams[stream_name].append(value)
