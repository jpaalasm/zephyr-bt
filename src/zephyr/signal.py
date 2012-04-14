
import time
import collections
import logging

import zephyr.message

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
    def __init__(self, clock_difference_correction=True):
        self._signal_streams = {}
        self._event_streams = {}
        self._clock_difference_deques = collections.defaultdict(lambda: collections.deque(maxlen=60))
        self.sequence_numbers = {}
        self.clock_difference_correction = clock_difference_correction
        
        self.summary_packets = []
    
    def get_message_end_timestamp(self, signal_packet):
        temporal_message_length = (len(signal_packet.signal_values) - 1) / signal_packet.samplerate
        return signal_packet.timestamp + temporal_message_length
    
    def initialize_event_stream(self, stream_name):
        all_stream_names = self._event_streams.keys() + self._signal_streams.keys()
        assert stream_name not in all_stream_names
        self._event_streams[stream_name] = []
    
    def append_to_event_stream(self, stream_name, value):
        self._event_streams[stream_name].append(value)
    
    def initialize_signal_stream(self, signal_packet):
        all_stream_names = self._event_streams.keys() + self._signal_streams.keys()
        assert signal_packet.type not in all_stream_names
        
        signal_stream = SignalStream(signal_packet.timestamp, signal_packet.samplerate, [])
        self._signal_streams[signal_packet.type] = signal_stream
    
    def reset_signal_stream(self, stream_name):
        del self._signal_streams[stream_name]
    
    def handle_packet(self, signal_packet):
        if isinstance(signal_packet, zephyr.message.SummaryMessage):
            self.summary_packets.append(signal_packet)
        
        else:
            assert isinstance(signal_packet, zephyr.message.SignalPacket)
            
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
            
            if self.clock_difference_correction:
                signal_stream_position = signal_stream.start_timestamp + (len(signal_stream.signal_values) - 1) / signal_stream.samplerate
                zephyr_clock_ahead = signal_stream_position - time.time()
                self._clock_difference_deques[signal_packet.type].append(zephyr_clock_ahead)
    
    def get_signal_stream(self, stream_type):
        signal_stream = self._signal_streams[stream_type]
        
        if self.clock_difference_correction:
            zephyr_clock_ahead_values = self._clock_difference_deques[stream_type]
            zephyr_clock_ahead_estimate = sum(zephyr_clock_ahead_values) / len(zephyr_clock_ahead_values)
        else:
            zephyr_clock_ahead_estimate = 0.0
        
        signal_stream = SignalStream(signal_stream.start_timestamp - zephyr_clock_ahead_estimate, signal_stream.samplerate, signal_stream.signal_values)
        return signal_stream
    
    def get_event_stream(self, stream_type):
        event_stream = self._event_streams[stream_type]
        return event_stream
    
    def iterate_signal_streams(self):
        for stream_type in self._signal_streams.keys():
            yield stream_type, self.get_signal_stream(stream_type)
    
    def iterate_event_streams(self):
        return self._event_streams.iteritems()
