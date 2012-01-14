
import pylab
import numpy

import zephyr.message
import zephyr.connection
import zephyr.signal
import zephyr.rr_event


def main():
    input_file = open("../test_data/120-second-bt-stream.dat", "rb")
    
    signal_collector = zephyr.rr_event.SignalCollectorWithRRProcessing(18.0)
    signal_receiver = zephyr.signal.SignalMessageParser(signal_collector.handle_signal)
    connection = zephyr.connection.Connection(input_file, signal_receiver.handle_message)
    
    while connection.read_and_handle_bytes(1000):
        pass
    
    rr_events_array = numpy.array(signal_collector.rr_events)
    
    acceleration_start_timestamp, acceleration_signal = signal_collector.signal_streams["acceleration"]
    breathing_start_timestamp, breathing_signal = signal_collector.signal_streams["breathing"]
    
    ax1 = pylab.subplot(4,1,1)
    ax2 = pylab.subplot(4,1,2,sharex=ax1)
    ax3 = pylab.subplot(4,1,3,sharex=ax1)
    ax4 = pylab.subplot(4,1,4,sharex=ax1)
    
    breathing_x_values = numpy.arange(len(breathing_signal), dtype=float)
    breathing_x_values *= 0.056
    breathing_x_values += breathing_start_timestamp
    
#    rr_x_values = numpy.arange(len(signal_receiver.rr_values), dtype=float)
#    rr_x_values *= 0.056
    
    acceleration_x_values = numpy.arange(len(acceleration_signal), dtype=float)
    acceleration_x_values *= 0.02
    acceleration_x_values += acceleration_start_timestamp
    
    ax1.plot(breathing_x_values, breathing_signal)
#    ax2.plot(rr_x_values, signal_receiver.rr_values)
    ax3.plot(acceleration_x_values, numpy.array(acceleration_signal))
    ax4.plot(rr_events_array[:, 0], rr_events_array[:, 1], "+")
    
    ax2.set_ylim((0, 1.5))
    ax4.set_ylim((0, 1.5))
    
    pylab.show()


if __name__ == "__main__":
    main()
