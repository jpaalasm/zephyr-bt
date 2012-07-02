
import threading
import collections
import time

import zephyr

class DelayedRealTimeStream(threading.Thread):
    def __init__(self, signal_collector, callbacks, delay=2.0):
        threading.Thread.__init__(self)
        self.signal_collector = signal_collector
        self.callbacks = callbacks
        self.delay = delay
        
        self.stream_output_positions = collections.defaultdict(lambda: 0)
        
        self.terminate_requested = False
    
    def terminate(self):
        self.terminate_requested = True
    
    def run(self):
        # Wait so that all signal streams have been initialized
        time.sleep(self.delay + 1.0)
        
        while not self.terminate_requested:
            delayed_current_time = zephyr.time() - self.delay
            
            for stream_name, stream_history in self.signal_collector.iterate_signal_stream_histories():
                from_sample = self.stream_output_positions[stream_name]
                for sample in stream_history.iterate_samples(from_sample, delayed_current_time):
                    self.stream_output_positions[stream_name] += 1
                    for callback in self.callbacks:
                        callback(stream_name, sample)
            
            for stream_name, stream in self.signal_collector.iterate_event_streams():
                output_position = self.stream_output_positions[stream_name]
                
                if len(stream) > output_position:
                    event_timestamp, event_value = stream[output_position]
                    
                    if event_timestamp <= delayed_current_time:
                        self.stream_output_positions[stream_name] += 1
                        for callback in self.callbacks:
                            callback(stream_name, event_value)
            
            time.sleep(0.01)
