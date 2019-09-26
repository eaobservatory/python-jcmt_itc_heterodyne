# Copyright (C) 2015 East Asian Observatory
# All Rights Reserved.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful,but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,51 Franklin
# Street, Fifth Floor, Boston, MA  02110-1301, USA

from __future__ import absolute_import, division, print_function, \
    unicode_literals

from unittest import TestCase

from jcmt_itc_heterodyne import HeterodyneITC, HeterodyneITCError, \
    HeterodyneReceiver


class CalculateTest(TestCase):
    def _test_calculation(self, rms, int_, elapsed, t_rx, t_sys,
                          *args, **kwargs):
        """
        The "tol_factor" kwarg can be used to ease the tolerance by a given
        factor for the "integration time" calculated for elapsed time and
        the elapsed time calculated from "integration time".  This is useful
        in the case of basket-weaved rasters.
        """

        tol_factor = kwargs.get('tol_factor', 1.0)
        itc = HeterodyneITC()

        (result, extra) = itc.calculate_time(
            rms, *args, with_extra_output=True)
        self.assertAlmostEqual(extra['t_rx'], t_rx, delta=0.1)
        self.assertAlmostEqual(extra['t_sys'], t_sys, delta=0.1)
        self.assertAlmostEqual(extra['int_time'], int_, delta=0.01)
        self.assertAlmostEqual(result, elapsed, delta=0.1)

        (result, extra) = itc.calculate_rms_for_elapsed_time(
            elapsed, *args, with_extra_output=True)
        self.assertAlmostEqual(extra['t_rx'], t_rx, delta=0.1)
        self.assertAlmostEqual(extra['t_sys'], t_sys, delta=0.1)
        self.assertAlmostEqual(extra['int_time'], int_,
                               delta=(0.01 * tol_factor))
        self.assertAlmostEqual(result, rms, delta=0.1)

        (result, extra) = itc.calculate_rms_for_int_time(
            int_, *args, with_extra_output=True)
        self.assertAlmostEqual(extra['t_rx'], t_rx, delta=0.1)
        self.assertAlmostEqual(extra['t_sys'], t_sys, delta=0.1)
        self.assertAlmostEqual(result, rms, delta=0.1)
        self.assertAlmostEqual(extra['elapsed_time'], elapsed,
                               delta=(5 * tol_factor))

    def test_rxa(self):
        # RxA Grid PSSW
        self._test_calculation(
            0.6, 75.60, 5088.7, 62.0, 399.6,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            233, 0.0192, 0.23, 25, True, False, 25,
            None, None, None, None, None, False, False)

        self._test_calculation(
            0.6, 40.80, 2783.2, 62.0, 293.6,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            233, 0.0192, 0.12, 25, True, False, 25,
            None, None, None, None, None, False, False)

        self._test_calculation(
            0.2, 658.47, 87327.6, 85.0, 393.1,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            215, 0.0192, 0.12, 45, True, False, 50,
            None, None, None, None, None, False, False)

        self._test_calculation(
            0.2, 12.50, 576.9, 62.0, 295.6,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            266, 0.488, 0.09, 30, True, False, 15,
            None, None, None, None, None, False, False)

        # RxA Grid BMSW

        self._test_calculation(
            0.2, 13.24, 1637.2, 96.0, 371.7,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            260, 0.488, 0.09, 30, True, False, 49,
            None, None, None, None, None, False, False)

        self._test_calculation(
            0.2, 23.16, 2790.1, 96.0, 371.7,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            260, 0.488, 0.09, 30, True, False, 49,
            None, None, None, None, None, True, False)

        self._test_calculation(
            0.2, 23.16, 3348.1, 96.0, 371.7,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            260, 0.488, 0.09, 30, True, False, 49,
            None, None, None, None, None, True, True)

        # RxA Jiggle BMSW

        self._test_calculation(
            0.25, 549.73, 8477.9, 185.0, 693.0,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            250, 0.0305, 0.11, 20, True, False, 9,
            None, None, None, None, None, False, False)

        self._test_calculation(
            0.15, 398.76, 23028.8, 79.0, 289.2,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            240, 0.0305, 0.07, 10, True, False, 25,
            None, None, None, None, None, True, False)

        # RxA Jiggle PSSW

        self._test_calculation(
            0.3, 161.3, 19443.2, 68.0, 367.8,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            235, 0.0305, 0.03, 80, True, False, 49,
            None, None, None, None, None, True, False)

        self._test_calculation(
            0.05, 48.65, 6976.4, 68.0, 255.7,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            235, 0.977, 0.03, 60, True, False, 81,
            None, None, None, None, None, False, False)

        # RxA Raster PSSW

        self._test_calculation(
            1.5, 4.56, 3607.4, 73.0, 391.2,
            HeterodyneReceiver.A3, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            220, 0.0305, 0.15, 50, True, False, None,
            150, 300, 10, 10, False, False, False)

        self._test_calculation(
            1.5, 4.43, 3309.9, 73.0, 391.2,
            HeterodyneReceiver.A3, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            220, 0.0305, 0.15, 50, True, False, None,
            150, 300, 10, 10, True, False, False,
            tol_factor=10.0)

    def test_rxw(self):
        # RxW Grid PSSW

        self._test_calculation(
            2.5, 60.22, 16038.3, 478.4, 2648.6,
            HeterodyneReceiver.WD, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            670, 0.0610, 0.04, 30, False, False, 100,
            None, None, None, None, None, False, False)

        self._test_calculation(
            2.5, 30.11, 8059.2, 478.4, 2648.6,
            HeterodyneReceiver.WD, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            670, 0.0610, 0.04, 30, False, True, 100,
            None, None, None, None, None, False, False)

        # RxW Grid BMSW

        self._test_calculation(
            3.5, 50.00, 9698.1, 636.1, 6410.7,
            HeterodyneReceiver.WD, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            640, 0.0610, 0.06, 20, False, True, 81,
            None, None, None, None, None, False, False)

        # RxW Jiggle BMSW

        self._test_calculation(
            0.75, 96.12, 16213.8, 544.9, 1359.3,
            HeterodyneReceiver.WD, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            690, 0.0305, 0.02, 10, False, True, 121,
            None, None, None, None, None, False, False)

        # RxW Jiggle PSSW

        self._test_calculation(
            4.5, 507.02, 11259.7, 521.8, 39127.3,
            HeterodyneReceiver.WD, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            700, 0.488, 0.11, 15, False, False, 9,
            None, None, None, None, None, True, False)

        # RxW Raster PSSW

        self._test_calculation(
            5.0, 88.67, 344385.3, 632.1, 12196.4,
            HeterodyneReceiver.WD, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            645, 0.061, 0.065, 45, False, True, None,
            400, 200, 5, 5, False, False, False,
            tol_factor=5.0)

    def test_harp(self):
        # HARP Grid PSSW

        self._test_calculation(
            0.05, 309.30, 837.8, 105, 339.6,
            HeterodyneReceiver.HARP, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            345, 0.488, 0.1, 35, False, False, 1,
            None, None, None, None, None, False, False)

        # HARP Grid BMSW

        self._test_calculation(
            0.25, 115.65, 1744.6, 137.6, 1237.2,
            HeterodyneReceiver.HARP, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            330, 0.488, 0.18, 55, False, False, 6,
            None, None, None, None, None, False, False)

        # HARP Jiggle PSSW

        self._test_calculation(
            0.2, 18.53, 598.8, 115.3, 595.0,
            HeterodyneReceiver.HARP, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            365, 0.977, 0.11, 45, False, False, 16,
            None, None, None, None, None, False, False)

        # HARP Jiggle BMSW

        self._test_calculation(
            0.2, 155.52, 6025.4, 111.1, 439.6,
            HeterodyneReceiver.HARP, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            355, 0.061, 0.11, 45, False, False, 25,
            None, None, None, None, None, False, False)

        # HARP Raster PSSW

        self._test_calculation(
            0.5, 9.616, 22944.4, 105.0, 1163.0,
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            345, 0.977, 0.25, 50, False, False, None,
            1800, 900, 7.27, 116.4, False, False, False)

        self._test_calculation(
            0.5, 9.719, 24269.7, 105.0, 1163.0,
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            345, 0.977, 0.25, 50, False, False, None,
            1800, 900, 7.27, 116.4, True, False, False,
            tol_factor=10.0)

        self._test_calculation(
            0.5, 0.188, 1781.9, 137.6, 628.7,
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            330, 0.977, 0.04, 75, False, False, None,
            300, 400, 7.27, 7.3, False, False, False)

        self._test_calculation(
            0.75, 24.640, 25247.4, 113.8, 688.9,
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            340, 0.0305, 0.065, 75, False, False, None,
            800, 400, 7.27, 58.2, False, False, False)

    def test_int_time_limit(self):
        itc = HeterodyneITC()
        args = [
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            330, 0.977, 0.04, 75, False, False, None,
            300, 400, 7.27, 7.3, False, False, False,
        ]

        with self.assertRaisesRegexp(
                HeterodyneITCError,
                '^The requested integration time per point is less than'):

            itc.calculate_rms_for_int_time(0.09, *args)

        with self.assertRaisesRegexp(
                HeterodyneITCError,
                '^The requested target sensitivity led to an integration t'):
            itc.calculate_time(1.0, *args)

        with self.assertRaisesRegexp(
                HeterodyneITCError,
                '^The requested elapsed time led to an integration t'):

            itc.calculate_rms_for_elapsed_time(500, *args)
