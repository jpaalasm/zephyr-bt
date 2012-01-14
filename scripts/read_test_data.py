
import serial

import zephyr.message
import zephyr.connection
import zephyr.signal


def main():
    signal_receiver = zephyr.signal.SignalReceiver()
    
    input_file = open("../test_data/120-second-bt-stream.dat", "rb")
    
    connection = zephyr.connection.Connection(input_file, signal_receiver.handle_message)
    
    while connection.read_and_handle_bytes(1):
        pass


if __name__ == "__main__":
    main()
