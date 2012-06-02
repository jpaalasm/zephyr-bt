
import time

import zephyr.util
from zephyr.collector import MeasurementCollector
from zephyr.bioharness import BioHarnessSignalAnalysis, BioHarnessPacketHandler
from zephyr.message import MessagePayloadParser
from zephyr.testing import FilePacketSimulator, visualize_measurements


def main():
    zephyr.util.DISABLE_CLOCK_DIFFERENCE_ESTIMATION = True
    
    collector = MeasurementCollector()
    rr_signal_analysis = BioHarnessSignalAnalysis([], [collector.handle_event])
    signal_packet_handlers = [collector.handle_signal, rr_signal_analysis.handle_signal]
    
    signal_packet_handler = BioHarnessPacketHandler(signal_packet_handlers, [collector.handle_event])
    
    payload_parser = MessagePayloadParser(signal_packet_handler.handle_packet)
    
    simulation_thread = FilePacketSimulator("../test_data/120-second-bt-stream.dat", "../test_data/120-second-bt-stream-timing.csv", payload_parser.handle_message, False)
    simulation_thread.start()
    simulation_thread.join()
    
    visualize_measurements(collector)

if __name__ == "__main__":
    main()
