
import zephyr.message
import zephyr.connection
import zephyr.signal
import zephyr.rr_event

import plots

def main():
    input_file = open("../test_data/120-second-bt-stream.dat", "rb")
    
    signal_collector = zephyr.rr_event.SignalCollectorWithRRProcessing()
    signal_receiver = zephyr.signal.SignalMessageParser(signal_collector.handle_signal)
    connection = zephyr.connection.Connection(input_file, signal_receiver.handle_message)
    
    while connection.read_and_handle_bytes(1):
        pass
    
    plots.visualize_measurements(signal_collector)


if __name__ == "__main__":
    main()
