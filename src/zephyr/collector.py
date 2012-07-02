
import collections


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
    
    def iterate_timed_samples(self):
        start_timestamp = self.start_timestamp
        sample_period = 1.0 / self.samplerate
        
        for sample_i, sample in enumerate(self.samples):
            sample_timestamp = start_timestamp + sample_i * sample_period
            yield sample_timestamp, sample


class SignalStreamHistory:
    def __init__(self):
        self._signal_streams = []
    
    def get_total_sample_count(self):
        return sum(len(stream.samples) for stream in self._signal_streams)
    
    def append_stream(self, signal_stream):
        self._signal_streams.append(signal_stream)

    def append_signal_packet(self, signal_packet, starts_new_stream):
        if starts_new_stream or not len(self._signal_streams):
            signal_stream = SignalStream(signal_packet)
            self._signal_streams.append(signal_stream)
        else:
            signal_stream = self._signal_streams[-1]
            signal_stream.append_signal_packet(signal_packet)
    
    def get_signal_streams(self):
        return self._signal_streams
    
    def iterate_samples(self, from_sample_index, to_end_timestamp):
        signal_stream_start_index = 0
        for signal_stream in self._signal_streams:
            sample_count = len(signal_stream.samples)
            next_signal_stream_start_index = signal_stream_start_index + sample_count
            
            if from_sample_index < next_signal_stream_start_index:
                for local_sample_index, (sample_timestamp, sample) in enumerate(signal_stream.iterate_timed_samples()):
                    global_sample_index = signal_stream_start_index + local_sample_index
                    
                    if global_sample_index < from_sample_index:
                        continue
                    elif sample_timestamp > to_end_timestamp:
                        break
                    
                    yield sample
            
            signal_stream_start_index = next_signal_stream_start_index


class MeasurementCollector:
    def __init__(self):
        self._signal_stream_histories = collections.defaultdict(SignalStreamHistory)
        self._event_streams = {}
        
        self.initialize_event_stream("activity")
        self.initialize_event_stream("heart_rate")
        self.initialize_event_stream("respiration_rate")
        
        self.initialize_event_stream("heartbeat_interval")
    
    def get_signal_stream_history(self, stream_type):
        return self._signal_stream_histories[stream_type]
    
    def get_event_stream(self, stream_type):
        return self._event_streams[stream_type]
    
    def iterate_signal_stream_histories(self):
        return self._signal_stream_histories.items()
    
    def iterate_event_streams(self):
        return self._event_streams.items()
    
    def initialize_event_stream(self, stream_name):
        assert stream_name not in self._event_streams
        self._event_streams[stream_name] = []
    
    def handle_signal(self, signal_packet, starts_new_stream):
        signal_stream_history = self._signal_stream_histories[signal_packet.type]
        signal_stream_history.append_signal_packet(signal_packet, starts_new_stream)
    
    def handle_event(self, stream_name, value):
        self._event_streams[stream_name].append(value)
