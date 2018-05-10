# Copyright (C) 2018 East Asian Observatory
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
from unittest import TestCase

from jcmt_itc_heterodyne.line_catalog import get_line_catalog

if version_info[0] < 3:
    string_type = unicode
else:
    string_type = str


class LineCatalogTest(TestCase):
    def test_line_catalog(self):
        # Check that we can get the line catalog.
        catalog = get_line_catalog()
        self.assertIsInstance(catalog, OrderedDict)
        self.assertGreater(len(catalog), 10)

        # Fetching the catalog again should return the same object.
        catalog2 = get_line_catalog()
        self.assertIs(catalog2, catalog)

        # Check type of entries.
        for (species, transitions) in catalog.items():
            self.assertIsInstance(species, string_type)
            self.assertIsInstance(transitions, OrderedDict)

            self.assertGreater(len(transitions), 0)

            for (transition, frequency) in transitions.items():
                self.assertIsInstance(transition, string_type)
                self.assertIsInstance(frequency, float)

        # Check a specific entry.
        self.assertIn('CO', catalog)
        self.assertIn('3 - 2', catalog['CO'])
        self.assertAlmostEqual(catalog['CO']['3 - 2'], 345.796, places=3)
