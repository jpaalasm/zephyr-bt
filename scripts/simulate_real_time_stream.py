
import threading
import time
import collections
import numpy
import matplotlib.pyplot

import zephyr.events
import zephyr.testing
import zephyr.delayed_stream
import zephyr.message
import zephyr.visualization


def callback(value_name, value):
    if value_name == "rr_event":
        print "                      ",
        print "%020s %s" % (value_name, value)


def main():
    zephyr.configure_root_logger()
    
    signal_collector = zephyr.events.SignalCollectorWithEventProcessing()
    
    stream_thread = zephyr.delayed_stream.DelayedRealTimeStream(signal_collector, callback)
    stream_thread.start()
    
    data_dir = zephyr.testing.test_data_dir
    
    signal_receiver = zephyr.signal.MessagePayloadParser(stream_thread.handle_packet)
    
    simulation_thread = zephyr.testing.FilePacketSimulator(data_dir + "/120-second-bt-stream.dat",
                                                           data_dir + "/120-second-bt-stream-timing.csv",
                                                           signal_receiver.handle_message)
    simulation_thread.start()
    
    visualization = zephyr.visualization.VisualizationWindow(signal_collector)
    visualization.show()
    
    simulation_thread.terminate()
    simulation_thread.join()
    
    stream_thread.terminate()
    stream_thread.join()


if __name__ == "__main__":
    main()
