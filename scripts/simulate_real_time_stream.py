
import zephyr
from zephyr.collector import MeasurementCollector
from zephyr.bioharness import BioHarnessSignalAnalysis, BioHarnessPacketHandler
from zephyr.delayed_stream import DelayedRealTimeStream
from zephyr.message import MessagePayloadParser
from zephyr.testing import test_data_dir, TimedVirtualSerial
from zephyr.protocol import BioHarnessProtocol


def callback(value_name, value):
    print value_name, value

def main():
    zephyr.configure_root_logger()
    
    ser = TimedVirtualSerial(test_data_dir + "/120-second-bt-stream.dat",
                             test_data_dir + "/120-second-bt-stream-timing.csv")
    
    collector = MeasurementCollector()
    rr_signal_analysis = BioHarnessSignalAnalysis([], [collector.handle_event])
    signal_packet_handlers = [collector.handle_signal, rr_signal_analysis.handle_signal]
    
    signal_packet_handler = BioHarnessPacketHandler(signal_packet_handlers, [collector.handle_event])
    
    payload_parser = MessagePayloadParser([signal_packet_handler.handle_packet])
    
    delayed_stream_thread = DelayedRealTimeStream(collector, [callback], 1.2)
    
    protocol = BioHarnessProtocol(ser, payload_parser.handle_message)
    protocol.enable_periodic_packets()
    
    delayed_stream_thread.start()
    
    try:
        protocol.run()
    except EOFError:
        pass
    
    delayed_stream_thread.terminate()
    delayed_stream_thread.join()


if __name__ == "__main__":
    main()
