
import serial
import time

import zephyr.message
import zephyr.protocol
import zephyr.signal
import zephyr.rr_event
import zephyr.testing

def callback(value_name, value):
    if value_name == "acceleration":
        print ["%010s" % ("%1.3f" % v) for v in value]

def main():
    ser = serial.Serial("/dev/cu.BHBHT001931-iSerialPort1", timeout=0.1) #OS X (Dave's machine)
    #ser = serial.Serial(23) #Windows (Joonas' machine)
    
    signal_collector = zephyr.rr_event.SignalCollectorWithRRProcessing()
    signal_receiver = zephyr.signal.SignalMessageParser(signal_collector.handle_packet)
    protocol = zephyr.protocol.Protocol(ser, signal_receiver.handle_message)
    
    protocol.enable_signals()
    
    stream_thread = zephyr.rr_event.DelayedRealTimeStream(signal_collector, callback)
    stream_thread.start()
    
    start_time = time.time()
    
    while time.time() < start_time + 120:
        protocol.read_and_handle_bytes(1)
    
    stream_thread.terminate()
    stream_thread.join()
    
    zephyr.testing.visualize_measurements(signal_collector)


if __name__ == "__main__":
    main()
