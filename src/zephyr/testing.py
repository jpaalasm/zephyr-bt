
import time

import zephyr.connection
import zephyr.signal


def simulate_signal_packets_from_file(bt_stream_data_file, packet_handler):
    input_file = open(bt_stream_data_file, "rb")
    
    signal_packets = []
    
    signal_receiver = zephyr.signal.SignalMessageParser(signal_packets.append)
    connection = zephyr.connection.Connection(input_file, signal_receiver.handle_message)
    
    while connection.read_and_handle_bytes(1):
        pass
    
    first_message_timestamp = signal_packets[0].timestamp
    
    timestamp_correction = time.time() - first_message_timestamp
    
    for packet in signal_packets:
        timestamp_corrected_packet = packet._replace(timestamp=packet.timestamp + timestamp_correction)
        
        while timestamp_corrected_packet.timestamp > time.time():
            time.sleep(0.01)
        
        packet_handler(timestamp_corrected_packet)


def visualize_measurements(signal_collector):
    import numpy
    import pylab
    
    rr_events_array = numpy.array(signal_collector.rr_events)
    
    acceleration_start_timestamp, acceleration_samplerate, acceleration_signal = signal_collector.signal_streams["acceleration"]
    breathing_start_timestamp, breathing_samplerate, breathing_signal = signal_collector.signal_streams["breathing"]
    
    ax1 = pylab.subplot(3,1,1)
    ax3 = pylab.subplot(3,1,2,sharex=ax1)
    ax4 = pylab.subplot(3,1,3,sharex=ax1)
    
    breathing_x_values = numpy.arange(len(breathing_signal), dtype=float)
    breathing_x_values /= breathing_samplerate
    breathing_x_values += breathing_start_timestamp
    
    acceleration_x_values = numpy.arange(len(acceleration_signal), dtype=float)
    acceleration_x_values /= acceleration_samplerate
    acceleration_x_values += acceleration_start_timestamp
    
    ax1.plot(breathing_x_values, breathing_signal)
    ax3.plot(acceleration_x_values, numpy.array(acceleration_signal))
    ax4.plot(rr_events_array[:, 0], rr_events_array[:, 1], "+")
    
    ax4.set_ylim((0, 1.5))
    
    pylab.show()
