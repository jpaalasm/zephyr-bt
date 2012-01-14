
import serial
import time

import zephyr.message
import zephyr.connection

def main():
    ser = serial.Serial(23)
    connection = zephyr.connection.Connection(ser, None)
    
    connection.send_message(0x15, [1])
    connection.send_message(0x16, [1])
    connection.send_message(0x19, [1])
    connection.send_message(0x1E, [1])
    
    parts = []
    
    start_time = time.time()
    
    while time.time() < start_time + 120:
        chunk = ser.read(100)
        print repr(chunk)
        parts.append(chunk)
    
    received_data = "".join(parts)
    
    file("../test_data/120-second-bt-stream.dat", "wb").write(received_data)


if __name__ == "__main__":
    main()
