
import time
import datetime


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


def parse_timestamp(timestamp_bytes):
    year = timestamp_bytes[0] + (timestamp_bytes[1] << 8)
    month = timestamp_bytes[2]
    day = timestamp_bytes[3]
    day_milliseconds = (timestamp_bytes[4] +
                        (timestamp_bytes[5] << 8) +
                        (timestamp_bytes[6] << 16) +
                        (timestamp_bytes[7] << 24))
    
    date = datetime.date(year=year, month=month, day=day)
    
    timestamp = time.mktime(date.timetuple()) + day_milliseconds / 1000.0
    return timestamp


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
