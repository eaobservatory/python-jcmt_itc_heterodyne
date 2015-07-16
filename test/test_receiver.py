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

from collections import OrderedDict
from unittest import TestCase

from jcmt_itc_heterodyne import HeterodyneReceiver
from jcmt_itc_heterodyne.receiver import ReceiverInfo


class ReceiverTest(TestCase):
    def test_receiver_names(self):
        names = HeterodyneReceiver.get_receiver_names()
        self.assertIsInstance(names, OrderedDict)
        self.assertTrue(len(names) > 0)

        for (receiver, name) in names.items():
            self.assertIsInstance(receiver, int)
            self.assertIsInstance(name, unicode)

    def test_receiver_info(self):
        info = HeterodyneReceiver.get_receiver_info(HeterodyneReceiver.HARP)
        self.assertIsInstance(info, ReceiverInfo)

    def test_interpolated_t_rx(self):
        self.assertAlmostEqual(HeterodyneReceiver.get_interpolated_t_rx(
            HeterodyneReceiver.A3, 255.5), 124.5)
