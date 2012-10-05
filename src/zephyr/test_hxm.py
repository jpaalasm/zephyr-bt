
import unittest

import hxm


class MonotonicSequenceModuloCorrectionTest(unittest.TestCase):
    def test_simple_case(self):
        correction = hxm.MonotonicSequenceModuloCorrection(10.0)
        
        self.assertEqual(correction.process(5.0), 5.0)
        self.assertEqual(correction.process(9.0), 9.0)
        self.assertEqual(correction.process(1.0), 11.0)
        self.assertEqual(correction.process(0.5), 20.5)
        self.assertEqual(correction.process(1.0), 21.0)
