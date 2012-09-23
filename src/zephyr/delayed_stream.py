
import threading
import collections
import itertools
import time

import zephyr

class DelayedRealTimeStream(threading.Thread):
    def __init__(self, signal_collector, callbacks, default_delay, specific_delays={}):
        threading.Thread.__init__(self)
        self.signal_collector = signal_collector
        self.callbacks = callbacks
        self.default_delay = default_delay
        self.specific_delays = specific_delays
        
        self.stream_output_positions = collections.defaultdict(lambda: 0)
        
        self.terminate_requested = False
    
    def add_callback(self, callback):
        self.callbacks.append(callback)
    
    def terminate(self):
        self.terminate_requested = True
    
    def run(self):
        while not self.terminate_requested:
            now = zephyr.time()
            all_streams = itertools.chain(self.signal_collector.iterate_signal_stream_histories(),
                                          self.signal_collector.iterate_event_streams())
            
            for signal_stream_name, signal_stream_history in all_streams:
                delay = self.specific_delays.get(signal_stream_name, self.default_delay)
                
                delayed_current_time = now - delay
                
                from_sample = self.stream_output_positions[signal_stream_name]
                for sample in signal_stream_history.iterate_samples(from_sample, delayed_current_time):
                    self.stream_output_positions[signal_stream_name] += 1
                    for callback in self.callbacks:
                        callback(signal_stream_name, sample)
            
            time.sleep(0.01)
