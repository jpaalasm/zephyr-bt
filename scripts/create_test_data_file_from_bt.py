
import serial
import time
import platform
import csv

import zephyr.message
import zephyr.protocol

def main():
    serial_port_dict = {"Darwin": "/dev/cu.BHBHT001931-iSerialPort1",
                        "Windows": 23}
    
    serial_port = serial_port_dict[platform.system()]
    ser = serial.Serial(serial_port)
    
    protocol = zephyr.protocol.Protocol(ser, None)
    
    protocol.enable_signals()
    
    start_time = time.time()
    
    recording_time = 120.0
    
    chunks_timing = []
    
    data_file = file("../test_data/120-second-bt-stream.dat", "wb")
    timing_file = file("../test_data/120-second-bt-stream-timing.csv", "wb")
    timing_file_csv_writer = csv.writer(timing_file)
    
    while True:
        time_before = time.time()
        byte = ser.read(1)
        delay = time.time() - time_before
        
        relative_previous_chunk_time = time_before - start_time
        
        data_file_position = data_file.tell()
        
        if delay > 0.01 and data_file_position:
            timing_file_csv_writer.writerow((relative_previous_chunk_time, data_file_position))
            print relative_previous_chunk_time, data_file_position
        
        if relative_previous_chunk_time > recording_time:
            break
        
        data_file.write(byte)
    
    data_file.close()
    timing_file.close()


if __name__ == "__main__":
    main()
