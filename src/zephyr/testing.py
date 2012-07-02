
import time
import csv
import os
import threading

import zephyr.protocol


test_data_dir = os.path.join(os.path.split(os.path.split(os.path.split(__file__)[0])[0])[0], "test_data")


class FilePacketSimulator(threading.Thread):
    def __init__(self, stream_data_path, timing_data_path, packet_handler, sleeping=True):
        threading.Thread.__init__(self)
        
        self.stream_data_path = stream_data_path
        self.timing_data_path = timing_data_path
        self.packet_handler = packet_handler
        self.sleeping = sleeping
        
        self.terminated = False
    
    def terminate(self):
        self.terminated = True
    
    def run(self):
        input_file = open(self.stream_data_path, "rb")
        timings = list(csv.reader(open(self.timing_data_path)))
        
        start_time = zephyr.time()
        first_timestamp = float(timings[0][0])
        timestamp_correction = start_time - first_timestamp
        
        connection = zephyr.protocol.Protocol(input_file, self.packet_handler)
        
        bytes_read = 0
        
        for chunk_timestamp_string, chunk_cumulative_byte_count_string in timings:
            chunk_timestamp = float(chunk_timestamp_string) + timestamp_correction
            chunk_cumulative_byte_count = int(chunk_cumulative_byte_count_string)
            
            time_to_sleep = chunk_timestamp - zephyr.time()
            
            if self.sleeping and time_to_sleep > 0:
                time.sleep(time_to_sleep)
            
            if self.terminated:
                break
            
            bytes_to_read = chunk_cumulative_byte_count - bytes_read
            for i in range(bytes_to_read):
                connection.read_and_handle_byte()
            
            bytes_read = chunk_cumulative_byte_count


def visualize_measurements(signal_collector):
    import numpy
    import pylab
    
    
    ax1 = pylab.subplot(4,1,1)
    ax2 = pylab.subplot(4,1,2,sharex=ax1)
    ax3 = pylab.subplot(4,1,3,sharex=ax1)
    ax4 = pylab.subplot(4,1,4,sharex=ax1)
    
    
    breathing_stream_history = signal_collector.get_signal_stream_history("breathing")
    for breathing_stream in breathing_stream_history.get_signal_streams():
        breathing_x_values = numpy.arange(len(breathing_stream.samples), dtype=float)
        breathing_x_values /= breathing_stream.samplerate
        breathing_x_values += breathing_stream.start_timestamp
        ax1.plot(breathing_x_values, breathing_stream.samples)
    
    ecg_stream_history = signal_collector.get_signal_stream_history("ecg")
    for ecg_stream in ecg_stream_history.get_signal_streams():
        ecg_x_values = numpy.arange(len(ecg_stream.samples), dtype=float)
        ecg_x_values /= ecg_stream.samplerate
        ecg_x_values += ecg_stream.start_timestamp
        ax2.plot(ecg_x_values, ecg_stream.samples)
    
    acceleration_stream_history = signal_collector.get_signal_stream_history("acceleration")
    for acceleration_stream in acceleration_stream_history.get_signal_streams():
        acceleration_x_values = numpy.arange(len(acceleration_stream.samples), dtype=float)
        acceleration_x_values /= acceleration_stream.samplerate
        acceleration_x_values += acceleration_stream.start_timestamp
        ax3.plot(acceleration_x_values, numpy.array(acceleration_stream.samples))
    
    
    heartbeat_interval_stream = signal_collector.get_event_stream("heartbeat_interval")
    heartbeat_interval_timestamps, heartbeat_intervals = zip(*heartbeat_interval_stream)
    ax4.plot(heartbeat_interval_timestamps, heartbeat_intervals, "+-")
    
    ax4.set_ylim((0, 1.5))
    
    pylab.show()
