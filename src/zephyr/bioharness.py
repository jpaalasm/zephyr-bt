
import logging

import zephyr.message
import zephyr.util


class BioHarnessSignalAnalysis:
    def __init__(self, signal_callbacks, event_callbacks):
        self.signal_callbacks = signal_callbacks
        self.event_callbacks = event_callbacks
        
        self.latest_rr_value_sign = 0
    
    def handle_signal(self, signal_packet, starts_new_stream):
        if signal_packet.type == "rr":
            
            for sample_number, rr_value in enumerate(signal_packet.samples):
                signal_discontinuity = (sample_number == 0) and starts_new_stream
                
                rr_value_sign = cmp(rr_value, 0)
                
                if rr_value_sign != self.latest_rr_value_sign and not signal_discontinuity:
                    heartbeat_interval = abs(rr_value)
                    heartbeat_interval_timestamp = signal_packet.timestamp + sample_number / float(signal_packet.samplerate)
                    
                    for event_callback in self.event_callbacks:
                        event_callback("heartbeat_interval", (heartbeat_interval_timestamp, heartbeat_interval))
                
                self.latest_rr_value_sign = rr_value_sign


class BioHarnessPacketHandler:
    def __init__(self, signal_callbacks, event_callbacks, sequence_number_wraparound=256):
        self.signal_callbacks = signal_callbacks
        self.event_callbacks = event_callbacks
        self.sequence_number_wraparound = sequence_number_wraparound
        
        self.sequence_numbers = {}
        self.clock_difference_correction = zephyr.util.ClockDifferenceEstimator()
    
    def get_message_end_timestamp(self, signal_packet):
        temporal_message_length = (len(signal_packet.samples) - 1) / signal_packet.samplerate
        return signal_packet.timestamp + temporal_message_length
    
    def get_expected_sequence_number(self, packet_type):
        previous_sequence_number = self.sequence_numbers.get(packet_type)
        if previous_sequence_number is not None:
            expected_sequence_number = (previous_sequence_number + 1) % self.sequence_number_wraparound
        else:
            expected_sequence_number = None
        
        return expected_sequence_number
    
    def handle_packet(self, packet):
        if isinstance(packet, zephyr.message.SignalPacket):
            expected_sequence_number = self.get_expected_sequence_number(packet.type)
            self.sequence_numbers[packet.type] = packet.sequence_number
            
            if expected_sequence_number is not None and expected_sequence_number != packet.sequence_number:
                logging.warning("Invalid sequence number in stream %s: %d != %d",
                                packet.type, expected_sequence_number,
                                packet.sequence_number)
                
                starts_new_stream = True
            else:
                starts_new_stream = False
            
            
            end_timestamp = self.get_message_end_timestamp(packet)
            
            corrected_end_timestamp = self.clock_difference_correction.estimate_and_correct_timestamp(end_timestamp, packet.type)
            corrected_timestamp = packet.timestamp + corrected_end_timestamp - end_timestamp
            
            corrected_signal_packet = packet._replace(timestamp=corrected_timestamp)
            
            for signal_callback in self.signal_callbacks:
                signal_callback(corrected_signal_packet, starts_new_stream)
        
        elif isinstance(packet, zephyr.message.SummaryMessage):
            corrected_timestamp = self.clock_difference_correction.estimate_and_correct_timestamp(packet.timestamp, "bh_summary")
            
            for event_callback in self.event_callbacks:
                event_callback("activity", (corrected_timestamp, packet.activity))
                event_callback("heart_rate", (corrected_timestamp, packet.heart_rate))
                event_callback("respiration_rate", (corrected_timestamp, packet.respiration_rate))
