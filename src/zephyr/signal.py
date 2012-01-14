
import time
import datetime
import collections

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
        
        self.signal_types = {0x21: self.handle_breathing_payload,
                             0x24: self.handle_rr_payload,
                             0x25: self.handle_accelerometer_payload}
    
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
        message_handler = self.signal_types.get(message.message_id)
        
        if message_handler is not None:
            message_handler(message.payload)
    
    def handle_rr_payload(self, payload):
        assert len(payload) == 45
        
        header_bytes = payload[:9]
        data_bytes = payload[9:]
        
        message_timestamp = self.parse_header(header_bytes)
        
        signal_values = unpack_bit_packed_values(data_bytes, 16, True)
        
        signal_values = [value / 1000.0 for value in signal_values]
        
        assert len(signal_values) == 18
        
        self.callback("rr", signal_values, message_timestamp)
    
    def handle_accelerometer_payload(self, payload):
        assert len(payload) == 84
        
        header_bytes = payload[:9]
        data_bytes = payload[9:]
        
        message_timestamp = self.parse_header(header_bytes)
        
        signal_values = unpack_bit_packed_values(data_bytes, 10, False)
        assert len(signal_values) == 60
        
        one_g_value = 83 / 4.0
        
        signal_values = [(value - 512) / one_g_value for value in signal_values]
        
        x_values = signal_values[0::3]
        y_values = signal_values[1::3]
        z_values = signal_values[2::3]
        
        acceleration_values = zip(x_values, y_values, z_values)
        
        self.callback("acceleration", acceleration_values, message_timestamp)
    
    def handle_breathing_payload(self, payload):
        assert len(payload) == 32
        
        header_bytes = payload[:9]
        data_bytes = payload[9:]
        
        message_timestamp = self.parse_header(header_bytes)
        
        signal_values = unpack_bit_packed_values(data_bytes, 10, False)
        assert len(signal_values) == 18
        
        signal_values = [value - 512 for value in signal_values]
        
        self.callback("breathing", signal_values, message_timestamp)

SignalStream = collections.namedtuple("SignalStream", ["start_timestamp", "samplerate", "signal_values"])

class SignalCollector:
    def __init__(self):
        self.samplerates = {"rr": 18.0,
                            "breathing": 18.0,
                            "acceleration": 50.0}
        
        self.signal_streams = {}
        self.estimated_clock_difference = None
    
    def handle_signal(self, signal_type, signal_values, message_timestamp):
        if signal_type not in self.signal_streams:
            samplerate = self.samplerates.get(signal_type)
            
            if samplerate is not None:
                if self.estimated_clock_difference is None:
                    temporal_message_length = len(signal_values) / samplerate
                    local_message_start_time = time.time() - temporal_message_length
                    self.estimated_clock_difference = message_timestamp - local_message_start_time
                
                signal_stream = SignalStream(message_timestamp, samplerate, signal_values)
                self.signal_streams[signal_type] = signal_stream
        else:
            signal_stream = self.signal_streams[signal_type]
            signal_stream.signal_values.extend(signal_values)
