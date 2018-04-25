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

from codecs import ascii_decode
from collections import namedtuple, OrderedDict
from pkgutil import get_data
import re
from sys import version_info

from xml.etree import ElementTree as etree

if version_info[0] < 3:
    def element_attr(element, attr):
        text = element.get(attr)
        if isinstance(text, unicode):
            return text
        return ascii_decode(text, 'replace')[0]

else:
    def element_attr(element, attr):
        return element.get(attr)


SpeciesInfo = namedtuple(
    'SpeciesInfo',
    ('name', 'transitions'))

TransitionInfo = namedtuple(
    'TransitionInfo',
    ('name', 'frequency'))


line_catalog = None


def get_line_catalog():
    """
    Fetch the line catalog, reading it from the XML file if necessary.

    The catalog is returned as an OrderedDict of species names.  Each
    entry is another OrderedDict of transitions giving frequencies in GHz.
    """

    global line_catalog

    if line_catalog is None:
        line_catalog = OrderedDict()
        species_list = []

        doc = etree.fromstring(get_data(
            'jcmt_itc_heterodyne', 'data/lineCatalog.xml'))

        for species in doc.findall('species'):
            species_name = element_attr(species, 'name')

            transitions = []

            for transition in species.findall('transition'):
                transition_name = element_attr(transition, 'name')
                transition_freq = float(
                    element_attr(transition, 'frequency')) / 1000.0

                transitions.append(TransitionInfo(
                    name=transition_name, frequency=transition_freq))

            # Skip species for which no transitions are defined.
            if not transitions:
                continue

            # Create catalog entry by sorting transitions by frequency.
            species_list.append(SpeciesInfo(
                name=species_name, transitions=OrderedDict(
                    sorted(transitions, key=lambda x: x.frequency))))

        line_catalog = OrderedDict(sorted(
            species_list, key=lambda x: _name_sort_key(x.name)))

    return line_catalog


def _name_sort_key(name):
    """
    Create "simple" version of a species name, for sorting
    and return it as a tuple with the removed parts and the
    original name.
    """

    main = []
    extra = []

    for part in (name.split('-')):
        (extra if re.match(r'^(\d+|[a-z])$', part) else main).append(part)

    return (''.join(main), ''.join(extra), name)
