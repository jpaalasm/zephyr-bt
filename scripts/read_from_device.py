
import serial

import zephyr.message
import zephyr.connection
import zephyr.signal

def dummy_handler(*args):
    print "Got:", args

def main():
    signal_receiver = zephyr.signal.SignalMessageParser(dummy_handler)
    
    ser = serial.Serial("/dev/cu.BHBHT001931-iSerialPort1", timeout=0.1) #OS X (Dave's machine)
    #ser = serial.Serial(23, timeout=0.1) #Windows (Joonas' machine)
    connection = zephyr.connection.Connection(ser, signal_receiver.handle_message)
    
    connection.send_message(0x15, [1])
    connection.send_message(0x16, [1])
    connection.send_message(0x19, [1])
    connection.send_message(0x1E, [1])
    
    while True:
        connection.read_and_handle_bytes(1)


if __name__ == "__main__":
    main()
