
import time
import collections
import logging

import zephyr.message
import zephyr.util

SignalStream = collections.namedtuple("SignalStream", ["start_timestamp", "samplerate", "signal_values"])


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
    
    def initialize_signal_stream_if_does_not_exist(self, signal_packet):
        if signal_packet.type not in self._signal_streams:
            signal_stream = SignalStream(signal_packet.timestamp, signal_packet.samplerate, [])
            
            assert signal_packet.type not in self._signal_streams
            self._signal_streams[signal_packet.type] = signal_stream
    
    def reset_signal_stream(self, stream_name):
        del self._signal_streams[stream_name]
    
    def get_signal_stream(self, stream_type):
        signal_stream = self._signal_streams[stream_type]
        
        zephyr_clock_ahead_estimate = self.clock_difference_correction.get_estimate(stream_type)
        
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

    def extend_stream(self, signal_packet):
        self.initialize_signal_stream_if_does_not_exist(signal_packet)
        
        signal_stream = self._signal_streams[signal_packet.type]
        signal_stream.signal_values.extend(signal_packet.signal_values)
        
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
            
            signal_stream_position = signal_stream.start_timestamp + (len(signal_stream.signal_values) - 1) / signal_stream.samplerate
            zephyr_clock_ahead = signal_stream_position - time.time()
            
            self.clock_difference_correction.append_clock_difference_value(signal_packet.type, zephyr_clock_ahead)
