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

# mktau_sma_am - Generate "tau" files using SMA's "am" routine
#
# This script generates "tau" data files which could be used by the
# heterodyne ITC.  These are a series of files, named by the 225 GHz
# opacity.  They tabulate the opacity as a function of frequency for
# the given sky conditions.  The ITC linearly interpolates both within
# the files and between them to obtain an opacity value for a given
# 225 GHz opacity and frequency.
#
# This script uses the "am" software from SMA.  Parameters which
# you may wish to consider adjusting are:
#   * The temperature parameter in run_am.
#   * The frequency range and sampling, in the 2nd call to run_am.
#   * The tolerance in the output file (optional argument to compress_list).
#
# Requirements:
#   * "am" should be in your path.
#   * You will need a configuration file suitable for Manuakea, such as the
#     example "2.5" provided for "am" (see the AM_CONFIG variable below).

from __future__ import print_function

import subprocess

from eao_util.interpolation import compress_list
from jcmt_itc_heterodyne import HeterodyneReceiver

# Set name of the "am" configuration file which we want to use.
# (This should perhaps be made a command line option.)
AM_CONFIG = 'MaunaKea_ex25.amc'


def main():
    # Determine at which frequencies the ITC needs "tau" files.
    taus = list(HeterodyneReceiver._tau_data.keys())
    mms = []

    # Perform a binary search to determine the "WH2O" parameter which gives
    # each desired 225 GHz opacity.
    for tau in taus:
        mm_min = 0.1
        mm_max = 10.0

        while True:
            mm_mid = (mm_min + mm_max) / 2.0

            values = run_am(225.0, 225.0, 0.01, mm_mid)

            assert len(values) == 1

            tau_mid = values[0][1]

            if abs(tau_mid - tau) < 0.0000001:
                break

            if tau_mid > tau:
                mm_max = mm_mid
            else:
                mm_min = mm_mid

        mms.append(mm_mid)

    # Generate data for each of the desired conditions.
    for (tau, mm) in zip(taus, mms):
        values = run_am(200.0, 1000.0, 0.01, mm)

        values = compress_list(values)

        filename = 'tau{}.dat'.format('{:.03f}'.format(tau)[2:])
        print('Writing:', filename)

        with open(filename, 'w') as f:
            for (freq, d) in values:
                print(freq, d, file=f)


def run_am(freq_min, freq_max, freq_res, mm):
    result = []

    # am returns bad status if there are narrow lines, so we can't just
    # use subprocess.check_output.
    p = subprocess.Popen(
        ['am', AM_CONFIG,
         str(freq_min), 'GHz',
         str(freq_max), 'GHz',
         str(freq_res), 'GHz',
         '0', 'deg',
         '277', 'K',  # Temperature parameter.
         str(mm),
         ],
        shell=False,
        stdout=subprocess.PIPE)

    (stdoutdata, stderrdata) = p.communicate()

    for line in stdoutdata.splitlines():
        (freq, tau, txn) = line.strip().split(' ')
        result.append((float(freq), float(tau)))

    return result


if __name__ == '__main__':
    main()