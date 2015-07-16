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

from jcmt_itc_heterodyne import HeterodyneITC, HeterodyneReceiver


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

        result = itc._calculate(HeterodyneITC.RMS_TO_TIME, rms, *args)
        self.assertAlmostEqual(result['extra']['t_rx'], t_rx, delta=0.1)
        self.assertAlmostEqual(result['extra']['t_sys'], t_sys, delta=0.1)
        self.assertAlmostEqual(result['int_time'], int_, delta=0.01)
        self.assertAlmostEqual(result['elapsed_time'], elapsed, delta=0.1)

        result = itc._calculate(HeterodyneITC.ELAPSED_TO_RMS, elapsed, *args)
        self.assertAlmostEqual(result['extra']['t_rx'], t_rx, delta=0.1)
        self.assertAlmostEqual(result['extra']['t_sys'], t_sys, delta=0.1)
        self.assertAlmostEqual(result['int_time'], int_,
                               delta=(0.01 * tol_factor))
        self.assertAlmostEqual(result['rms'], rms, delta=0.1)

        result = itc._calculate(HeterodyneITC.INT_TIME_TO_RMS, int_, *args)
        self.assertAlmostEqual(result['extra']['t_rx'], t_rx, delta=0.1)
        self.assertAlmostEqual(result['extra']['t_sys'], t_sys, delta=0.1)
        self.assertAlmostEqual(result['rms'], rms, delta=0.1)
        self.assertAlmostEqual(result['elapsed_time'], elapsed,
                               delta=(5 * tol_factor))

    def test_rxa(self):
        # RxA Grid PSSW
        self._test_calculation(
            0.6, 77.10, 5187.9, 62.0, 403.5,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            233, 0.0192, 0.23, 25, True, False, 25,
            None, None, None, None, None, None, False, False)

        self._test_calculation(
            0.6, 42.00, 2862.5, 62.0, 298.0,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            233, 0.0192, 0.12, 25, True, False, 25,
            None, None, None, None, None, None, False, False)

        self._test_calculation(
            0.2, 574.00, 76135.0, 85.0, 367.0,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            215, 0.0192, 0.12, 45, True, False, 50,
            None, None, None, None, None, None, False, False)

        self._test_calculation(
            0.2, 13.20, 604.7, 62.0, 303.5,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            266, 0.488, 0.09, 30, True, False, 15,
            None, None, None, None, None, None, False, False)

        # RxA Grid BMSW

        self._test_calculation(
            0.2, 13.80, 1702.6, 96.0, 379.8,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            260, 0.488, 0.09, 30, True, False, 49,
            None, None, None, None, None, None, False, False)

        self._test_calculation(
            0.2, 24.20, 2910.3, 96.0, 379.8,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            260, 0.488, 0.09, 30, True, False, 49,
            None, None, None, None, None, None, True, False)

        self._test_calculation(
            0.2, 24.20, 3492.4, 96.0, 379.8,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            260, 0.488, 0.09, 30, True, False, 49,
            None, None, None, None, None, None, True, True)

        # RxA Jiggle BMSW

        self._test_calculation(
            0.25, 417.90, 6468.8, 185.0, 604.3,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            250, 0.0305, 0.11, 20, True, False, 9,
            None, None, None, None, None, None, False, False)

        self._test_calculation(
            0.15, 394.3, 22772.2, 79.0, 287.5,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            240, 0.0305, 0.07, 10, True, False, 25,
            None, None, None, None, None, None, True, False)

        # RxA Jiggle PSSW

        self._test_calculation(
            0.3, 144.3, 17403.2, 68.0, 347.9,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            235, 0.0305, 0.03, 80, True, False, 49,
            None, None, None, None, None, None, True, False)

        self._test_calculation(
            0.05, 46.4, 6657.2, 68.0, 249.6,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            235, 0.977, 0.03, 60, True, False, 81,
            None, None, None, None, None, None, False, False)

        # RxA Raster PSSW

        self._test_calculation(
            1.5, 4.90, 3827.9, 73.0, 405.5,
            HeterodyneReceiver.A3, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            220, 0.0305, 0.15, 50, True, False, None,
            150, 300, 10, 10, False, None, False, False)

        self._test_calculation(
            1.5, 4.75, 3510.9, 73.0, 405.5,
            HeterodyneReceiver.A3, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            220, 0.0305, 0.15, 50, True, False, None,
            150, 300, 10, 10, True, None, False, False)

    def test_rxw(self):
        # RxW Grid PSSW

        self._test_calculation(
            2.5, 41.90, 11183.5, 478.4, 2208.2,
            HeterodyneReceiver.WD, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            670, 0.0610, 0.04, 30, False, False, 100,
            None, None, None, None, None, None, False, False)

        self._test_calculation(
            2.5, 20.90, 5618.5, 478.4, 2208.2,
            HeterodyneReceiver.WD, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            670, 0.0610, 0.04, 30, False, True, 100,
            None, None, None, None, None, None, False, False)

        # RxW Grid BMSW

        self._test_calculation(
            3.5, 26.80, 5244.8, 636.1, 4693.2,
            HeterodyneReceiver.WD, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            640, 0.0610, 0.06, 20, False, True, 81,
            None, None, None, None, None, None, False, False)

        # RxW Jiggle BMSW

        self._test_calculation(
            0.75, 118.70, 19998.9, 544.9, 1510.7,
            HeterodyneReceiver.WD, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            690, 0.0305, 0.02, 10, False, True, 121,
            None, None, None, None, None, None, False, False)

        # RxW Jiggle PSSW

        self._test_calculation(
            4.5, 148.50, 3354.4, 521.8, 21172.4,
            HeterodyneReceiver.WD, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            700, 0.488, 0.11, 15, False, False, 9,
            None, None, None, None, None, None, True, False)

        # RxW Raster PSSW

        self._test_calculation(
            5.0, 34.20, 133325.9, 632.1, 7570.6,
            HeterodyneReceiver.WD, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            645, 0.061, 0.065, 45, False, True, None,
            400, 200, 5, 5, False, None, False, False)

    def test_harp(self):
        # HARP Grid PSSW

        self._test_calculation(
            0.05, 309.30, 837.8, 105, 339.6,
            HeterodyneReceiver.HARP, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            345, 0.488, 0.1, 35, False, False, 1,
            None, None, None, None, None, None, False, False)

        # HARP Grid BMSW

        self._test_calculation(
            0.25, 115.70, 1745.3, 137.6, 1237.2,
            HeterodyneReceiver.HARP, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            330, 0.488, 0.18, 55, False, False, 6,
            None, None, None, None, None, None, False, False)

        # HARP Jiggle PSSW

        self._test_calculation(
            0.2, 18.50, 598.0, 115.3, 595.0,
            HeterodyneReceiver.HARP, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            365, 0.977, 0.11, 45, False, False, 16,
            None, None, None, None, None, None, False, False)

        # HARP Jiggle BMSW

        self._test_calculation(
            0.2, 155.50, 6024.6, 111.1, 439.6,
            HeterodyneReceiver.HARP, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            355, 0.061, 0.11, 45, False, False, 25,
            None, None, None, None, None, None, False, False)

        # HARP Raster PSSW

        self._test_calculation(
            0.5, 9.60, 22906.3, 105.0, 1163.0,
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            345, 0.977, 0.25, 50, False, False, None,
            1800, 900, 7.27, 116.4, False, True, False, False)

        self._test_calculation(
            0.5, 9.7, 24221.8, 105.0, 1163.0,
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            345, 0.977, 0.25, 50, False, False, None,
            1800, 900, 7.27, 116.4, True, True, False, False,
            tol_factor=10.0)

        self._test_calculation(
            0.5, 0.2, 1827.9, 137.6, 628.7,
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            330, 0.977, 0.04, 75, False, False, None,
            300, 400, 7.27, 7.3, False, True, False, False)

        self._test_calculation(
            0.75, 24.6, 25206.5, 113.8, 688.9,
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            340, 0.0305, 0.065, 75, False, False, None,
            800, 400, 7.27, 58.2, False, True, False, False)
