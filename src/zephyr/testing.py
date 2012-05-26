
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
        timings = csv.reader(open(self.timing_data_path))
        
        connection = zephyr.protocol.Protocol(input_file, self.packet_handler)
        
        start_time = time.time()
        
        bytes_read = 0
        
        for chunk_timestamp_string, chunk_cumulative_byte_count_string in timings:
            chunk_timestamp = float(chunk_timestamp_string)
            chunk_cumulative_byte_count = int(chunk_cumulative_byte_count_string)
            
            time_to_sleep = chunk_timestamp - (time.time() - start_time)
            
            if self.sleeping and time_to_sleep > 0:
                time.sleep(time_to_sleep)
            
            if self.terminated:
                break
            
            bytes_to_read = chunk_cumulative_byte_count - bytes_read
            connection.read_and_handle_bytes(bytes_to_read)
            bytes_read = chunk_cumulative_byte_count


def visualize_measurements(signal_collector):
    import numpy
    import pylab
    
    acceleration_end_timestamp, acceleration_samplerate, acceleration_signal = signal_collector.get_signal_stream("acceleration")
    breathing_end_timestamp, breathing_samplerate, breathing_signal = signal_collector.get_signal_stream("breathing")
    ecg_end_timestamp, ecg_samplerate, ecg_signal = signal_collector.get_signal_stream("ecg")
    
    ax1 = pylab.subplot(4,1,1)
    ax2 = pylab.subplot(4,1,2,sharex=ax1)
    ax3 = pylab.subplot(4,1,3,sharex=ax1)
    ax4 = pylab.subplot(4,1,4,sharex=ax1)
    
    breathing_x_values = numpy.arange(len(breathing_signal), dtype=float)
    breathing_x_values /= breathing_samplerate
    breathing_x_values += breathing_end_timestamp - len(breathing_signal) / breathing_samplerate
    
    acceleration_x_values = numpy.arange(len(acceleration_signal), dtype=float)
    acceleration_x_values /= acceleration_samplerate
    acceleration_x_values += acceleration_end_timestamp - len(acceleration_signal) / acceleration_samplerate
    
    ecg_x_values = numpy.arange(len(ecg_signal), dtype=float)
    ecg_x_values /= ecg_samplerate
    ecg_x_values += ecg_end_timestamp - len(ecg_signal) / ecg_samplerate
    
    ax1.plot(breathing_x_values, breathing_signal)
    ax2.plot(ecg_x_values, ecg_signal)
    ax3.plot(acceleration_x_values, numpy.array(acceleration_signal))
    
    ax4.set_ylim((0, 1.5))
    
    pylab.show()
