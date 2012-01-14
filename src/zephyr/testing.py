
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
