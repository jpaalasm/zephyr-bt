
import numpy
import time
import threading
import matplotlib.pyplot

class VisualizationWindow:
    def __init__(self, signal_collector):
        self.figure, self.axes = matplotlib.pyplot.subplots(7, 1, sharex=True)
        self.figure.subplots_adjust(hspace=0)
        
        self.signal_collector = signal_collector
        
        def create_empty_line(ax_index, *args):
            return self.axes[ax_index].plot([], [], *args)[0]
        
        self.acceleration_lines = [create_empty_line(0), create_empty_line(0), create_empty_line(0)]
        self.breathing_line = create_empty_line(1)
        self.ecg_line = create_empty_line(2)
        
        self.respiration_rate_line = create_empty_line(3, "+")
        self.heart_rate_line = create_empty_line(4, "+")
        self.heartbeat_interval_line = create_empty_line(5, "+")
        self.activity_line = create_empty_line(6, "+")
        
        self.axes[0].set_ylim((-4, 4))
        self.axes[1].set_ylim((-1000, 1000))
        self.axes[2].set_ylim((-500, 500))
        self.axes[3].set_ylim((0, 50))
        self.axes[4].set_ylim((0, 120))
        self.axes[5].set_ylim((0, 2))
        self.axes[6].set_ylim((0, 2))
        
        self.stop_updating_requested = False
    
    def update_plots(self):
        while not self.stop_updating_requested:
            for stream_name, stream_data in self.signal_collector.iterate_signal_streams():
                end_timestamp, samplerate, samples = stream_data
                
                signal_value_array = numpy.array(samples, dtype=float)
                
                x_values = numpy.arange(len(signal_value_array), dtype=float)
                x_values /= samplerate
                x_values += end_timestamp - len(signal_value_array) / samplerate
                
                if stream_name == "acceleration":
                    for line_i, line in enumerate(self.acceleration_lines):
                        line.set_xdata(x_values)
                        line.set_ydata(signal_value_array[:, line_i])
                
                elif stream_name == "breathing":
                    self.breathing_line.set_xdata(x_values)
                    self.breathing_line.set_ydata(signal_value_array)
                
                elif stream_name == "ecg":
                    self.ecg_line.set_xdata(x_values)
                    self.ecg_line.set_ydata(signal_value_array)
            
            
            for stream_name, event_list in self.signal_collector.iterate_event_streams():
                if len(event_list) == 0:
                    continue
                
                event_data_array = numpy.array(event_list, dtype=float)
                
                event_timestamps = event_data_array[:, 0]
                event_values = event_data_array[:, 1]
                
                
                event_line_object_map = {"heart_rate": self.heart_rate_line,
                                         "respiration_rate": self.respiration_rate_line,
                                         "heartbeat_interval": self.heartbeat_interval_line,
                                         "activity": self.activity_line}
                
                event_line_object = event_line_object_map[stream_name]
                
                if event_line_object is not None:
                    event_line_object.set_xdata(event_timestamps)
                    event_line_object.set_ydata(event_values)
            
            now = time.time()
            self.axes[0].set_xlim((now - 115, now + 5))
            
            matplotlib.pyplot.draw()
            time.sleep(0.2)
    
    def show(self):
        threading.Thread(target=self.update_plots).start()
        
        matplotlib.pyplot.show()
        
        self.stop_updating_requested = True
