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
    def test_rxa(self):
        itc = HeterodyneITC()

        # RxA Grid PSSW

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 0.6,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            233, 0.0192, 0.23, 25, True, False, 25,
            None, None, None, None, None, None, False, False)
        self.assertAlmostEqual(result['extra']['t_rx'], 62.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 403.5, places=1)
        self.assertAlmostEqual(result['int_time'], 77.10, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 5187.9, places=1)

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 0.6,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            233, 0.0192, 0.12, 25, True, False, 25,
            None, None, None, None, None, None, False, False)
        self.assertAlmostEqual(result['extra']['t_rx'], 62.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 298.0, places=1)
        self.assertAlmostEqual(result['int_time'], 42.00, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 2862.5, places=1)

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 0.2,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            215, 0.0192, 0.12, 45, True, False, 50,
            None, None, None, None, None, None, False, False)
        self.assertAlmostEqual(result['extra']['t_rx'], 85.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 367.0, places=1)
        self.assertAlmostEqual(result['int_time'], 574.00, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 76135.0, places=1)

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 0.2,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            266, 0.488, 0.09, 30, True, False, 15,
            None, None, None, None, None, None, False, False)
        self.assertAlmostEqual(result['extra']['t_rx'], 62.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 303.5, places=1)
        self.assertAlmostEqual(result['int_time'], 13.20, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 604.7, places=1)

        # RxA Grid BMSW

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 0.2,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            260, 0.488, 0.09, 30, True, False, 49,
            None, None, None, None, None, None, False, False)
        self.assertAlmostEqual(result['extra']['t_rx'], 96.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 379.8, places=1)
        self.assertAlmostEqual(result['int_time'], 13.80, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 1702.6, places=1)

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 0.2,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            260, 0.488, 0.09, 30, True, False, 49,
            None, None, None, None, None, None, True, False)
        self.assertAlmostEqual(result['extra']['t_rx'], 96.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 379.8, places=1)
        self.assertAlmostEqual(result['int_time'], 24.20, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 2910.3, places=1)

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 0.2,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.BMSW,
            260, 0.488, 0.09, 30, True, False, 49,
            None, None, None, None, None, None, True, True)
        self.assertAlmostEqual(result['extra']['t_rx'], 96.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 379.8, places=1)
        self.assertAlmostEqual(result['int_time'], 24.20, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 3492.4, places=1)

        # RxA Jiggle BMSW

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 0.25,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            250, 0.0305, 0.11, 20, True, False, 9,
            None, None, None, None, None, None, False, False)
        self.assertAlmostEqual(result['extra']['t_rx'], 185.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 604.3, places=1)
        self.assertAlmostEqual(result['int_time'], 417.90, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 6468.8, places=1)

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 0.15,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.BMSW,
            240, 0.0305, 0.07, 10, True, False, 25,
            None, None, None, None, None, None, True, False)
        self.assertAlmostEqual(result['extra']['t_rx'], 79.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 287.5, places=1)
        self.assertAlmostEqual(result['int_time'], 394.3, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 22772.2, places=1)

        # RxA Jiggle PSSW

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 0.3,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            235, 0.0305, 0.03, 80, True, False, 49,
            None, None, None, None, None, None, True, False)
        self.assertAlmostEqual(result['extra']['t_rx'], 68.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 347.9, places=1)
        self.assertAlmostEqual(result['int_time'], 144.3, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 17403.2, places=1)

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 0.05,
            HeterodyneReceiver.A3, HeterodyneITC.JIGGLE, HeterodyneITC.PSSW,
            235, 0.977, 0.03, 60, True, False, 81,
            None, None, None, None, None, None, False, False)
        self.assertAlmostEqual(result['extra']['t_rx'], 68.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 249.6, places=1)
        self.assertAlmostEqual(result['int_time'], 46.4, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 6657.2, places=1)

        # RxA Raster PSSW

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 1.5,
            HeterodyneReceiver.A3, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            220, 0.0305, 0.15, 50, True, False, None,
            150, 300, 10, 10, False, None, False, False)
        self.assertAlmostEqual(result['extra']['t_rx'], 73.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 405.5, places=1)
        self.assertAlmostEqual(result['int_time'], 4.90, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 3827.9, places=1)

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 1.5,
            HeterodyneReceiver.A3, HeterodyneITC.RASTER, HeterodyneITC.PSSW,
            220, 0.0305, 0.15, 50, True, False, None,
            150, 300, 10, 10, True, None, False, False)
        self.assertAlmostEqual(result['extra']['t_rx'], 73.0, places=1)
        self.assertAlmostEqual(result['extra']['t_sys'], 405.5, places=1)
        self.assertAlmostEqual(result['int_time'], 4.75, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 3510.9, places=1)
