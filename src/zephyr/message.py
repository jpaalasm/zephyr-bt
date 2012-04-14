
import collections

import zephyr.util


HxMMessage = collections.namedtuple("HxMMessage",
                                    ["heart_rate", "heartbeat_number", "heartbeat_timestamps",
                                     "distance", "speed", "strides"])

SummaryMessage = collections.namedtuple("SummaryMessage",
                                        ["sequence_number", "timestamp", "heart_rate",
                                         "respiration_rate", "skin_temperature",
                                         "posture", "activity", "peak_acceleration",
                                         "breathing_wave_amplitude", "breathing_confidence",
                                         "heart_rate_confidence"])

SignalPacket = collections.namedtuple("SignalPacket", ["type", "timestamp", "samplerate",
                                                       "signal_values", "sequence_number"])


def parse_hxm_message(payload):
    heart_rate, heartbeat_number = payload[9:11]
    
    heartbeat_timestamp_bytes = payload[11:41]
    
    movement_data_bytes = payload[47:53]
    
    distance, speed, strides = tuple(zephyr.util.parse_uint16_values_from_bytes(movement_data_bytes))
    
    distance = distance / 16.0
    speed = speed / 256.0
    
    heartbeat_timestamps = [t / 1000.0 for t in zephyr.util.parse_uint16_values_from_bytes(heartbeat_timestamp_bytes)]
    
    hxm_message = HxMMessage(heart_rate=heart_rate, heartbeat_number=heartbeat_number,
                             heartbeat_timestamps=heartbeat_timestamps, distance=distance,
                             speed=speed, strides=strides)
    return hxm_message


def uint16_from_two_bytes((byte1, byte2)):
    return byte1 + (byte2 << 8)


def parse_uint16_values_from_byte_sequence(ls_byte_indices, byte_sequence):
    values = [uint16_from_two_bytes(byte_sequence[index:index + 2])
              for index in ls_byte_indices]
    return values


def parse_summary_packet(payload):
    sequence_number = payload[0]
    
    timestamp = zephyr.util.parse_timestamp(payload[1:9])
    
    (heart_rate, respiration_rate, skin_temperature, posture, activity,
     peak_acceleration, breathing_wave_amplitude) = \
        parse_uint16_values_from_byte_sequence([10, 12, 14, 16, 18, 20, 25], payload)
    
    respiration_rate *= 0.1
    skin_temperature *= 0.1
    activity *= 0.01
    peak_acceleration *= 0.01
    
    breathing_confidence = payload[29]
    heart_rate_confidence = payload[34]
    
    message = SummaryMessage(sequence_number, timestamp, heart_rate,
                             respiration_rate, skin_temperature,
                             posture, activity, peak_acceleration,
                             breathing_wave_amplitude, breathing_confidence,
                             heart_rate_confidence)
    
    return message


def parse_signal_packet(message):
    sequence_number = message.payload[0]
    timestamp_bytes = message.payload[1:9]
    signal_bytes = message.payload[9:]
    
    sample_parser, signal_code, samplerate = SIGNAL_MESSAGE_TYPES[message.message_id]
    
    message_timestamp = zephyr.util.parse_timestamp(timestamp_bytes)
    signal_values = sample_parser(signal_bytes)
    
    signal_packet = zephyr.message.SignalPacket(signal_code, message_timestamp, samplerate, signal_values, sequence_number)
    return signal_packet


def parse_10_bit_samples(signal_bytes):
    signal_values = zephyr.util.unpack_bit_packed_values(signal_bytes, 10, False)
    signal_values = [value - 512 for value in signal_values]
    return signal_values


def parse_16_bit_samples(signal_bytes):
    signal_values = zephyr.util.unpack_bit_packed_values(signal_bytes, 16, True)
    signal_values = [value * 0.001 for value in signal_values]
    return signal_values


def parse_accelerometer_samples(signal_bytes):
    interleaved_signal_values = parse_10_bit_samples(signal_bytes)
    
    # 83 correspond to one g in the 14-bit acceleration
    # signal, and this of 1/4 of that
    one_g_value = 20.75
    interleaved_signal_values = [value / one_g_value for value in interleaved_signal_values]
    
    signal_values = zip(interleaved_signal_values[0::3],
                        interleaved_signal_values[1::3],
                        interleaved_signal_values[2::3])
    return signal_values


SIGNAL_MESSAGE_TYPES = {0x21: (parse_10_bit_samples, "breathing", 18.0),
                        0x22: (parse_10_bit_samples, "ecg", 250.0),
                        0x24: (parse_16_bit_samples, "rr", 18.0),
                        0x25: (parse_accelerometer_samples, "acceleration", 50.0)}

OTHER_MESSAGE_TYPES = {0x2B: parse_summary_packet}

