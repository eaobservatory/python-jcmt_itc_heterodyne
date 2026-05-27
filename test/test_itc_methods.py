# Copyright (C) 2024-2026 East Asian Observatory
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

from .compat import TestCase

from jcmt_itc_heterodyne import HeterodyneITC, HeterodyneITCError, \
    HeterodyneReceiver


class ITCMethodsTest(TestCase):
    def test_combine_rms(self):
        itc = HeterodyneITC()

        self.assertAlmostEqual(itc._combine_rms([2]), 2, delta=0.01)
        self.assertAlmostEqual(itc._combine_rms([2, 2]), 1.41, delta=0.01)
        self.assertAlmostEqual(itc._combine_rms([2, 2, 2, 2]), 1, delta=0.01)

    def test_raster_parameters(self):
        # Test the array_overscan_x/y options for array receivers.

        itc = HeterodyneITC()
        array_info = HeterodyneReceiver.get_receiver_info(
                HeterodyneReceiver.HARP).array

        for (dy, hits, nre) in (
                (116.4, 1, 2),
                (58.2, 2, 4),
                (29.1, 4, 7),
                (14.6, 8, 13),
                (7.3, 16, 25)):
            extra = {}

            # No overscan.
            (nr, np, ms) = itc._get_raster_parameters(
                180, 180, 7.27, dy, array_info, False, False, False, extra)

            self.assertEqual(extra['multiscan_passes'], hits)
            self.assertEqual(np, 25)
            self.assertEqual(nr, nre)

            # Overscan in x only.
            extra.clear()
            (nr_, npos, ms) = itc._get_raster_parameters(
                180, 180, 7.27, dy, array_info, True, False, False, extra)

            self.assertEqual(npos, 42)
            self.assertEqual(nr_, nr)

            # Overscan in y only.
            extra.clear()
            (nros, np_, ms) = itc._get_raster_parameters(
                180, 180, 7.27, dy, array_info, False, True, False, extra)

            self.assertEqual(np_, np)
            self.assertEqual(nros, nr + hits - 1)

            # Re-enter the modified height without overscan.
            yos = extra['overscanned_dim_y']
            extra.clear()
            (nros_, np__, ms) = itc._get_raster_parameters(
                180, yos, 7.27, dy, array_info, False, False, False, extra)

            self.assertEqual(np__, np)
            self.assertEqual(nros_, nros)
