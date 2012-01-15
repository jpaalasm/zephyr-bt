
import time

import zephyr.rr_event
import zephyr.testing

def main():
    signal_collector = zephyr.rr_event.SignalCollectorWithRRProcessing()
    zephyr.testing.simulate_signal_packets_from_file("../test_data/120-second-bt-stream.dat", signal_collector.handle_packet)
    zephyr.testing.visualize_measurements(signal_collector)


if __name__ == "__main__":
    main()
