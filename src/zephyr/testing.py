
import time
import csv
import os

import zephyr.protocol
import zephyr.signal


test_data_dir = os.path.join(os.path.split(os.path.split(os.path.split(__file__)[0])[0])[0], "test_data")


def simulate_signal_packets_from_file(stream_data_path, timing_data_path, packet_handler, sleeping=True):
    signal_receiver = zephyr.signal.SignalMessageParser(packet_handler)
    simulate_packets_from_file(stream_data_path, timing_data_path, signal_receiver.handle_message, sleeping)


def simulate_packets_from_file(stream_data_path, timing_data_path, packet_handler, sleeping=True):
    input_file = open(stream_data_path, "rb")
    timings = csv.reader(open(timing_data_path))
    
    connection = zephyr.protocol.Protocol(input_file, packet_handler)
    
    start_time = time.time()
    
    bytes_read = 0
    
    for chunk_timestamp_string, chunk_cumulative_byte_count_string in timings:
        chunk_timestamp = float(chunk_timestamp_string)
        chunk_cumulative_byte_count = int(chunk_cumulative_byte_count_string)
        
        time_to_sleep = chunk_timestamp - (time.time() - start_time)
        
        if sleeping and time_to_sleep > 0:
            time.sleep(time_to_sleep)
        
        bytes_to_read = chunk_cumulative_byte_count - bytes_read
        connection.read_and_handle_bytes(bytes_to_read)
        bytes_read = chunk_cumulative_byte_count


def visualize_measurements(signal_collector):
    import numpy
    import pylab
    
    rr_events_array = numpy.array(signal_collector.get_event_stream("rr_event"))
    
    acceleration_start_timestamp, acceleration_samplerate, acceleration_signal = signal_collector.get_signal_stream("acceleration")
    breathing_start_timestamp, breathing_samplerate, breathing_signal = signal_collector.get_signal_stream("breathing")
    ecg_start_timestamp, ecg_samplerate, ecg_signal = signal_collector.get_signal_stream("ecg")
    
    ax1 = pylab.subplot(4,1,1)
    ax2 = pylab.subplot(4,1,2,sharex=ax1)
    ax3 = pylab.subplot(4,1,3,sharex=ax1)
    ax4 = pylab.subplot(4,1,4,sharex=ax1)
    
    breathing_x_values = numpy.arange(len(breathing_signal), dtype=float)
    breathing_x_values /= breathing_samplerate
    breathing_x_values += breathing_start_timestamp
    
    acceleration_x_values = numpy.arange(len(acceleration_signal), dtype=float)
    acceleration_x_values /= acceleration_samplerate
    acceleration_x_values += acceleration_start_timestamp
    
    ecg_x_values = numpy.arange(len(ecg_signal), dtype=float)
    ecg_x_values /= ecg_samplerate
    ecg_x_values += ecg_start_timestamp
    
    ax1.plot(breathing_x_values, breathing_signal)
    ax2.plot(ecg_x_values, ecg_signal)
    ax3.plot(acceleration_x_values, numpy.array(acceleration_signal))
    ax4.plot(rr_events_array[:, 0], rr_events_array[:, 1], "+")
    
    ax4.set_ylim((0, 1.5))
    
    pylab.show()
