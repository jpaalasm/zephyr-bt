
import time
import datetime
import collections

import zephyr


class FastTime:
    def __init__(self, speed):
        self.start_time = time.time()
        self.speed = speed
    
    def __call__(self):
        seconds_since_start = time.time() - self.start_time
        now = self.start_time + seconds_since_start * self.speed
        return now


class FastSleep:
    def __init__(self, speed):
        self.speed = speed
    
    def __call__(self, seconds):
        time.sleep(seconds / self.speed)


def set_time_speed(simulation_speed):
    zephyr.time = FastTime(simulation_speed)
    zephyr.sleep = FastSleep(simulation_speed)


def crc_8_digest(values):
    crc = 0
    
    for byte in values:
        crc ^= byte
        for i in range(8):  #@UnusedVariable
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


def uint16_from_two_bytes((byte1, byte2)):
    return byte1 + (byte2 << 8)


def parse_uint16_values_from_byte_sequence(ls_byte_indices, byte_sequence):
    values = [uint16_from_two_bytes(byte_sequence[index:index + 2])
              for index in ls_byte_indices]
    return values


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


DISABLE_CLOCK_DIFFERENCE_ESTIMATION = False

class ClockDifferenceEstimator:
    def __init__(self):
        self._clock_difference_deques = collections.defaultdict(lambda: collections.deque(maxlen=60))
    
    def estimate_and_correct_timestamp(self, timestamp, key):
        if DISABLE_CLOCK_DIFFERENCE_ESTIMATION:
            return timestamp
        
        instantaneous_zephyr_clock_ahead = timestamp - zephyr.time()
        self._clock_difference_deques[key].append(instantaneous_zephyr_clock_ahead)
        
        clock_ahead_values = self._clock_difference_deques[key]
        zephyr_clock_ahead_estimate = sum(clock_ahead_values) / float(len(clock_ahead_values))
        
        corrected_timestamp = timestamp - zephyr_clock_ahead_estimate
        return corrected_timestamp
