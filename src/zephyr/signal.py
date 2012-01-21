
import time
import datetime
import collections


SignalStream = collections.namedtuple("SignalStream", ["start_timestamp", "samplerate", "signal_values"])
SignalPacket = collections.namedtuple("SignalPacket", ["type", "timestamp", "samplerate", "signal_values"])


def unpack_bit_packed_values(data_bytes, value_nbits, twos_complement):
    total_bit_count = len(data_bytes) * 8
    value_count = total_bit_count / value_nbits
    
    value_bit_mask = 2**value_nbits - 1
    represented_value_count = 2**value_nbits
    half_represented_value_count = represented_value_count / 2
    
    unpacked_values = [] 
    
    for value_i in range(value_count):
        value_start_bit = value_i * value_nbits
        value_start_byte = value_start_bit / 8
        bit_offset_from_start_byte = value_start_bit % 8
        
        unpacked_value = data_bytes[value_start_byte] + (data_bytes[value_start_byte + 1] << 8)
        unpacked_value >>= bit_offset_from_start_byte
        unpacked_value &= value_bit_mask
        
        if twos_complement and unpacked_value >= half_represented_value_count:
            unpacked_value = unpacked_value - represented_value_count
        
        unpacked_values.append(unpacked_value)
    
    return unpacked_values

class SignalMessageParser:
    def __init__(self, callback):
        self.callback = callback
        
        self.signal_types = {0x21: (self.handle_10_bit_signal, "breathing", 18.0),
                             0x22: (self.handle_10_bit_signal, "ecg", 250.0),
                             0x24: (self.handle_rr_payload, "rr", 18.0),
                             0x25: (self.handle_accelerometer_payload, "acceleration", 50.0)}
    
    def parse_header_timestamp(self, header_bytes):
        year = header_bytes[1] + (header_bytes[2] << 8)
        month = header_bytes[3]
        day = header_bytes[4]
        day_milliseconds = (header_bytes[5] + (header_bytes[6] << 8) +
                            (header_bytes[7] << 16) + (header_bytes[8] << 24))
        
        date = datetime.date(year=year, month=month, day=day)
        
        timestamp = time.mktime(date.timetuple()) + day_milliseconds / 1000.0
        return timestamp
    
    def handle_message(self, message):
        if message.message_id in self.signal_types:
            message_handler, signal_code, samplerate = self.signal_types[message.message_id]
            
            header_bytes = message.payload[:9]
            signal_bytes = message.payload[9:]
            
            message_timestamp = self.parse_header_timestamp(header_bytes)
            
            signal_values = message_handler(signal_bytes)
            
            signal_packet = SignalPacket(signal_code, message_timestamp, samplerate, signal_values)
            self.callback(signal_packet)
    
    def handle_10_bit_signal(self, signal_bytes):
        signal_values = unpack_bit_packed_values(signal_bytes, 10, False)
        signal_values = [value - 512 for value in signal_values]
        return signal_values
    
    def handle_rr_payload(self, signal_bytes):
        signal_values = unpack_bit_packed_values(signal_bytes, 16, True)
        signal_values = [value / 1000.0 for value in signal_values]
        
        return signal_values
    
    def handle_accelerometer_payload(self, signal_bytes):
        interleaved_signal_values = self.handle_10_bit_signal(signal_bytes)
        
        # 83 correspond to one g in the 14-bit acceleration
        # signal, and this of 1/4 of that
        one_g_value = 20.75
        interleaved_signal_values = [value / one_g_value for value in interleaved_signal_values]
        
        signal_values = zip(interleaved_signal_values[0::3], interleaved_signal_values[1::3], interleaved_signal_values[2::3])
        return signal_values


class SignalCollector:
    def __init__(self):
        self.signal_streams = {}
        self.event_streams = {}
        self.estimated_clock_difference = None
    
    def initialize_event_stream(self, stream_name):
        all_stream_names = self.event_streams.keys() + self.signal_streams.keys()
        assert stream_name not in all_stream_names
        self.event_streams[stream_name] = []
    
    def initialize_signal_stream(self, signal_packet):
        all_stream_names = self.event_streams.keys() + self.signal_streams.keys()
        assert signal_packet.type not in all_stream_names
        
        if self.estimated_clock_difference is None:
            temporal_message_length = len(signal_packet.signal_values) / signal_packet.samplerate
            local_message_start_time = time.time() - temporal_message_length
            self.estimated_clock_difference = signal_packet.timestamp - local_message_start_time
        
        signal_stream = SignalStream(signal_packet.timestamp - self.estimated_clock_difference, signal_packet.samplerate, [])
        self.signal_streams[signal_packet.type] = signal_stream
    
    def handle_packet(self, signal_packet):
        if signal_packet.type not in self.signal_streams:
            self.initialize_signal_stream(signal_packet)
        
        signal_stream = self.signal_streams[signal_packet.type]
        signal_stream.signal_values.extend(signal_packet.signal_values)
