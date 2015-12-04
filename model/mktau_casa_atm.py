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

# mktau_casa_atm - Generate "tau" files using CASA's ATM model
#
# This script generates "tau" data files which could be used by the
# heterodyne ITC.  These are a series of files, named by the 225 GHz
# opacity.  They tabulate the opacity as a function of frequency for
# the given sky conditions.  The ITC linearly interpolates both within
# the files and between them to obtain an opacity value for a given
# 225 GHz opacity and frequency.
#
# This script uses the ATM model provided with CASA.  Parameters which
# you may wish to consider adjusting are:
#   * The altitude, temperature and pressure in the call to initAtmProfile.
#   * The frequency range and sampling, in the 2nd call to initSpectralWindow.
#   * The tolerance in the output file (optional argument to compress_list).
#
# Run with:
#     casapy -c mkatm.py

from __future__ import print_function

from eao_util.interpolation import compress_list
from jcmt_itc_heterodyne import HeterodyneReceiver

# Set up basic parameters for JCMT.
at.initAtmProfile(
    altitude=qa.quantity(4125, 'm'),
    temperature=qa.quantity(273.0, 'K'),
    pressure=qa.quantity(625.0, 'mbar'))

# Determine at which frequencies the ITC needs "tau" files.
taus = list(HeterodyneReceiver._tau_data.keys())
mms = []

# Configure ATM to look at 225 GHz and perform a binary search to determine
# the "WH2O" parameter which gives each desired 225 GHz opacity.
at.initSpectralWindow(1, qa.quantity(225, 'GHz'), qa.quantity(1, 'Hz'))

for tau in taus:
    mm_min = 0.1
    mm_max = 10.0

    while True:
        mm_mid = (mm_min + mm_max) / 2.0

        at.setUserWH2O(qa.quantity(mm_mid, 'mm'))

        tau_mid = at.getWetOpacity()['value'][0] + at.getDryOpacity()

        if abs(tau_mid - tau) < 0.0000001:
            break

        if tau_mid > tau:
            mm_max = mm_mid
        else:
            mm_min = mm_mid

    mms.append(mm_mid)

# Now reconfigure ATM to use the whole frequency range in which we are
# interested and generate data for each of the desired conditions.
at.initSpectralWindow(1, qa.quantity(600, 'GHz'), qa.quantity(800, 'GHz'),
                      qa.quantity(0.01, 'GHz'))

for (tau, mm) in zip(taus, mms):
    at.setUserWH2O(qa.quantity(mm, 'mm'))
    values = []

    for i in range(at.getNumChan()):
        freq = at.getChanFreq(chanNum=i)['value'][0]

        d = at.getWetOpacity(nc=i)['value'][0] + at.getDryOpacity(nc=i)

        values.append((freq, d))

    values = compress_list(values)

    filename = 'tau{}.dat'.format('{:.03f}'.format(tau)[2:])
    print('Writing:', filename)

    with open(filename, 'w') as f:
        for (freq, d) in values:
            print(freq, d, file=f)
