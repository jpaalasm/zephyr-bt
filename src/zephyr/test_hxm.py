
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


class RelativeHeartbeatTimestampAnalysisTest(unittest.TestCase):
    def test_exactly_synchronized_heartbeats(self):
        analysis = hxm.RelativeHeartbeatTimestampAnalysis()
        
        modulo = 2**16 * 0.001
        
        heartbeat_timestamps = [float(t) for t in range(-13, 3600)]
        heart_rate = 60
        
        start_time = time.time()
        
        for heartbeat_number in range(3600):
            packet_timestamps = heartbeat_timestamps[heartbeat_number:heartbeat_number + 14]
            
            reverse_cyclical_packet_timestamps = [t % modulo for t in packet_timestamps[::-1]]
            packet = HxMMessage(heart_rate=heart_rate, heartbeat_number=heartbeat_number,
                                heartbeat_timestamps=reverse_cyclical_packet_timestamps,
                                distance=0, speed=0, strides=0)
            
            zephyr.time = lambda: start_time + packet_timestamps[-1]
            
            for timestamp, heartbeat_interval in analysis.process(packet):
                self.assertEqual(timestamp, start_time + packet_timestamps[-1])
                self.assertEqual(heartbeat_interval, 1.0)
                self.assertTrue(all(offset == start_time for offset in analysis.instantaneous_offset_deque))
                self.assertEqual(analysis.offset, start_time)
