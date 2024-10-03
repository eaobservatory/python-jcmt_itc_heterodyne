# Copyright (C) 2024 East Asian Observatory
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


class ITCMethodsTest(TestCase):
    def test_combine_rms(self):
        itc = HeterodyneITC()

        self.assertAlmostEqual(itc._combine_rms([2]), 2, delta=0.01)
        self.assertAlmostEqual(itc._combine_rms([2, 2]), 1.41, delta=0.01)
        self.assertAlmostEqual(itc._combine_rms([2, 2, 2, 2]), 1, delta=0.01)
