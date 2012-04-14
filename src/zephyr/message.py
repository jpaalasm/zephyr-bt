
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
