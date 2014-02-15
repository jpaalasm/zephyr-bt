
import threading
import collections

import zephyr


class EventStream:
    def __init__(self):
        self.events = []
        self.events_cleaned_up = 0
        self.lock = threading.RLock()
    
    def __iter__(self):
        with self.lock:
            return iter(self.events[:])
    
    def __len__(self):
        with self.lock:
            corrected_length = len(self.events) + self.events_cleaned_up
            return corrected_length
    
    def __getitem__(self, index):
        with self.lock:
            assert 0 <= index < len(self)
            assert index >= self.events_cleaned_up
            
            corrected_index = index - self.events_cleaned_up
            return self.events[corrected_index]
    
    def append(self, value):
        with self.lock:
            self.events.append(value)
    
    def clean_up_events_before(self, timestamp_lower_bound):
        with self.lock:
            cutoff_index = 0
            
            for event_timestamp, event_value in self.events: #@UnusedVariable
                if event_timestamp < timestamp_lower_bound:
                    cutoff_index += 1
                else:
                    break
            
            if cutoff_index:
                self.events = self.events[cutoff_index:]
                self.events_cleaned_up += cutoff_index
    
    def iterate_samples(self, from_sample_index, to_end_timestamp):
        sample_index = from_sample_index
        
        while True:
            if len(self) > sample_index:
                event_timestamp, event_value = self[sample_index]
                
                if event_timestamp <= to_end_timestamp:
                    yield event_value
                    sample_index += 1
                    continue
            
            break


class SignalStream:
    def __init__(self, signal_packet):
        self.samplerate = signal_packet.samplerate
        self.samples = []
        self.lock = threading.RLock()
        
        self.end_timestamp = None
        self.append_signal_packet(signal_packet)
    
    def append_signal_packet(self, signal_packet):
        with self.lock:
            assert signal_packet.samplerate == self.samplerate
            
            self.samples.extend(signal_packet.samples)
            self.end_timestamp = signal_packet.timestamp + len(signal_packet.samples) / float(signal_packet.samplerate)
    
    def remove_samples_before(self, timestamp_lower_bound):
        with self.lock:
            samples_to_remove = max(0, int((timestamp_lower_bound - self.start_timestamp) * self.samplerate))
            
            if samples_to_remove:
                self.samples = self.samples[samples_to_remove:]
        
        return samples_to_remove
    
    @property
    def start_timestamp(self):
        return self.end_timestamp - len(self.samples) / float(self.samplerate)
    
    def iterate_timed_samples(self, skip_samples=0):
        with self.lock:
            start_timestamp = self.start_timestamp
            sample_period = 1.0 / self.samplerate
            
            for sample_i, sample in enumerate(self.samples[skip_samples:], start=skip_samples):
                sample_timestamp = start_timestamp + sample_i * sample_period
                yield sample_timestamp, sample


class SignalStreamHistory:
    def __init__(self):
        self._signal_streams = []
        
        self.samples_cleaned_up = 0
    
    def append_signal_packet(self, signal_packet, starts_new_stream):
        if starts_new_stream or not len(self._signal_streams):
            signal_stream = SignalStream(signal_packet)
            self._signal_streams.append(signal_stream)
        else:
            signal_stream = self._signal_streams[-1]
            signal_stream.append_signal_packet(signal_packet)
    
    def get_signal_streams(self):
        return self._signal_streams
    
    def _cleanup_signal_stream(self, signal_stream, timestamp_bound):
        if timestamp_bound >= signal_stream.end_timestamp:
            self._signal_streams.remove(signal_stream)
            samples_removed = len(signal_stream.samples)
        else:
            samples_removed = signal_stream.remove_samples_before(timestamp_bound)
        
        self.samples_cleaned_up += samples_removed
    
    def clean_up_samples_before(self, history_limit):
        for signal_stream in self._signal_streams[:]:
            first_timestamp = signal_stream.start_timestamp
            
            if first_timestamp >= history_limit:
                break
            
            self._cleanup_signal_stream(signal_stream, history_limit)
    
    def iterate_samples(self, from_sample_index, to_end_timestamp):
        from_sample_index = from_sample_index - self.samples_cleaned_up
        
        signal_stream_start_index = 0
        for signal_stream in self._signal_streams:
            sample_count = len(signal_stream.samples)
            next_signal_stream_start_index = signal_stream_start_index + sample_count
            
            if from_sample_index < next_signal_stream_start_index:
                samples_to_skip = max(0, from_sample_index - signal_stream_start_index)
                
                for sample_timestamp, sample in signal_stream.iterate_timed_samples(samples_to_skip):
                    if sample_timestamp > to_end_timestamp:
                        break
                    
                    yield sample
            
            signal_stream_start_index = next_signal_stream_start_index


class MeasurementCollector:
    def __init__(self, history_length_seconds=20.0):
        self._signal_stream_histories = collections.defaultdict(SignalStreamHistory)
        self._event_streams = collections.defaultdict(EventStream)
        
        self.history_length_seconds = history_length_seconds
        self.last_cleanup_time = 0.0
    
    def get_signal_stream_history(self, stream_type):
        return self._signal_stream_histories[stream_type]
    
    def get_event_stream(self, stream_type):
        return self._event_streams[stream_type]
    
    def iterate_signal_stream_histories(self):
        return self._signal_stream_histories.items()
    
    def iterate_event_streams(self):
        return self._event_streams.items()
    
    def handle_signal(self, signal_packet, starts_new_stream):
        signal_stream_history = self._signal_stream_histories[signal_packet.type]
        signal_stream_history.append_signal_packet(signal_packet, starts_new_stream)
        self.cleanup_if_needed()
    
    def handle_event(self, stream_name, value):
        self._event_streams[stream_name].append(value)
        self.cleanup_if_needed()
    
    def cleanup_if_needed(self):
        now = zephyr.time()
        
        if self.last_cleanup_time < now - 5.0:
            history_limit = now - self.history_length_seconds
            for signal_stream_history in self._signal_stream_histories.values():
                signal_stream_history.clean_up_samples_before(history_limit)
            
            for event_stream in self._event_streams.values():
                event_stream.clean_up_events_before(history_limit)
            
            self.last_cleanup_time = now
