#!/usr/bin/env python

# Copyright (C) 2019 East Asian Observatory
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

"""
Usage:
    bin_combined_data.py [-v|-q] <file>...

Options:
    --verbose, -v           Verbose
    --quiet, -q             Quiet
"""

from __future__ import division, print_function

import logging
import math
import sys

from docopt import docopt

from jcmt_itc_heterodyne import HeterodyneReceiver
from eao_util.fitting import pre_bin_data

logger = logging.getLogger(sys.argv[0])


def main():
    args = docopt(__doc__)
    logging.basicConfig(level=(
        logging.DEBUG if args['--verbose'] else (
            logging.WARNING if args['--quiet'] else logging.INFO)))

    data = []
    columns = [0.25, 0.25, True]

    for filename in args['<file>']:
        if 'USB' in filename:
            is_usb = True
        elif 'LSB' in filename:
            is_usb = False
        else:
            raise Exception('Unable to determine sideband from file name')

        with open(filename) as f:
            logger.debug('Reading file: %s', filename)
            for line in f:
                if 'None' in line:
                    continue

                (utdate, obsnum, subsysnr, lofreq, iffreq, rffreq, t_rx, t_sys,
                    wvmtau, elevation) = line.strip().split(' ')

                rffreq = float(rffreq)
                elevation = float(elevation)
                wvmtau = float(wvmtau)
                t_sys = float(t_sys)

                if is_usb:
                    if rffreq < 340.0:
                        continue
                else:
                    if rffreq > 363.0:
                        continue

                if t_sys > 3000.0:
                    continue

                tau = HeterodyneReceiver.get_interpolated_opacity(
                    tau_225=wvmtau, freq=rffreq)

                eta_sky = math.exp(- tau / math.cos(
                    math.radians(90.0 - elevation)))

                if eta_sky > 0.95 or eta_sky < 0.25:
                    continue

                data.append([rffreq, eta_sky, t_sys])

    result = pre_bin_data(data, columns, n_min=6)

    for row in result:
        print(*row)


if __name__ == '__main__':
    main()
