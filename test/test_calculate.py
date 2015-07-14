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

        result = itc._calculate(
            HeterodyneITC.RMS_TO_TIME, 0.6,
            HeterodyneReceiver.A3, HeterodyneITC.GRID, HeterodyneITC.PSSW,
            233, 0.0192, 0.23, 25, True, False, 25,
            None, None, None, None, None, None, False, False)
        self.assertAlmostEqual(result['int_time'], 77.10, places=2)
        self.assertAlmostEqual(result['elapsed_time'], 5187.9, places=1)
