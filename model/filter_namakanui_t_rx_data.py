#!/usr/bin/env python2

# Copyright (C) 2021 East Asian Observatory
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
filter_namakanui_t_rx_data - Filter receiver temperature data

Usage:
    filter_namakanui_t_rx_data [options] <filename>...

Options:
    --smooth                    Apply smoothing
    --method <method>           Smoothing method [default: mean]
    --width <width>             Smoothing width [default: 3]
    --despiketolerance <value>  Despking fractional tolerance [default: 0.1]
    --despikeref <function>     Despking reference function [default: min]
    --compress                  Apply compression
    --tolerance <tolerance>     Compression tolerance [default: 0.5]
    --lo2 <numbers>             LO2s to include (1-indexed, comma-separated)
    --pol <number>              Polarization to use
    --if <frequency>            Select values matching IF frequency
    --ifrelation                Output Trx vs IF instead of vs LO
    --prefix <prefix>           Output filename prefix
    --json                      Also write JSON (for receiver info file)
    --verbose, -v               Verbose
    --quiet, -q                 Quiet
"""


from __future__ import print_function

from collections import namedtuple
import logging
import re
from statistics import mean, median
import sys

from docopt import docopt
from eao_util.interpolation import compress_list

Measurement = namedtuple('Measurement', ('lo', 'if_', 'lsb', 'usb'))

logger = logging.getLogger(sys.argv[0])


def main():
    args = docopt(__doc__)

    logging.basicConfig(level=(
        logging.DEBUG if args['--verbose'] else (
            logging.WARNING if args['--quiet'] else logging.INFO)))

    lo2s = None
    if args['--lo2']:
        lo2s = [int(x) for x in args['--lo2'].split(',')]
        dcm_lo2 = get_dcm_lo2_mapping()

    pol = None
    if args['--pol']:
        pol = int(args['--pol'])

    if_ = None
    if args['--if']:
        if_ = float(args['--if'])

    prefix = ''
    if args['--prefix']:
        prefix = '{}_'.format(args['--prefix'])

    pattern = re.compile('^trx_([01])([UL])_dcm([0-9]+)$')

    data = []
    for filename in args['<filename>']:
        if filename.endswith('.txt'):
            format_csv = False
        elif filename.endswith('.csv'):
            format_csv = True
        else:
            raise Exception('Filename {!r} is not .txt or .csv'.format(filename))

        logger.info('Reading file %s', filename)
        with open(filename) as f:
            cols = None
            header = None

            for line in f:
                line = line.strip()

                if not line:
                    continue

                if format_csv:
                    if cols is None:
                        cols = line.split(',')[1:]
                        continue

                    vals = line.split(',')[1:]

                else:
                    if line.startswith('#'):
                        header = line[1:]
                        continue

                    if cols is None:
                        cols = header.split(' ')

                    vals = line.split(' ')

                assert(len(vals) == len(cols))

                row = dict(zip(cols, vals))

                lo_freq = float(row['lo_ghz'])
                if_freq = None
                if 'if_ghz' in row:
                    if_freq = float(row['if_ghz'])

                if if_:
                    if if_freq is None:
                        raise Exception('if_ghz column not present')

                    if not abs(if_freq - if_) < 0.05:
                        continue

                sum_lsb = 0.0
                n_lsb = 0
                sum_usb = 0.0
                n_usb = 0

                for (key, val) in row.items():
                    match = pattern.match(key)
                    if match:
                        if pol is not None:
                            if int(match.group(1)) != pol:
                                continue

                        if lo2s:
                            lo2 = dcm_lo2[int(match.group(3))]

                            if lo2 not in lo2s:
                                continue

                        t_rx = float(val)

                        if match.group(2) == 'L':
                            sum_lsb += t_rx
                            n_lsb += 1

                        elif match.group(2) == 'U':
                            sum_usb += t_rx
                            n_usb += 1

                data.append(Measurement(
                    lo_freq,
                    if_freq,
                    (None if not n_lsb else (sum_lsb / n_lsb)),
                    (None if not n_usb else (sum_usb / n_usb))))

    # Average data from multiple files?
    if len(args['<filename>']) > 1:
        filtered = []
        keys = sorted(set((x.lo, x.if_) for x in data))
        for (lo, if_) in keys:
            sum_lsb = 0.0
            sum_usb = 0.0
            n_lsb = 0
            n_usb = 0

            for entry in data:
                if (entry.lo == lo and entry.if_ == if_):
                    if entry.lsb is not None:
                        sum_lsb += entry.lsb
                        n_lsb += 1
                    if entry.usb is not None:
                        sum_usb += entry.usb
                        n_usb += 1

            filtered.append(Measurement(
                lo,
                if_,
                (None if not n_lsb else (sum_lsb / n_lsb)),
                (None if not n_usb else (sum_usb / n_usb))))

        data = filtered

    base_suffix = ''

    if args['--ifrelation']:
        key = 'if_'
        sidebands = ('mean',)
        base_suffix = '{}_{}'.format(base_suffix, 'if')

        filtered = []

        ifs = sorted(set(x.if_ for x in data))

        for if_ in ifs:
            sum_lsb = 0.0
            sum_usb = 0.0
            n = 0
            for entry in data:
                if entry.if_ == if_:
                    n += 1
                    sum_lsb += entry.lsb
                    sum_usb += entry.usb
            filtered.append(Measurement(
                None, if_, sum_lsb / n, sum_usb / n))

        data = subtract_min(filtered)

    else:
        key = 'lo'
        data = sorted(data, key=lambda x: x.lo)

        have_lsb = False
        have_usb = False
        for entry in data:
            if entry.lsb is not None:
                have_lsb = True
            if entry.usb is not None:
                have_usb = True

        if have_lsb and have_usb:
            sidebands = ('lsb', 'usb')
        elif have_lsb:
            sidebands = ('lsb',)
        elif have_usb:
            sidebands = ('usb',)
        else:
            raise Exception('can not find sideband')

    for sideband in sidebands:
        suffix = base_suffix
        if sideband == 'mean':
            data_sb = [(getattr(x, key), (x.lsb + x.usb) / 2.0) for x in data]
        else:
            data_sb = [(getattr(x, key), getattr(x, sideband)) for x in data]

        if args['--smooth']:
            suffix = '{}_{}'.format(suffix, 'sm')
            methods = args['--method'].split(',')
            widths = [int(x) for x in args['--width'].split(',')]
            despiketolerance = [
                float(x) for x in args['--despiketolerance'].split(',')]
            despikeref = args['--despikeref'].split(',')

            for (method, width) in zip(methods, widths):
                if method == 'mean':
                    logger.info('Applying sliding mean smooth')
                    data_sb = smooth_mean(data_sb, n=width)

                elif method == 'median':
                    logger.info('Applying sliding median smooth')
                    data_sb = smooth_median(data_sb, n=width)

                elif method == 'minimum':
                    logger.info('Applying sliding minimum smooth')
                    data_sb = smooth_min(data_sb, n=width)

                elif method == 'maximum':
                    logger.info('Applying sliding maximum smooth')
                    data_sb = smooth_max(data_sb, n=width)

                elif method == 'midrange':
                    logger.info('Applying midrange smooth')
                    data_sb = smooth_midrange(data_sb, n=width)

                elif method == 'despike':
                    logger.info('Applying despiking filter')
                    data_sb = smooth_despike(
                        data_sb, n=width,
                        tolerance=despiketolerance.pop(0),
                        ref_func=despikeref.pop(0))

                else:
                    raise Exception(
                        'Unknown smoothing method "{}"'.format(method))

        if args['--compress']:
            tolerance = float(args['--tolerance'])
            data_sb = compress_list(data_sb, tolerance=tolerance)
            logger.info(
                'After compression: %s %i point(s)', sideband, len(data_sb))
            suffix = '{}_{}'.format(suffix, 'comp')

        if args['--ifrelation']:
            min_ = min(x[1] for x in data_sb)
            data_sb = [(x[0], x[1] - min_) for x in data_sb]

        outfile = '{}trx_{}{}.txt'.format(prefix, sideband, suffix)
        logger.info('Writing %s', outfile)
        with open(outfile, 'w') as f:
            for (freq, value) in data_sb:
                print(freq, '{:.1f}'.format(value), file=f)

        if args['--json']:
            with open(outfile.replace('.txt', '.json'), 'w') as f:
                for (n, (freq, value)) in enumerate(data_sb, start=1):
                    print('            [{}, {:.1f}]{}'.format(
                        freq, value,
                        ('' if n >= len(data_sb) else ',')), file=f)


def smooth_min(data, n):
    return smooth_func(data, n, min)


def smooth_max(data, n):
    return smooth_func(data, n, max)


def smooth_midrange(data, n):
    return smooth_func(data, n, lambda xs: ((min(xs) + max(xs)) / 2.0))


def smooth_func(data, n, func):
    smoothed = []

    length = len(data)
    for i in range(0, length):
        vals = []
        for j in range(i - n, i + n + 1):
            if 0 <= j < length:
                vals.append(data[j][1])

        smoothed.append([data[i][0], func(vals)])

    return smoothed


def smooth_despike(data, n, tolerance, ref_func):
    if ref_func == 'min':
        func = min
        comparison = abs
    elif ref_func == 'median':
        func = median
        comparison = lambda x: x
    else:
        raise Exception(
            'Unknown reference function "{}"'.format(ref_func))

    smoothed = []

    length = len(data)
    for i in range(0, length):
        vals = []
        for j in range(i - n, i + n + 1):
            if 0 <= j < length:
                vals.append(data[j][1])

        ref = func(vals)
        if comparison(data[i][1] - ref) < tolerance * ref:
            smoothed.append([data[i][0], data[i][1]])

    return smoothed


def smooth_mean(data, n):
    return smooth_func(data, n, mean)


def smooth_median(data, n):
    return smooth_func(data, n, median)


def subtract_min(data):
    min_lsb = 1000000.0
    min_usb = 1000000.0
    for entry in data:
        if entry.lsb < min_lsb:
            min_lsb = entry.lsb
        if entry.usb < min_usb:
            min_usb = entry.usb

    return [x._replace(lsb=x.lsb - min_lsb, usb=x.usb - min_usb) for x in data]


def get_dcm_lo2_mapping():
    from taco import Taco

    taco = Taco(lang='perl')
    taco.import_module('JCMT::ACSIS::HWMap')

    dcm_lo2 = {}
    for entry in taco.construct_object(
            'JCMT::ACSIS::HWMap', File='cm_wire_file.txt').call_method(
                'cm_map', context='list'):
        dcm_lo2[int(entry['DCM_ID'])] = int(entry['LO2'])

    return dcm_lo2


if __name__ == '__main__':
    main()
