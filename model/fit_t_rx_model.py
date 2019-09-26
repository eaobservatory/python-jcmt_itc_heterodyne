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
    fit_t_rx_model.py [-v|-q] [--remove-outliers] [--out <outfile>] [--out-trx <trxfile>] <file>...

Options:
    --remove-outliers       Remove outliers
    --out <outfile>         File in which to store fitted data
    --out-trx <trxfile>     File in which to store t_rx parameters
    --verbose, -v           Verbose
    --quiet, -q             Quiet
"""

from __future__ import division, print_function

from collections import namedtuple
import logging
from math import sin, cos
import sys

from docopt import docopt
import numpy as np
from scipy.optimize import minimize

from jcmt_itc_heterodyne import HeterodyneReceiver
from eao_util.fitting import pre_bin_data

logger = logging.getLogger(sys.argv[0])

DataPoint = namedtuple('DataPoint', ('freq', 'eta_sky', 't_sys'))

eta_tel = HeterodyneReceiver.get_receiver_info(HeterodyneReceiver.HARP).eta_tel
t_rx_data = HeterodyneReceiver.get_receiver_info(HeterodyneReceiver.HARP).t_rx
freq_off = t_rx_data[0]
freq_scale = t_rx_data[1]
orig_coeffs = t_rx_data[2:]

data = []


def main():
    args = docopt(__doc__)
    logging.basicConfig(level=(
        logging.DEBUG if args['--verbose'] else (
            logging.WARNING if args['--quiet'] else logging.INFO)))

    for filename in args['<file>']:
        logger.debug('Reading file: %s', filename)
        with open(filename) as f:
            for line in f:
                if not line:
                    continue
                (freq, eta_sky, t_sys) = line.strip().split()
                freq = float(freq)
                eta_sky = float(eta_sky)
                t_sys = float(t_sys)

                if args['--remove-outliers']:
                    t_sys_ratio = calculate_t_sys(
                        freq, eta_sky, orig_coeffs) / t_sys
                    if t_sys_ratio < 0.5 or t_sys_ratio > 1.5:
                        logger.info(
                            'Removing outlier: %s with ratio %f',
                            line.strip(), t_sys_ratio)
                        continue

                data.append(DataPoint(freq, eta_sky, t_sys))

    result = minimize(
        merit_function, x0=orig_coeffs, method='Nelder-Mead',
        options={'disp': False, 'maxiter': 10000, 'maxfev': 10000})
    logger.info('%r', result)

    new_coeffs = result.x.tolist()
    if args['--out-trx'] is not None:
        with open(args['--out-trx'], 'w') as f:
            for coeff in new_coeffs:
                print('{}'.format(coeff), file=f)

    if args['--out'] is not None:
        with open(args['--out'], 'w') as f:
            for point in data:
                t_sys = calculate_t_sys(point.freq, point.eta_sky, new_coeffs)
                print(point.freq, point.eta_sky, point.t_sys, t_sys, file=f)


def merit_function(coeffs):
    sum_sq = 0.0

    for point in data:
        # Squared difference method:
        # sum_sq += (
        #     point.t_sys - calculate_t_sys(
        #         point.freq, point.eta_sky, coeffs)) ** 2

        # Squared difference of ratio from 1 method:
        sum_sq += (
            calculate_t_sys(point.freq, point.eta_sky, coeffs) /
            point.t_sys - 1.0) ** 2

    return sum_sq


def calculate_t_sys(freq, eta_sky, coeffs):
    (a, b, c, d, e, f, g, h, i, j, k, l, m) = coeffs

    x = freq_scale * (freq - freq_off)

    t_rx = (
        a + b*sin(x) + c*cos(x) + d*sin(2*x) + e*cos(2*x) +
        f*sin(3*x) + g*cos(3*x) + h*sin(4*x) + i*cos(4*x) +
        j*sin(5*x) + k*cos(5*x) + l*sin(6*x) + m*cos(6*x))

    t_sky = 260.0 * (1 - eta_sky)
    t_tel = 265.0 * (1 - eta_tel)

    return (t_rx + eta_tel * t_sky + t_tel) / (eta_sky * eta_tel)


if __name__ == '__main__':
    main()
