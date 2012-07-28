
import serial
import platform

import zephyr
from zephyr.collector import MeasurementCollector
from zephyr.bioharness import BioHarnessSignalAnalysis, BioHarnessPacketHandler
from zephyr.delayed_stream import DelayedRealTimeStream
from zephyr.message import MessagePayloadParser
from zephyr.protocol import BioHarnessProtocol


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
    
    delayed_stream_thread = DelayedRealTimeStream(collector, [callback], 1.2)
    
    protocol = BioHarnessProtocol(ser, payload_parser.handle_message)
    protocol.enable_periodic_packets()
    
    delayed_stream_thread.start()
    
    protocol.run()
    
    delayed_stream_thread.terminate()
    delayed_stream_thread.join()


if __name__ == "__main__":
    main()
