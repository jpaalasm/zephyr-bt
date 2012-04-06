
def crc_8_digest(values):
    crc = 0
    
    for byte in values:
        crc ^= byte
        for i in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8C
            else:
                crc = (crc >> 1)
    
    return crc


def parse_uint16_values_from_bytes(byte_values):
    assert not len(byte_values) % 2
    
    byte_iterator = iter(byte_values)
    
    while True:
        byte1 = byte_iterator.next()
        byte2 = byte_iterator.next()
        yield byte1 + (byte2 << 8)
