
import numpy
import time
import matplotlib.pyplot
from matplotlib.animation import FuncAnimation


class VisualizationWindow:
    def __init__(self, signal_collector):
        self.figure, self.axes = matplotlib.pyplot.subplots(7, 1, sharex=True)
        self.figure.subplots_adjust(hspace=0)
        
        ax_ylabels = ["3D accel.", "Breathing", "ECG", 
                      "Resp. rate", "HR", "HBI", "Activity"]
        
        for ylabel, ax in zip(ax_ylabels, self.axes):
            ax.set_ylabel(ylabel)
        
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
        
        self.artists = self.acceleration_lines + [self.breathing_line, self.ecg_line, self.respiration_rate_line, self.heart_rate_line, self.heartbeat_interval_line, self.activity_line]
        
        self.axes[0].set_ylim((-4, 4))
        self.axes[1].set_ylim((-1000, 1000))
        self.axes[2].set_ylim((-500, 500))
        self.axes[3].set_ylim((0, 50))
        self.axes[4].set_ylim((0, 120))
        self.axes[5].set_ylim((0, 2))
        self.axes[6].set_ylim((0, 2))
    
    def update_plots(self, framedata):
        for stream_name, stream in self.signal_collector.iterate_signal_streams():
            signal_value_array = numpy.array(stream.samples, dtype=float)
            
            x_values = numpy.arange(len(signal_value_array), dtype=float)
            x_values /= stream.samplerate
            x_values += stream.end_timestamp - len(signal_value_array) / stream.samplerate
            
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
        
        return self.artists
    
    def show(self):
        anim = FuncAnimation(self.figure, self.update_plots, interval=1000, blit=False)
        matplotlib.pyplot.show()
