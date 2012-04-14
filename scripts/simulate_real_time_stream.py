
import threading
import time
import collections
import numpy
import matplotlib.pyplot

import zephyr.rr_event
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
    
    signal_collector = zephyr.rr_event.SignalCollectorWithEventProcessing()
    
    stream_thread = zephyr.delayed_stream.DelayedRealTimeStream(signal_collector, callback)
    stream_thread.start()
    
    data_dir = zephyr.testing.test_data_dir
    
    simulation_thread = threading.Thread(target=zephyr.testing.simulate_signal_packets_from_file,
                                         args=(data_dir + "/120-second-bt-stream.dat",
                                               data_dir + "/120-second-bt-stream-timing.csv",
                                               stream_thread.handle_packet))
    simulation_thread.start()
    
    visualization = zephyr.visualization.VisualizationWindow(signal_collector)
    visualization.run()
    
    simulation_thread.join()
    
    stream_thread.terminate()
    stream_thread.join()


if __name__ == "__main__":
    main()
