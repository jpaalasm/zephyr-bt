
import threading
import collections
import time
import logging


class DelayedRealTimeStream(threading.Thread):
    def __init__(self, signal_collector, callback, delay=2.0):
        threading.Thread.__init__(self)
        self.signal_collector = signal_collector
        self.callback = callback
        self.delay = delay
        
        self.stream_progresses = collections.defaultdict(lambda: 0)
        
        self.terminate_requested = False
    
    def terminate(self):
        self.terminate_requested = True
    
    def handle_packet(self, signal_packet):
        self.signal_collector.handle_packet(signal_packet)
    
    def run(self):
        # Wait so that all signal streams have been initialized
        time.sleep(self.delay + 1.0)
        
        while not self.terminate_requested:
            delayed_current_time = time.time() - self.delay
            
            for stream_name, stream in self.signal_collector.iterate_signal_streams():
                stream_sample_index = int((delayed_current_time - stream.start_timestamp) * stream.samplerate)
                
                stream_progress = self.stream_progresses[stream_name]
                
                if stream_sample_index > stream_progress:
                    if stream_sample_index < len(stream.signal_values):
                        delayed_value = stream.signal_values[stream_sample_index]
                        self.callback(stream_name, delayed_value)
                        self.stream_progresses[stream_name] = stream_sample_index
                    else:
                        logging.warning("%1.3f sec of data missing", (stream_sample_index - len(stream.signal_values)) / stream.samplerate)
            
            
            for stream_name, stream in self.signal_collector.iterate_event_streams():
                stream_progress = self.stream_progresses[stream_name]
                
                if len(stream) > stream_progress:
                    event_timestamp, event_value = stream[stream_progress]
                    
                    if event_timestamp <= delayed_current_time:
                        self.callback(stream_name, event_value)
                        self.stream_progresses[stream_name] += 1
            
            time.sleep(0.01)
