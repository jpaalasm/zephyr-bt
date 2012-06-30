
import numpy
import time
import pyglet
from pyglet import gl
from matplotlib.transforms import Bbox, BboxTransform


class VisualizationWindow:
    def __init__(self, signal_collector):
        self.signal_collector = signal_collector
        config = pyglet.gl.Config(sample_buffers=1, samples=4)
        
        screens = pyglet.window.get_platform().get_default_display().get_screens()
        primary_display = screens[0]
        
        self.window1 = AnalysisSupervisorWindow(self, resizable=True, screen=primary_display, config=config, caption='Analysis visualization')
    
    def update(self, dt):
        pass
    
    def show(self):
        pyglet.clock.schedule_interval(self.update, 1/100.)
        
        event_loop = pyglet.app.EventLoop()
        event_loop.run()


class Axes:
    def __init__(self, target_bbox):
        self.target_bbox = target_bbox
        self.data_bbox = Bbox([[0, 0], [1, 1]])
    
    def set_data_bbox(self, data_bbox):
        self.data_bbox = data_bbox
    
    def _make_coord_list(self, line_data):
        point_count = len(line_data)
        assert line_data.shape == (point_count, 2)
        
        transformation = BboxTransform(self.data_bbox, self.target_bbox)
        transformed_line_data = transformation.transform(line_data)
        
        coord_list = list(transformed_line_data.flat)
        return point_count, coord_list
    
    def plot_line(self, line_data, color, line_width):
        point_count, coord_list = self._make_coord_list(line_data)
        
        gl.glLineWidth(line_width)
        gl.glColor4f(*color)
        pyglet.graphics.draw(point_count, gl.GL_LINE_STRIP, ('v2f', coord_list))
    
    def plot_points(self, line_data, color, point_size):
        point_count, coord_list = self._make_coord_list(line_data)
        
        gl.glPointSize(point_size)
        gl.glColor4f(*color)
        pyglet.graphics.draw(point_count, gl.GL_POINTS, ('v2f', coord_list))


class BasePlotWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(BasePlotWindow, self).__init__(*args, **kwargs)
        self.aspect_ratio = 1.0
        self.coordinate_space_pixel_height = 1.0
        self.coordinate_space_pixel_width = 1.0
    
    def on_resize(self, width, height):
        if height > 0:
            self.aspect_ratio = float(width) / height
            self.coordinate_space_pixel_height = 1.0 / height
            self.coordinate_space_pixel_width = self.aspect_ratio / width
        else:
            self.aspect_ratio = 1.0
            self.coordinate_space_pixel_height = 1.0
            self.coordinate_space_pixel_width = 1.0
        
        top = 1.0
        bottom = 0.0
        right = 0.0
        left = -self.aspect_ratio
        
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(left, right, bottom, top, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
    
    def on_key_press(self, symbol, modifiers):
        if symbol == ord("f"):
            self.toggle_fullscreen()
    
    def toggle_fullscreen(self):
        self.set_fullscreen(not self.fullscreen)


class AnalysisSupervisorWindow(BasePlotWindow, pyglet.window.Window):
    def __init__(self, app, *args, **kwargs):
        super(AnalysisSupervisorWindow, self).__init__(*args, **kwargs)
        self.app = app
        self.switch_to_and_setup()
        
        self.ecg_line = Axes(Bbox([[-1, 0.5], [0, 1]]))
        self.breathing_line = Axes(Bbox([[-1, 0], [0, 0.5]]))
    
    def on_draw(self):
        self.clear()
        self.draw_border()
        self.draw_axes()
        self.draw_lines()
    
    def draw_axes(self):
        coord_list = (0,0,  0,1,  -1,1,  -1,0,  0,0)
        
        gl.glLineWidth(3)
        gl.glColor4f(0, 1, 0, 1)
        pyglet.graphics.draw(5, gl.GL_LINE_STRIP, ('v2f', coord_list))
    
    def draw_border(self):
        border_width = self.coordinate_space_pixel_width * 20
        border_height = self.coordinate_space_pixel_height * 20
        
        coord_list = (-border_width, border_height,
                      -border_width, 1 - border_height,
                      -self.aspect_ratio + border_width, 1 - border_height,
                      -self.aspect_ratio + border_width, border_height,
                      -border_width, border_height)
        
        gl.glLineWidth(1)
        gl.glColor4f(1, 1, 1, 1)
        pyglet.graphics.draw(5, gl.GL_LINE_STRIP, ('v2f', coord_list))
    
    def draw_lines(self):
#        ax_ylabels = ["3D accel.", "Breathing", "ECG", 
#                      "Resp. rate", "HR", "HBI", "Activity"]
        
        now = time.time()
        xmin, xmax = now - 15, now + 5
        
        for stream_name, stream in self.app.signal_collector.iterate_signal_streams():
            if stream_name == "acceleration":
                continue
            
            signal_value_array = numpy.array(stream.samples, dtype=float)
            
            x_values = numpy.arange(len(signal_value_array), dtype=float)
            x_values /= stream.samplerate
            x_values += stream.end_timestamp - len(signal_value_array) / stream.samplerate
            
            line_data = numpy.empty((len(signal_value_array), 2))
            line_data[:, 0] = x_values
            line_data[:, 1] = signal_value_array
            
            if stream_name == "ecg":
                self.ecg_line.set_data_bbox(Bbox([[xmin, -500], [xmax, 500]]))
                self.ecg_line.plot_line(line_data, (1, 0, 0, 1), 2)
            
            elif stream_name == "breathing":
                self.breathing_line.set_data_bbox(Bbox([[xmin, -1000], [xmax, 1000]]))
                self.breathing_line.plot_points(line_data, (0, 0, 1, 1), 5)
        
        
#        for stream_name, event_list in self.signal_collector.iterate_event_streams():
#            if len(event_list) == 0:
#                continue
#            
#            event_data_array = numpy.array(event_list, dtype=float)
#            
#            event_timestamps = event_data_array[:, 0]
#            event_values = event_data_array[:, 1]
#            
#            
#            event_line_object_map = {"heart_rate": self.heart_rate_line,
#                                     "respiration_rate": self.respiration_rate_line,
#                                     "heartbeat_interval": self.heartbeat_interval_line,
#                                     "activity": self.activity_line}
#            
#            event_line_object = event_line_object_map[stream_name]
#            
#            if event_line_object is not None:
#                event_line_object.set_xdata(event_timestamps)
#                event_line_object.set_ydata(event_values)
    
    def switch_to_and_setup(self):
        self.switch_to()
        gl.glClearColor(0, 0, 0, 1)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_BLEND)
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)
