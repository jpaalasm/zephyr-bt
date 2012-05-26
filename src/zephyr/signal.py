
import time
import logging
import copy

import zephyr.message
import zephyr.util


class SignalStream:
    def __init__(self, signal_packet):
        self.samplerate = None
        self.end_timestamp = None
        self.signal_values = []
        
        self.append_signal_packet(signal_packet)
    
    def append_signal_packet(self, signal_packet):
        assert self.samplerate is None or self.samplerate == signal_packet.samplerate
        
        self.samplerate = signal_packet.samplerate
        self.end_timestamp = signal_packet.timestamp + len(signal_packet.signal_values) / float(signal_packet.samplerate)
        self.signal_values.extend(signal_packet.signal_values)
    
    def get_time_corrected_signal_stream(self, corrected_timestamp):
        signal_stream = copy.copy(self)
        signal_stream.samplerate = self.samplerate
        signal_stream.end_timestamp = corrected_timestamp
        signal_stream.signal_values = self.signal_values
        return signal_stream
    
    @property
    def start_timestamp(self):
        return self.end_timestamp - len(self.signal_values) / float(self.samplerate)


class MessagePayloadParser:
    def __init__(self, callback):
        self.callback = callback
    
    def handle_message(self, message_frame):
        message_id = message_frame.message_id
        
        if message_id in zephyr.message.MESSAGE_TYPES:
            handler = zephyr.message.MESSAGE_TYPES[message_id]
            message = handler(message_frame.payload)
            self.callback(message)


class SignalCollector:
    def __init__(self):
        self._signal_streams = {}
        self.chunk_handler = SignalChunkHandler(self)
        self.clock_difference_correction = zephyr.util.ClockDifferenceEstimator()
    
    def reset_signal_stream(self, stream_name):
        del self._signal_streams[stream_name]
    
    def get_signal_stream(self, stream_type):
        signal_stream = self._signal_streams[stream_type]
        zephyr_clock_ahead_estimate = self.clock_difference_correction.get_estimate(stream_type)
        corrected_timestamp = signal_stream.end_timestamp - zephyr_clock_ahead_estimate
        
        signal_stream = signal_stream.get_time_corrected_signal_stream(corrected_timestamp)
        return signal_stream
    
    def iterate_samples_with_timing(self, stream_type, start_sample=0):
        signal_stream = self.get_signal_stream(stream_type)
        
        signal_values = signal_stream.signal_values[start_sample:]
        
        for sample_index, signal_value in enumerate(signal_values, start=start_sample):
            timestamp = signal_stream.start_timestamp + float(sample_index) / signal_stream.samplerate
            yield timestamp, signal_value
    
    def iterate_signal_streams(self):
        for stream_type in self._signal_streams.keys():
            yield stream_type, self.get_signal_stream(stream_type)

    def extend_stream(self, signal_packet):
        if signal_packet.type not in self._signal_streams:
            signal_stream = SignalStream(signal_packet)
            self._signal_streams[signal_packet.type] = signal_stream
        else:
            signal_stream = self._signal_streams[signal_packet.type]
        
        signal_stream.append_signal_packet(signal_packet)
        return signal_stream
    
    def handle_packet(self, signal_packet):
        return self.chunk_handler.handle_packet(signal_packet)


class SignalChunkHandler:
    def __init__(self, signal_collector):
        self.signal_collector = signal_collector
        self.sequence_numbers = {}
        self.clock_difference_correction = zephyr.util.ClockDifferenceEstimator()
    
    def get_message_end_timestamp(self, signal_packet):
        temporal_message_length = (len(signal_packet.signal_values) - 1) / signal_packet.samplerate
        return signal_packet.timestamp + temporal_message_length

    def get_expected_sequence_number(self, packet_type):
        previous_sequence_number = self.sequence_numbers.get(packet_type)
        if previous_sequence_number is not None:
            expected_sequence_number = (previous_sequence_number + 1) % 256
        else:
            expected_sequence_number = None
        
        return expected_sequence_number
    
    def handle_packet(self, signal_packet):
        if isinstance(signal_packet, zephyr.message.SignalPacket):
            expected_sequence_number = self.get_expected_sequence_number(signal_packet.type)
            
            if expected_sequence_number is not None and expected_sequence_number != signal_packet.sequence_number:
                logging.warning("Invalid sequence number in stream %s: %d != %d",
                                signal_packet.type, expected_sequence_number,
                                signal_packet.sequence_number)
                self.signal_collector.reset_signal_stream(signal_packet.type)
            else:
                pass
            
            self.sequence_numbers[signal_packet.type] = signal_packet.sequence_number
            
            signal_stream = self.signal_collector.extend_stream(signal_packet)
            
            zephyr_clock_ahead = signal_stream.end_timestamp - time.time()
            
            self.clock_difference_correction.append_clock_difference_value(signal_packet.type, zephyr_clock_ahead)
