
import threading
import collections
import itertools
import time

import zephyr

class DelayedRealTimeStream(threading.Thread):
    def __init__(self, signal_collector, callbacks, delay):
        threading.Thread.__init__(self)
        self.signal_collector = signal_collector
        self.callbacks = callbacks
        self.delay = delay
        
        self.stream_output_positions = collections.defaultdict(lambda: 0)
        
        self.terminate_requested = False
    
    def terminate(self):
        self.terminate_requested = True
    
    def run(self):
        while not self.terminate_requested:
            delayed_current_time = zephyr.time() - self.delay
            
            all_streams = itertools.chain(self.signal_collector.iterate_signal_stream_histories(),
                                          self.signal_collector.iterate_event_streams())
            
            for signal_stream_name, signal_stream_history in all_streams:
                from_sample = self.stream_output_positions[signal_stream_name]
                for sample in signal_stream_history.iterate_samples(from_sample, delayed_current_time):
                    self.stream_output_positions[signal_stream_name] += 1
                    for callback in self.callbacks:
                        callback(signal_stream_name, sample)
            
            time.sleep(0.01)
