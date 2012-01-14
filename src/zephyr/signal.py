
def unpack_bit_packed_values(data_bytes, value_nbits):
    total_bit_count = len(data_bytes) * 8
    value_count = total_bit_count / value_nbits
    value_bit_mask = 2**value_nbits - 1
    
    unpacked_values = [] 
    
    for value_i in range(value_count):
        value_start_bit = value_i * value_nbits
        value_start_byte = value_start_bit / 8
        bit_offset_from_start_byte = value_start_bit % 8
        
        unpacked_value = data_bytes[value_start_byte] + data_bytes[value_start_byte + 1] * 255
        unpacked_value >>= bit_offset_from_start_byte
        unpacked_value &= value_bit_mask
        
        unpacked_values.append(unpacked_value)
    
    return unpacked_values

class SignalReceiver:
    def __init__(self):
        self.breathing_values = []
    
    def handle_message(self, message):
        print "Message: %02x" % message.message_id
        
        if message.message_id == 0x21:
            self.handle_breathing_payload(message.payload)
    
    def handle_breathing_payload(self, payload):
        assert len(payload) == 32
        
        header = payload[:9]
        data_bytes = payload[9:]
        
        signal_values = unpack_bit_packed_values(data_bytes, 10)
        
        assert len(signal_values) == 18
        
        self.breathing_values.extend(signal_values)
        
        print "Breathing signal:", signal_values
