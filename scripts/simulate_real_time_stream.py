
import threading
import time
import collections
import numpy
import matplotlib.pyplot

import zephyr
from zephyr.collector import MeasurementCollector
from zephyr.bioharness import BioHarnessSignalAnalysis, BioHarnessPacketHandler
from zephyr.delayed_stream import DelayedRealTimeStream
from zephyr.message import MessagePayloadParser
from zephyr.testing import FilePacketSimulator, test_data_dir
from zephyr.visualization import VisualizationWindow


def callback(value_name, value):
    if value_name == "rr_event":
        print "                      ",
        print "%020s %s" % (value_name, value)


def main():
    zephyr.configure_root_logger()
    
    collector = MeasurementCollector()
    rr_signal_analysis = BioHarnessSignalAnalysis([], [collector.handle_event])
    signal_packet_handlers = [collector.handle_signal, rr_signal_analysis.handle_signal]
    
    signal_packet_handler = BioHarnessPacketHandler(signal_packet_handlers, [collector.handle_event])
    
    payload_parser = MessagePayloadParser(signal_packet_handler.handle_packet)
    
    delayed_stream_thread = DelayedRealTimeStream(collector, callback)
    
    simulation_thread = FilePacketSimulator(test_data_dir + "/120-second-bt-stream.dat",
                                            test_data_dir + "/120-second-bt-stream-timing.csv",
                                            payload_parser.handle_message)
    
    delayed_stream_thread.start()
    simulation_thread.start()
    
    visualization = VisualizationWindow(collector)
    visualization.show()
    
    simulation_thread.terminate()
    simulation_thread.join()
    
    delayed_stream_thread.terminate()
    delayed_stream_thread.join()


if __name__ == "__main__":
    main()
