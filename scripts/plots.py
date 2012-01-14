
import numpy
import pylab

def visualize_measurements(signal_collector):
    print signal_collector.estimated_clock_difference
    
    rr_events_array = numpy.array(signal_collector.rr_events)
    
    acceleration_start_timestamp, acceleration_samplerate, acceleration_signal = signal_collector.signal_streams["acceleration"]
    breathing_start_timestamp, breathing_samplerate, breathing_signal = signal_collector.signal_streams["breathing"]
    
    ax1 = pylab.subplot(3,1,1)
    ax3 = pylab.subplot(3,1,2,sharex=ax1)
    ax4 = pylab.subplot(3,1,3,sharex=ax1)
    
    breathing_x_values = numpy.arange(len(breathing_signal), dtype=float)
    breathing_x_values /= breathing_samplerate
    breathing_x_values += breathing_start_timestamp
    
    acceleration_x_values = numpy.arange(len(acceleration_signal), dtype=float)
    acceleration_x_values /= acceleration_samplerate
    acceleration_x_values += acceleration_start_timestamp
    
    ax1.plot(breathing_x_values, breathing_signal)
    ax3.plot(acceleration_x_values, numpy.array(acceleration_signal))
    ax4.plot(rr_events_array[:, 0], rr_events_array[:, 1], "+")
    
    ax4.set_ylim((0, 1.5))
    
    pylab.show()
