# Copyright (C) 2025 East Asian Observatory
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

from jcmt_itc_heterodyne.error import HeterodyneITCError, \
    HeterodyneITCFreqError


class ErrorTest(TestCase):
    def test_error(self):
        with self.assertRaisesRegex(
                HeterodyneITCError,
                r'^The EXAMPLE FREQ \(123\.457 GHz\) is not within the '
                r'available range \(234\.6 - 345\.7 GHz\)\.$'):
            raise HeterodyneITCFreqError(
                'EXAMPLE FREQ', 123.456789, 234.567, 345.678)
