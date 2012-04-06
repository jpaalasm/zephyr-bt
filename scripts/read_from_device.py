
import serial
import time
import platform

import zephyr.message
import zephyr.protocol
import zephyr.signal
import zephyr.rr_event
import zephyr.delayed_stream
import zephyr.testing

def callback(value_name, value):
    if value_name == "acceleration":
        print ["%010s" % ("%1.3f" % v) for v in value]

def main():
    zephyr.configure_root_logger()
    
    serial_port_dict = {"Darwin": "/dev/cu.BHBHT001931-iSerialPort1",
                        "Windows": 23}
    
    serial_port = serial_port_dict[platform.system()]
    ser = serial.Serial(serial_port)
    
    signal_collector = zephyr.rr_event.SignalCollectorWithRRProcessing()
    signal_receiver = zephyr.signal.SignalMessageParser(signal_collector.handle_packet)
    protocol = zephyr.protocol.BioHarnessProtocol(ser, signal_receiver.handle_message)
    
    stream_thread = zephyr.delayed_stream.DelayedRealTimeStream(signal_collector, callback)
    stream_thread.start()
    
    protocol.enable_periodic_packets()
    protocol.read_and_handle_forever()
    
    stream_thread.terminate()
    stream_thread.join()
    
    zephyr.testing.visualize_measurements(signal_collector)


if __name__ == "__main__":
    main()
