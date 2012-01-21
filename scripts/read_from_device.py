
import serial
import time

import zephyr.message
import zephyr.protocol
import zephyr.signal
import zephyr.rr_event
import zephyr.testing

def main():
    ser = serial.Serial("/dev/cu.BHBHT001931-iSerialPort1", timeout=0.1) #OS X (Dave's machine)
    #ser = serial.Serial(23, timeout=0.1) #Windows (Joonas' machine)
    
    signal_collector = zephyr.rr_event.SignalCollectorWithRRProcessing()
    signal_receiver = zephyr.signal.SignalMessageParser(signal_collector.handle_packet)
    protocol = zephyr.protocol.Prototol(ser, signal_receiver.handle_message)
    
    protocol.send_message(0x15, [1])
    protocol.send_message(0x16, [1])
    protocol.send_message(0x19, [1])
    protocol.send_message(0x1E, [1])
    
    start_time = time.time()
    
    while time.time() < start_time + 30:
        protocol.read_and_handle_bytes(1)
    
    zephyr.testing.visualize_measurements(signal_collector)


if __name__ == "__main__":
    main()
