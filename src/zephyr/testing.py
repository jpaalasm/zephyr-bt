
import os
import csv
import collections

import zephyr
from zephyr.collector import MeasurementCollector
from zephyr.bioharness import BioHarnessSignalAnalysis, BioHarnessPacketHandler
from zephyr.delayed_stream import DelayedRealTimeStream
from zephyr.message import MessagePayloadParser
from zephyr.protocol import BioHarnessProtocol, MessageFrameParser
from zephyr.hxm import HxMPacketAnalysis


test_data_dir = os.path.join(os.path.split(os.path.split(os.path.split(__file__)[0])[0])[0], "test_data")


class VirtualSerial:
    def __init__(self, stream_data_path):
        self.input_file = open(stream_data_path, "rb")
    
    def open(self):
        return None
    
    def read(self, byte_count):
        read_bytes = self.input_file.read(byte_count)
        
        if len(read_bytes) == 0:
            raise EOFError("End of file reached")
        
        return read_bytes


class TimedVirtualSerial:
    def __init__(self, stream_data_path, timing_data_path):
        self.input_file = open(stream_data_path, "rb")
        
        timing_csv_iterator = csv.reader(open(timing_data_path))
        self.timings = collections.deque((float(timestamp_str), int(byte_count_str))
                                         for timestamp_str, byte_count_str
                                         in timing_csv_iterator)
        
        start_time = zephyr.time()
        first_timestamp = float(self.timings[0][0])
        self.timestamp_correction = start_time - first_timestamp
    
    def open(self):
        return None
    
    def read(self, byte_count):
        assert byte_count == 1
        return self.read_byte()
    
    def write(self, data):
        pass
    
    def read_byte(self):
        if len(self.timings) == 0:
            raise EOFError("End of file reached")
        
        chunk_timestamp_string, chunk_cumulative_byte_count_string = self.timings[0]
        chunk_timestamp = float(chunk_timestamp_string) + self.timestamp_correction
        chunk_cumulative_byte_count = int(chunk_cumulative_byte_count_string)
        
        time_to_chunk_timestamp = chunk_timestamp - zephyr.time()
        
        if time_to_chunk_timestamp > 0:
            zephyr.sleep(time_to_chunk_timestamp)
        
        output_byte = self.input_file.read(1)
        position = self.input_file.tell()
        
        if position >= chunk_cumulative_byte_count:
            self.timings.popleft()
        
        return output_byte


def visualize_measurements(signal_collector):
    import numpy
    import pylab
    
    
    ax1 = pylab.subplot(4,1,1)
    ax2 = pylab.subplot(4,1,2,sharex=ax1)
    ax3 = pylab.subplot(4,1,3,sharex=ax1)
    ax4 = pylab.subplot(4,1,4,sharex=ax1)
    
    
    breathing_stream_history = signal_collector.get_signal_stream_history("breathing")
    for breathing_stream in breathing_stream_history.get_signal_streams():
        breathing_x_values = numpy.arange(len(breathing_stream.samples), dtype=float)
        breathing_x_values /= breathing_stream.samplerate
        breathing_x_values += breathing_stream.start_timestamp
        ax1.plot(breathing_x_values, breathing_stream.samples)
    
    ecg_stream_history = signal_collector.get_signal_stream_history("ecg")
    for ecg_stream in ecg_stream_history.get_signal_streams():
        ecg_x_values = numpy.arange(len(ecg_stream.samples), dtype=float)
        ecg_x_values /= ecg_stream.samplerate
        ecg_x_values += ecg_stream.start_timestamp
        ax2.plot(ecg_x_values, ecg_stream.samples)
    
    acceleration_stream_history = signal_collector.get_signal_stream_history("acceleration")
    for acceleration_stream in acceleration_stream_history.get_signal_streams():
        acceleration_x_values = numpy.arange(len(acceleration_stream.samples), dtype=float)
        acceleration_x_values /= acceleration_stream.samplerate
        acceleration_x_values += acceleration_stream.start_timestamp
        ax3.plot(acceleration_x_values, numpy.array(acceleration_stream.samples))
    
    
    heartbeat_interval_stream = signal_collector.get_event_stream("heartbeat_interval")
    heartbeat_interval_timestamps, heartbeat_intervals = zip(*heartbeat_interval_stream)
    ax4.plot(heartbeat_interval_timestamps, heartbeat_intervals, "+-")
    
    ax4.set_ylim((0, 1.5))
    
    pylab.show()


def simulation_workflow(callbacks, ser):
    zephyr.configure_root_logger()
    
    collector = MeasurementCollector()
    
    rr_signal_analysis = BioHarnessSignalAnalysis([], [collector.handle_event])

    signal_packet_handler_bh = BioHarnessPacketHandler([collector.handle_signal, rr_signal_analysis.handle_signal],
                                                       [collector.handle_event])
    signal_packet_handler_hxm = HxMPacketAnalysis([collector.handle_event])
    
    payload_parser = MessagePayloadParser([signal_packet_handler_bh.handle_packet,
                                           signal_packet_handler_hxm.handle_packet])
    
    message_parser = MessageFrameParser(payload_parser.handle_message)
    
    delayed_stream_thread = DelayedRealTimeStream(collector, callbacks, 1.2)
    
    protocol = BioHarnessProtocol(ser, [message_parser.parse_data])
    protocol.enable_periodic_packets()
    
    delayed_stream_thread.start()
    
    try:
        protocol.run()
    except EOFError:
        pass
    
    delayed_stream_thread.terminate()
    delayed_stream_thread.join()
