"""Focused discharge masking tests for channel-parameter power laws."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
import warnings

import numpy as np

CODE = Path(__file__).resolve().parents[1] / 'code'
sys.path.insert(0, str(CODE))

from param_channel_calc_rivwth import calculate_channel_fields


class ChannelCalculationTests(unittest.TestCase):
    def setUp(self):
        self.args = SimpleNamespace(
            hc=np.float32(.1), hp=np.float32(.5), ho=np.float32(.25),
            hmin=np.float32(1), wc=np.float32(2.5), wp=np.float32(.6),
            wo=np.float32(.5), wmin=np.float32(5),
        )

    def test_positive_zero_and_missing_discharge(self):
        discharge = np.array([[100, 0, -9999]], dtype='f4')
        valid = np.array([[True, True, False]])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            fields = calculate_channel_fields(discharge, valid, self.args)
        self.assertEqual(caught, [])

        # Compare valid values against the unchanged reference expressions.
        expected_depth = np.maximum(
            self.args.hmin,
            self.args.hc*discharge[valid]**self.args.hp+self.args.ho,
        )
        expected_width = np.maximum(
            self.args.wmin,
            self.args.wc*discharge[valid]**self.args.wp+self.args.wo,
        )
        np.testing.assert_array_equal(fields['rivhgt'][valid], expected_depth)
        np.testing.assert_array_equal(fields['rivwth'][valid], expected_width)
        self.assertEqual(fields['rivhgt'][0, 1], self.args.hmin)
        self.assertEqual(fields['rivwth'][0, 1], self.args.wmin)
        self.assertEqual(fields['rivhgt'][0, 2], -9999)
        self.assertEqual(fields['rivwth'][0, 2], -9999)
        self.assertEqual(fields['rivman'][0, 2], -9999)

    def test_invalid_discharge_on_mapped_cell_is_reported(self):
        for value in (-1, np.nan, np.inf):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'mapped river cells'):
                calculate_channel_fields(
                    np.array([[value]], dtype='f4'),
                    np.array([[True]]),
                    self.args,
                )

    def test_nonfinite_or_negative_discharge_outside_network_is_not_evaluated(self):
        discharge = np.array([[-9999, np.nan, -1]], dtype='f4')
        valid = np.zeros(discharge.shape, dtype=bool)
        fields = calculate_channel_fields(discharge, valid, self.args)
        np.testing.assert_array_equal(fields['rivhgt'], np.full(discharge.shape, -9999, dtype='f4'))
        np.testing.assert_array_equal(fields['rivwth'], np.full(discharge.shape, -9999, dtype='f4'))


if __name__ == '__main__':
    unittest.main()
