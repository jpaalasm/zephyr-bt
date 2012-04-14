
import numpy
import time
import threading
import matplotlib.pyplot

class VisualizationWindow:
    def __init__(self, signal_collector):
        self.figure, self.axes = matplotlib.pyplot.subplots(3, 1, sharex=True)
        
        self.signal_collector = signal_collector
        
        create_empty_line = lambda ax_index: self.axes[ax_index].plot([], [])[0]
        
        self.acceleration_lines = [create_empty_line(0) for i in range(3)]
        self.breathing_line = create_empty_line(1)
        self.ecg_line = create_empty_line(2)
    
    def update_plots(self):
        while True:
            for stream_type, stream_data in self.signal_collector.iterate_signal_streams():
                start_timestamp, samplerate, signal_values = stream_data
                
                signal_value_array = numpy.array(signal_values, dtype=float)
                
                x_values = numpy.arange(len(signal_value_array), dtype=float)
                x_values /= samplerate
                x_values += start_timestamp
                
                if stream_type == "acceleration":
                    for line_i, line in enumerate(self.acceleration_lines):
                        line.set_xdata(x_values)
                        line.set_ydata(signal_value_array[:, line_i])
                
                elif stream_type == "breathing":
                    self.breathing_line.set_xdata(x_values)
                    self.breathing_line.set_ydata(signal_value_array)
                
                elif stream_type == "ecg":
                    self.ecg_line.set_xdata(x_values)
                    self.ecg_line.set_ydata(signal_value_array)
            
            
            now = time.time()
            self.axes[0].set_xlim((now - 30, now))
            
            matplotlib.pyplot.draw()
            time.sleep(0.1)
    
    def run(self):
        threading.Thread(target=self.update_plots).start()
        
        matplotlib.pyplot.show()
