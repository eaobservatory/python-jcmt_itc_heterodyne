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

from distutils.core import setup
import sys

sys.path.insert(0, 'lib')
from jcmt_itc_heterodyne.version import version

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='jcmt_itc_heterodyne',
    version=version,
    description='JCMT Heterodyne Integration Time Calculator',
    long_description=long_description,
    url='https://github.com/eaobservatory/python-jcmt_itc_heterodyne',
    package_dir={'': 'lib'},
    packages=['jcmt_itc_heterodyne'],
    package_data={'jcmt_itc_heterodyne': [
        'data/receiver_info.json',
        'data/*.dat',
        'data/line_catalog.xml',
    ]})
