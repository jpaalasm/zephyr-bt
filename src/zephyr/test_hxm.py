
import unittest
import time

import zephyr
from zephyr import hxm
from zephyr.message import HxMMessage

class MonotonicSequenceModuloCorrectionTest(unittest.TestCase):
    def test_simple_case(self):
        correction = hxm.MonotonicSequenceModuloCorrection(10.0)
        
        self.assertEqual(correction.process(5.0), 5.0)
        self.assertEqual(correction.process(9.0), 9.0)
        self.assertEqual(correction.process(1.0), 11.0)
        self.assertEqual(correction.process(0.5), 20.5)
        self.assertEqual(correction.process(1.0), 21.0)


class RelativeHeartbeatTimestampAnalysisFixedHeartrateTest(unittest.TestCase):
    def setUp(self):
        self.analysis = hxm.RelativeHeartbeatTimestampAnalysis()
        self.modulo = 2**16
        self.heartbeat_millisecond_timestamps = [t * 1000 for t in range(-13, 3600)]
        self.heart_rate = 60
        self.start_time = time.time()
    
    def get_millisecond_timestamps_for_heartbeat_number(self, heartbeat_number):
        return self.heartbeat_millisecond_timestamps[heartbeat_number:heartbeat_number + 14]
    
    def process_packet(self, heartbeat_number):
        packet_millisecond_timestamps = self.get_millisecond_timestamps_for_heartbeat_number(heartbeat_number)
        reverse_cyclical_packet_timestamps = [t % self.modulo for t in packet_millisecond_timestamps[::-1]]
        packet = HxMMessage(heart_rate=self.heart_rate, heartbeat_number=heartbeat_number,
                            heartbeat_milliseconds=reverse_cyclical_packet_timestamps,
                            distance=0, speed=0, strides=0)
        
        latest_timestamp = packet_millisecond_timestamps[-1] / 1000.0
        
        zephyr.time = lambda: self.start_time + latest_timestamp
        
        for timestamp, heartbeat_interval in self.analysis.process(packet):
            yield timestamp, heartbeat_interval, latest_timestamp
    
    def test_exactly_synchronized_heartbeats(self):
        for heartbeat_number in range(3600):
            for timestamp, heartbeat_interval, latest_timestamp in self.process_packet(heartbeat_number):
                self.assertEqual(timestamp, self.start_time + latest_timestamp)
                self.assertEqual(heartbeat_interval, 1.0)
                self.assertTrue(all(offset == self.start_time for offset in self.analysis.instantaneous_offset_deque))
                self.assertEqual(self.analysis.offset, self.start_time)
    
    def test_calculation_history_overflow(self):
        self.assertEqual(len(list(self.process_packet(0))), 0) # first item skipped
        self.assertEqual(len(list(self.process_packet(1))), 1) # second item is processed
        self.assertEqual(len(list(self.process_packet(15))), 14) # history is just enough
        
        with self.assertRaises(hxm.CalculationHistoryOverflow):
            self.process_packet(30).next() # history overflows
