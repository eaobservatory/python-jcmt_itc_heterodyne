# Copyright (C) 2015-2025 East Asian Observatory
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

from collections import OrderedDict
from sys import version_info
from .compat import TestCase, string_type

from jcmt_itc_heterodyne import HeterodyneITCError, HeterodyneReceiver
from jcmt_itc_heterodyne.receiver import ArrayInfo, ReceiverInfo


class ReceiverTest(TestCase):
    def test_receiver_names(self):
        names = HeterodyneReceiver.get_receiver_names()
        self.assertIsInstance(names, OrderedDict)
        self.assertTrue(len(names) > 0)

        for (receiver, name) in names.items():
            self.assertIsInstance(receiver, int)
            self.assertIsInstance(name, string_type)

    def test_receiver_info(self):
        info = HeterodyneReceiver.get_receiver_info(HeterodyneReceiver.HARP)
        self.assertIsInstance(info, ReceiverInfo)
        self.assertIsInstance(info.array, ArrayInfo)
        self.assertIsInstance(info.array.jiggle_patterns, OrderedDict)
        self.assertIsInstance(info.array.scan_spacings, OrderedDict)
        self.assertIsInstance(info.array.fraction_available, float)

        info = HeterodyneReceiver.get_receiver_info(HeterodyneReceiver.A3)
        self.assertIsInstance(info, ReceiverInfo)
        self.assertIsNone(info.array, ArrayInfo)

        receivers = HeterodyneReceiver.get_all_receivers()
        self.assertIsInstance(receivers, OrderedDict)

        for (receiver, info) in receivers.items():
            self.assertIsInstance(receiver, int)

            self.assertLessEqual(info.f_if, info.f_if_max)
            self.assertGreaterEqual(info.f_if, info.f_if_min)

    def test_interpolated_t_rx(self):
        self.assertAlmostEqual(HeterodyneReceiver.get_interpolated_t_rx(
            HeterodyneReceiver.A3, 255.5), 124.5)

    def test_best_sideband(self):
        info = HeterodyneReceiver.get_receiver_info(HeterodyneReceiver.UU)

        sideband = HeterodyneReceiver._find_best_sideband(info, 240)
        self.assertEqual(sideband, 'LSB')
        sideband = HeterodyneReceiver._find_best_sideband(info, 260)
        self.assertEqual(sideband, 'USB')

        # Test we get an error without the "best_sideband" attribute.
        info = info._replace(best_sideband=None)

        with self.assertRaisesRegex(
                HeterodyneITCError,
                'does not have preferred sideband data'):
            HeterodyneReceiver._find_best_sideband(info, 240)

        # Test a receiver where only one sideband is available.
        info = HeterodyneReceiver.get_receiver_info(HeterodyneReceiver.ALAIHI)

        sideband = HeterodyneReceiver._find_best_sideband(info, 90)
        self.assertEqual(sideband, 'USB')

        # Should get an error if there is no useable sideband data.
        trx_data = info.t_rx_usb
        info = info._replace(t_rx_usb=None)

        with self.assertRaisesRegex(
                HeterodyneITCError,
                'appears to have no available sideband'):
            HeterodyneReceiver._find_best_sideband(info, 90)

        # Try setting the data for the LSB side so it can be selected.
        info = info._replace(t_rx_lsb=trx_data)

        sideband = HeterodyneReceiver._find_best_sideband(info, 90)
        self.assertEqual(sideband, 'LSB')
