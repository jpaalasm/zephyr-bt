
import threading
import time
import collections

import zephyr.rr_event
import zephyr.testing
import zephyr.delayed_stream


def callback(value_name, value):
    if value_name == "rr_event":
        print "                      ",
        print "%020s %s" % (value_name, value)

def cb(m):
    if m.message_id == 0x2B:
        print m.payload

def main():
    zephyr.configure_root_logger()
    
    signal_collector = zephyr.rr_event.SignalCollectorWithRRProcessing()
    
    stream_thread = zephyr.delayed_stream.DelayedRealTimeStream(signal_collector, callback)
    stream_thread.start()
    
    data_dir = zephyr.testing.test_data_dir
    
    try:
        zephyr.testing.simulate_packets_from_file(data_dir + "/120-second-bt-stream.dat",
                                                  data_dir + "/120-second-bt-stream-timing.csv",
                                                  cb)
    finally:
        stream_thread.terminate()
        stream_thread.join()


if __name__ == "__main__":
    main()
