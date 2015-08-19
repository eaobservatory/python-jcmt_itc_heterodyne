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
            0.6, 78.70, 5293.9, 62.0, 407.8,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            233, 0.0192, 0.23, 25, True, False, 25,
            None, None, None, None, None, False, False)

        self._test_calculation(
            0.6, 41.40, 2822.8, 62.0, 295.6,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            233, 0.0192, 0.12, 25, True, False, 25,
            None, None, None, None, None, False, False)

        self._test_calculation(
            0.2, 590.70, 78347.8, 85.0, 372.3,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            215, 0.0192, 0.12, 45, True, False, 50,
            None, None, None, None, None, False, False)

        self._test_calculation(
            0.2, 12.90, 592.8, 62.0, 300.0,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            266, 0.488, 0.09, 30, True, False, 15,
            None, None, None, None, None, False, False)

        # RxA Grid BMSW

        self._test_calculation(
            0.2, 13.80, 1702.6, 96.0, 379.6,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            260, 0.488, 0.09, 30, True, False, 49,
            None, None, None, None, None, False, False)

        self._test_calculation(
            0.2, 24.20, 2910.3, 96.0, 379.6,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            260, 0.488, 0.09, 30, True, False, 49,
            None, None, None, None, None, True, False)

        self._test_calculation(
            0.2, 24.20, 3492.4, 96.0, 379.6,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            260, 0.488, 0.09, 30, True, False, 49,
            None, None, None, None, None, True, True)

        # RxA Jiggle BMSW

        self._test_calculation(
            0.25, 425.30, 6581.6, 185.0, 609.6,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            250, 0.0305, 0.11, 20, True, False, 9,
            None, None, None, None, None, False, False)

        self._test_calculation(
            0.15, 394.7, 22795.2, 79.0, 287.7,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            240, 0.0305, 0.07, 10, True, False, 25,
            None, None, None, None, None, True, False)

        # RxA Jiggle PSSW

        self._test_calculation(
            0.3, 145.6, 17559.3, 68.0, 349.5,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            235, 0.0305, 0.03, 80, True, False, 49,
            None, None, None, None, None, True, False)

        self._test_calculation(
            0.05, 46.5, 6671.4, 68.0, 250.0,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            235, 0.977, 0.03, 60, True, False, 81,
            None, None, None, None, None, False, False)

        # RxA Raster PSSW

        self._test_calculation(
            1.5, 4.70, 3697.7, 73.0, 398.9,
            HeterodyneReceiver.A3, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            220, 0.0305, 0.15, 50, True, False, None,
            150, 300, 10, 10, False, False, False)

        self._test_calculation(
            1.5, 4.60, 3415.1, 73.0, 398.9,
            HeterodyneReceiver.A3, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            220, 0.0305, 0.15, 50, True, False, None,
            150, 300, 10, 10, True, False, False,
            tol_factor=10.0)

    def test_rxw(self):
        # RxW Grid PSSW

        self._test_calculation(
            2.5, 43.10, 11501.5, 478.4, 2240.0,
            HeterodyneReceiver.WD, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            670, 0.0610, 0.04, 30, False, False, 100,
            None, None, None, None, None, False, False)

        self._test_calculation(
            2.5, 21.50, 5777.5, 478.4, 2240.0,
            HeterodyneReceiver.WD, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            670, 0.0610, 0.04, 30, False, True, 100,
            None, None, None, None, None, False, False)

        # RxW Grid BMSW

        self._test_calculation(
            3.5, 26.90, 5264.0, 636.1, 4705.7,
            HeterodyneReceiver.WD, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            640, 0.0610, 0.06, 20, False, True, 81,
            None, None, None, None, None, False, False)

        # RxW Jiggle BMSW

        self._test_calculation(
            0.75, 118.50, 19965.3, 544.9, 1509.3,
            HeterodyneReceiver.WD, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            690, 0.0305, 0.02, 10, False, True, 121,
            None, None, None, None, None, False, False)

        # RxW Jiggle PSSW

        self._test_calculation(
            4.5, 148.20, 3347.8, 521.8, 21151.5,
            HeterodyneReceiver.WD, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            700, 0.488, 0.11, 15, False, False, 9,
            None, None, None, None, None, True, False)

        # RxW Raster PSSW

        self._test_calculation(
            5.0, 34.70, 135263.2, 632.1, 7626.2,
            HeterodyneReceiver.WD, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            645, 0.061, 0.065, 45, False, True, None,
            400, 200, 5, 5, False, False, False)

    def test_harp(self):
        # HARP Grid PSSW

        self._test_calculation(
            0.05, 309.30, 837.8, 105, 339.6,
            HeterodyneReceiver.HARP, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            345, 0.488, 0.1, 35, False, False, 1,
            None, None, None, None, None, False, False)

        # HARP Grid BMSW

        self._test_calculation(
            0.25, 115.70, 1745.3, 137.6, 1237.2,
            HeterodyneReceiver.HARP, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            330, 0.488, 0.18, 55, False, False, 6,
            None, None, None, None, None, False, False)

        # HARP Jiggle PSSW

        self._test_calculation(
            0.2, 18.50, 598.0, 115.3, 595.0,
            HeterodyneReceiver.HARP, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            365, 0.977, 0.11, 45, False, False, 16,
            None, None, None, None, None, False, False)

        # HARP Jiggle BMSW

        self._test_calculation(
            0.2, 155.50, 6024.6, 111.1, 439.6,
            HeterodyneReceiver.HARP, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            355, 0.061, 0.11, 45, False, False, 25,
            None, None, None, None, None, False, False)

        # HARP Raster PSSW

        self._test_calculation(
            0.5, 9.60, 22906.3, 105.0, 1163.0,
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            345, 0.977, 0.25, 50, False, False, None,
            1800, 900, 7.27, 116.4, False, False, False)

        self._test_calculation(
            0.5, 9.7, 24221.8, 105.0, 1163.0,
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            345, 0.977, 0.25, 50, False, False, None,
            1800, 900, 7.27, 116.4, True, False, False,
            tol_factor=10.0)

        self._test_calculation(
            0.5, 0.2, 1827.9, 137.6, 628.7,
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            330, 0.977, 0.04, 75, False, False, None,
            300, 400, 7.27, 7.3, False, False, False)

        self._test_calculation(
            0.75, 24.6, 25206.5, 113.8, 688.9,
            HeterodyneReceiver.HARP, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            340, 0.0305, 0.065, 75, False, False, None,
            800, 400, 7.27, 58.2, False, False, False)
