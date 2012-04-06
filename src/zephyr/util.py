
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
