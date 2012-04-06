
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
    
    callback = lambda x: None
    protocol = zephyr.protocol.Protocol(ser, callback, "../test_data/120-second-bt-stream")
    protocol.enable_signals()
    
    start_time = time.time()
    while time.time() < start_time + 120:
        protocol.read_and_handle_bytes(1)


if __name__ == "__main__":
    main()
