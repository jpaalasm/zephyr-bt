
import serial
import time
import platform
import json

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
    
    read_bytes_list = []
    chunks_timing = []
    
    while True:
        time_before = time.time()
        byte = ser.read(1)
        delay = time.time() - time_before
        
        relative_previous_chunk_time = time_before - start_time
        
        if delay > 0.01 and len(read_bytes_list):
            chunks_timing.append((relative_previous_chunk_time, len(read_bytes_list)))
            print chunks_timing[-1]
        
        if relative_previous_chunk_time > recording_time:
            break
        
        read_bytes_list.append(byte)
    
    read_bytes = "".join(read_bytes_list)
    
    file("../test_data/120-second-bt-stream.dat", "wb").write(read_bytes)
    json.dump(chunks_timing, file("../test_data/120-second-bt-stream-timing.json", "w"))


if __name__ == "__main__":
    main()
