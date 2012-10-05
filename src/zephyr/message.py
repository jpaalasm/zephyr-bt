
import collections

import zephyr.util


HxMMessage = collections.namedtuple("HxMMessage",
                                    ["heart_rate", "heartbeat_number", "heartbeat_milliseconds",
                                     "distance", "speed", "strides"])

SummaryMessage = collections.namedtuple("SummaryMessage",
                                        ["sequence_number", "timestamp", "heart_rate",
                                         "respiration_rate", "skin_temperature",
                                         "posture", "activity", "peak_acceleration",
                                         "breathing_wave_amplitude", "breathing_confidence",
                                         "heart_rate_confidence"])

SignalPacket = collections.namedtuple("SignalPacket", ["type", "timestamp", "samplerate",
                                                       "samples", "sequence_number"])




#Specification of HxM payload bytes:
#Firmware ID
#Firmware Version
#Hardware ID
#Hardware Version
#Battery Charge Indicator
#Heart Rate
#Heart Beat Number
#Heart Beat Timestamp #1 (Oldest)
#Heart Beat Timestamp #2
#...
#Heart Beat Timestamp #14
#Heart Beat Timestamp #15 (Oldest)
#Reserved
#Reserved
#Reserved
#Distance
#Instantaneous speed
#Strides
#Reserved
#Reserved

def parse_hxm_message(payload):
    heart_rate, heartbeat_number = payload[9:11]
    
    heartbeat_timestamp_bytes = payload[11:41]
    
    movement_data_bytes = payload[47:53]
    
    distance, speed, strides = tuple(zephyr.util.parse_uint16_values_from_bytes(movement_data_bytes))
    
    distance = distance / 16.0
    speed = speed / 256.0
    
    heartbeat_milliseconds = list(zephyr.util.parse_uint16_values_from_bytes(heartbeat_timestamp_bytes))
    
    hxm_message = HxMMessage(heart_rate=heart_rate, heartbeat_number=heartbeat_number,
                             heartbeat_milliseconds=heartbeat_milliseconds, distance=distance,
                             speed=speed, strides=strides)
    return hxm_message


def parse_summary_packet(payload):
    sequence_number = payload[0]
    
    timestamp = zephyr.util.parse_timestamp(payload[1:9])
    
    (heart_rate, respiration_rate, skin_temperature, posture, activity,
     peak_acceleration, breathing_wave_amplitude) = \
        zephyr.util.parse_uint16_values_from_byte_sequence([10, 12, 14, 16, 18, 20, 25], payload)
    
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


def signal_packet_payload_parser_factory(sample_parser, signal_code, samplerate):
    def parse_signal_packet(payload):
        sequence_number = payload[0]
        timestamp_bytes = payload[1:9]
        signal_bytes = payload[9:]
        
        message_timestamp = zephyr.util.parse_timestamp(timestamp_bytes)
        samples = sample_parser(signal_bytes)
        
        signal_packet = zephyr.message.SignalPacket(signal_code, message_timestamp, samplerate, samples, sequence_number)
        return signal_packet
    
    return parse_signal_packet


def parse_10_bit_samples(signal_bytes):
    samples = zephyr.util.unpack_bit_packed_values(signal_bytes, 10, False)
    samples = [value - 512 for value in samples]
    return samples


def parse_16_bit_samples(signal_bytes):
    samples = zephyr.util.unpack_bit_packed_values(signal_bytes, 16, True)
    samples = [value * 0.001 for value in samples]
    return samples


def parse_accelerometer_samples(signal_bytes):
    interleaved_samples = parse_10_bit_samples(signal_bytes)
    
    # 83 correspond to one g in the 14-bit acceleration
    # signal, and this of 1/4 of that
    one_g_value = 20.75
    interleaved_samples = [value / one_g_value for value in interleaved_samples]
    
    samples = zip(interleaved_samples[0::3],
                        interleaved_samples[1::3],
                        interleaved_samples[2::3])
    return samples


class MessagePayloadParser:
    def __init__(self, callbacks):
        self.callbacks = callbacks
    
    def handle_message(self, message_frame):
        handler = MESSAGE_TYPES.get(message_frame.message_id)
        if handler is not None:
            message = handler(message_frame.payload)
            for callback in self.callbacks:
                callback(message)


MESSAGE_TYPES = {0x2B: parse_summary_packet,
                 0x21: signal_packet_payload_parser_factory(parse_10_bit_samples, "breathing", 18.0),
                 0x22: signal_packet_payload_parser_factory(parse_10_bit_samples, "ecg", 250.0),
                 0x24: signal_packet_payload_parser_factory(parse_16_bit_samples, "rr", 18.0),
                 0x25: signal_packet_payload_parser_factory(parse_accelerometer_samples, "acceleration", 50.0),
                 0x26: parse_hxm_message}
