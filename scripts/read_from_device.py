
import serial
import time
import platform
import threading

import zephyr.message
import zephyr.protocol
import zephyr.signal
import zephyr.events
import zephyr.delayed_stream
import zephyr.testing


def callback(value_name, value):
    if value_name == "acceleration":
        print ["%010s" % ("%1.3f" % v) for v in value]

def main():
    zephyr.configure_root_logger()
    
    serial_port_dict = {"Darwin": "/dev/cu.BHBHT001931-iSerialPort1",
                        "Windows": 25}
    
    serial_port = serial_port_dict[platform.system()]
    ser = serial.Serial(serial_port)
    
    
    collector = MeasurementCollector()
    rr_signal_analysis = BioHarnessSignalAnalysis([], [collector.handle_event])
    signal_packet_handlers = [collector.handle_signal, rr_signal_analysis.handle_signal]
    
    signal_packet_handler = BioHarnessPacketHandler(signal_packet_handlers, [collector.handle_event])
    
    payload_parser = MessagePayloadParser(signal_packet_handler.handle_packet)
    
    delayed_stream_thread = DelayedRealTimeStream(collector, callback)
    
    protocol = zephyr.protocol.BioHarnessProtocol(ser, payload_parser.handle_message)
    protocol.enable_periodic_packets()
    
    delayed_stream_thread.start()
    
    protocol.read_and_handle_forever()
    
    stream_thread.terminate()
    stream_thread.join()


if __name__ == "__main__":
    main()
