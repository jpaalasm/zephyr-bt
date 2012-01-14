
def unpack_bit_packed_values(data_bytes, value_nbits):
    total_bit_count = len(data_bytes) * 8
    value_count = total_bit_count / value_nbits
    value_bit_mask = 2**value_nbits - 1
    
    unpacked_values = [] 
    
    for value_i in range(value_count):
        value_start_bit = value_i * value_nbits
        value_start_byte = value_start_bit / 8
        bit_offset_from_start_byte = value_start_bit % 8
        
        unpacked_value = data_bytes[value_start_byte] + (data_bytes[value_start_byte + 1] << 8)
        unpacked_value >>= bit_offset_from_start_byte
        unpacked_value &= value_bit_mask
        
        unpacked_values.append(unpacked_value)
    
    return unpacked_values

class SignalReceiver:
    def __init__(self):
        self.breathing_values = []
        self.rr_values = []
        self.acceleration_values = []
        
        self.message_handlers = {0x21: self.handle_breathing_payload,
                                 0x24: self.handle_rr_payload,
                                 0x25: self.handle_accelerometer_payload}
    
    def handle_message(self, message):
        message_handler = self.message_handlers.get(message.message_id)
        
        if message_handler is not None:
            message_handler(message.payload)
    
    def handle_rr_payload(self, payload):
        assert len(payload) == 45
        
        data_bytes = payload[9:]
        
        signal_values = unpack_bit_packed_values(data_bytes, 16)
        
        maximum_value = 2**16
        value_boundary = 2**15
        
        signal_values = [(value if value < value_boundary else value - maximum_value)
                         for value in signal_values]
        
        assert len(signal_values) == 18
        
        self.rr_values.extend(signal_values)
    
    def handle_accelerometer_payload(self, payload):
        assert len(payload) == 84
        
        data_bytes = payload[9:]
        
        signal_values = unpack_bit_packed_values(data_bytes, 10)
        assert len(signal_values) == 60
        
        one_g_value = (83 / 4.0)
        
        signal_values = [(value - 512) / one_g_value for value in signal_values]
        
        x_values = signal_values[0::3]
        y_values = signal_values[1::3]
        z_values = signal_values[2::3]
        
        self.acceleration_values.extend(zip(x_values, y_values, z_values))
    
    def handle_breathing_payload(self, payload):
        assert len(payload) == 32
        
        data_bytes = payload[9:]
        
        signal_values = unpack_bit_packed_values(data_bytes, 10)
        assert len(signal_values) == 18
        
        signal_values = [value - 512 for value in signal_values]
        
        self.breathing_values.extend(signal_values)
