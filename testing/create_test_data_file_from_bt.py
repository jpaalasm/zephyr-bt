
import serial
import time
import platform
import csv
import threading

import zephyr.protocol
import zephyr.message


def callback(x):
    print x


def reading_thread(protocol):
    start_time = time.time()
    
    while time.time() < start_time + 120:
        protocol.read_and_handle_byte()


def create_data_files(input_definitions):
    threads = []
    
    try:
        for serial_i, (serial_port, enable_channels) in enumerate(input_definitions):
            payload_parser = zephyr.message.MessagePayloadParser([callback])
            
            ser = serial.Serial(serial_port)
            protocol = zephyr.protocol.BioHarnessProtocol(ser, payload_parser.handle_message, "../test_data/120-second-bt-stream-%d" % serial_i)
            
            if enable_channels:
                protocol.enable_periodic_packets()
            
            thread = threading.Thread(target=reading_thread, args=(protocol,))
            threads.append(thread)
            thread.start()
    
    finally:
        for thread in threads:
            thread.join()


def main():
    create_data_files([(29, False), (30, True)])


if __name__ == "__main__":
    main()
