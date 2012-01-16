
import time
import datetime
import collections


SignalStream = collections.namedtuple("SignalStream", ["start_timestamp", "samplerate", "signal_values"])
SignalPacket = collections.namedtuple("SignalPacket", ["type", "timestamp", "signal_values"])


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
        
        self.signal_types = {0x21: (self.handle_breathing_payload, "breathing"),
                             0x22: (self.handle_ecg_payload, "ecg"),
                             0x24: (self.handle_rr_payload, "rr"),
                             0x25: (self.handle_accelerometer_payload, "acceleration")}
    
    def parse_header(self, header_bytes):
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
            message_handler, signal_code = self.signal_types[message.message_id]
            
            header_bytes = message.payload[:9]
            signal_bytes = message.payload[9:]
            
            message_timestamp = self.parse_header(header_bytes)
            
            signal_values = message_handler(signal_bytes)
            
            signal_packet = SignalPacket(signal_code, message_timestamp, signal_values)
            self.callback(signal_packet)
    
    def handle_rr_payload(self, signal_bytes):
        assert len(signal_bytes) == 36
        
        signal_values = unpack_bit_packed_values(signal_bytes, 16, True)
        signal_values = [value / 1000.0 for value in signal_values]
        assert len(signal_values) == 18
        
        return signal_values
    
    def handle_accelerometer_payload(self, signal_bytes):
        assert len(signal_bytes) == 75
        
        one_g_value = 83 / 4.0
        
        interleaved_signal_values = unpack_bit_packed_values(signal_bytes, 10, False)
        assert len(interleaved_signal_values) == 60
        interleaved_signal_values = [(value - 512) / one_g_value for value in interleaved_signal_values]
        
        signal_values = zip(interleaved_signal_values[0::3], interleaved_signal_values[1::3], interleaved_signal_values[2::3])
        
        return signal_values
    
    def handle_breathing_payload(self, signal_bytes):
        assert len(signal_bytes) == 23
        
        signal_values = unpack_bit_packed_values(signal_bytes, 10, False)
        assert len(signal_values) == 18
        signal_values = [value - 512 for value in signal_values]
        return signal_values
    
    def handle_ecg_payload(self, signal_bytes):
        assert len(signal_bytes) == 79
        
        signal_values = unpack_bit_packed_values(signal_bytes, 10, False)
        assert len(signal_values) == 63
        signal_values = [value - 512 for value in signal_values]
        return signal_values

class SignalCollector:
    def __init__(self):
        self.samplerates = {"rr": 18.0,
                            "breathing": 18.0,
                            "acceleration": 50.0,
                            "ecg": 250.}
        
        self.signal_streams = {}
        self.estimated_clock_difference = None
    
    def handle_packet(self, signal_packet):
        if signal_packet.type not in self.signal_streams:
            samplerate = self.samplerates.get(signal_packet.type)
            
            if samplerate is not None:
                if self.estimated_clock_difference is None:
                    temporal_message_length = len(signal_packet.signal_values) / samplerate
                    local_message_start_time = time.time() - temporal_message_length
                    self.estimated_clock_difference = signal_packet.timestamp - local_message_start_time
                
                signal_stream = SignalStream(signal_packet.timestamp, samplerate, signal_packet.signal_values)
                self.signal_streams[signal_packet.type] = signal_stream
        else:
            signal_stream = self.signal_streams[signal_packet.type]
            signal_stream.signal_values.extend(signal_packet.signal_values)
