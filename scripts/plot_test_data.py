
import time

import zephyr.events
import zephyr.testing

def main():
    signal_collector = zephyr.events.SignalCollectorWithEventProcessing(True)
    signal_receiver = zephyr.signal.SignalMessageParser(signal_collector.handle_packet)
    zephyr.testing.simulate_packets_from_file("../test_data/120-second-bt-stream.dat", "../test_data/120-second-bt-stream-timing.csv", signal_receiver.handle_message, False)
    zephyr.testing.visualize_measurements(signal_collector)

if __name__ == "__main__":
    main()
