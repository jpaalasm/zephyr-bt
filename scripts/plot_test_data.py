
import time

import zephyr.rr_event
import zephyr.testing

def main():
    signal_collector = zephyr.rr_event.SignalCollectorWithEventProcessing(False)
    zephyr.testing.simulate_signal_packets_from_file("../test_data/120-second-bt-stream.dat", "../test_data/120-second-bt-stream-timing.csv", signal_collector.handle_packet, False)
    zephyr.testing.visualize_measurements(signal_collector)

if __name__ == "__main__":
    main()
