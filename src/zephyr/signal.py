
import time
import collections
import logging

import zephyr.message
import zephyr.util

SignalStream = collections.namedtuple("SignalStream", ["start_timestamp", "samplerate", "signal_values"])


class SignalMessageParser:
    def __init__(self, callback):
        self.callback = callback
    
    def handle_message(self, message_frame):
        message_id = message_frame.message_id
        
        if message_id in zephyr.message.SIGNAL_MESSAGE_TYPES:
            message = zephyr.message.parse_signal_packet(message_frame)
            self.callback(message)
        elif message_id in zephyr.message.OTHER_MESSAGE_TYPES:
            handler = zephyr.message.OTHER_MESSAGE_TYPES[message_id]
            message = handler(message_frame.payload)
            self.callback(message)


class SignalCollector:
    def __init__(self, use_clock_difference_correction=True):
        self._signal_streams = {}
        self.sequence_numbers = {}
        
        if use_clock_difference_correction:
            self.clock_difference_correction = zephyr.util.ClockDifferenceEstimator()
        else:
            self.clock_difference_correction = None
    
    def get_message_end_timestamp(self, signal_packet):
        temporal_message_length = (len(signal_packet.signal_values) - 1) / signal_packet.samplerate
        return signal_packet.timestamp + temporal_message_length
    
    def initialize_signal_stream(self, signal_packet):
        signal_stream = SignalStream(signal_packet.timestamp, signal_packet.samplerate, [])
        
        assert signal_packet.type not in self._signal_streams
        self._signal_streams[signal_packet.type] = signal_stream
    
    def reset_signal_stream(self, stream_name):
        del self._signal_streams[stream_name]
    
    def handle_packet(self, signal_packet):
        if isinstance(signal_packet, zephyr.message.SignalPacket):
            previous_sequence_number = self.sequence_numbers.get(signal_packet.type)
            if previous_sequence_number is not None:
                expected_sequence_number = (previous_sequence_number + 1) % 256
                if signal_packet.sequence_number != expected_sequence_number:
                    logging.warning("Invalid sequence number in stream %s: %d -> %d",
                                    signal_packet.type, previous_sequence_number,
                                    signal_packet.sequence_number)
                    self.reset_signal_stream(signal_packet.type)
            
            self.sequence_numbers[signal_packet.type] = signal_packet.sequence_number
            
            if signal_packet.type not in self._signal_streams:
                self.initialize_signal_stream(signal_packet)
            
            signal_stream = self._signal_streams[signal_packet.type]
            signal_stream.signal_values.extend(signal_packet.signal_values)
            
            if self.clock_difference_correction is not None:
                signal_stream_position = signal_stream.start_timestamp + (len(signal_stream.signal_values) - 1) / signal_stream.samplerate
                zephyr_clock_ahead = signal_stream_position - time.time()
                
                self.clock_difference_correction.append_clock_difference_value(signal_packet.type, zephyr_clock_ahead)
    
    def get_signal_stream(self, stream_type):
        signal_stream = self._signal_streams[stream_type]
        
        zephyr_clock_ahead_estimate = 0.0 if self.clock_difference_correction is None \
                else self.clock_difference_correction.get_estimate(stream_type)
        
        corrected_timestamp = signal_stream.start_timestamp - zephyr_clock_ahead_estimate
        
        signal_stream = SignalStream(corrected_timestamp, signal_stream.samplerate, signal_stream.signal_values)
        return signal_stream
    
    def iterate_samples_with_timing(self, stream_type, start_sample=0):
        signal_stream = self.get_signal_stream(stream_type)
        
        signal_values = signal_stream.signal_values[start_sample:]
        
        for sample_index, signal_value in enumerate(signal_values, start=start_sample):
            timestamp = float(sample_index) / signal_stream.samplerate + signal_stream.start_timestamp
            yield timestamp, signal_value
    
    def iterate_signal_streams(self):
        for stream_type in self._signal_streams.keys():
            yield stream_type, self.get_signal_stream(stream_type)
