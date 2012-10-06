
import zephyr.util
from zephyr.collector import MeasurementCollector
from zephyr.bioharness import BioHarnessSignalAnalysis, BioHarnessPacketHandler
from zephyr.message import MessagePayloadParser
from zephyr.testing import visualize_measurements, test_data_dir, VirtualSerial
from zephyr.protocol import Protocol, MessageFrameParser


def main():
    zephyr.util.DISABLE_CLOCK_DIFFERENCE_ESTIMATION = True
    
    collector = MeasurementCollector()
    rr_signal_analysis = BioHarnessSignalAnalysis([], [collector.handle_event])
    signal_packet_handlers = [collector.handle_signal, rr_signal_analysis.handle_signal]
    
    signal_packet_handler = BioHarnessPacketHandler(signal_packet_handlers, [collector.handle_event])
    
    payload_parser = MessagePayloadParser([signal_packet_handler.handle_packet])
    
    message_parser = MessageFrameParser(payload_parser.handle_message)
    
    ser = VirtualSerial(test_data_dir + "/120-second-bt-stream.dat")
    
    protocol = Protocol(ser, [message_parser.parse_data])
    
    try:
        protocol.run()
    except EOFError:
        pass
    
    visualize_measurements(collector)

if __name__ == "__main__":
    main()
