
import threading
import time
import collections

import zephyr.rr_event
import zephyr.testing
import zephyr.delayed_stream


def callback(value_name, value):
    print "%020s %s" % (value_name, value)

def main():
    signal_collector = zephyr.rr_event.SignalCollectorWithRRProcessing()
    
    stream_thread = zephyr.delayed_stream.DelayedRealTimeStream(signal_collector, callback)
    stream_thread.start()
    
    data_dir = zephyr.testing.test_data_dir
    
    zephyr.testing.simulate_signal_packets_from_file(data_dir + "/120-second-bt-stream.dat",
                                                     data_dir + "/120-second-bt-stream-timing.json",
                                                     stream_thread.handle_packet)
    
    stream_thread.terminate()
    stream_thread.join()


if __name__ == "__main__":
    main()
