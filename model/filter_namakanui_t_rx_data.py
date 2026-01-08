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
    --clip                      Apply clipping
    --clip-n-stdev <value>      Number of std. dev. [default: 2.0]
    --if <frequency>            Select values matching IF frequency
    --ifrelation                Output Trx vs IF instead of vs LO
    --ifrelation-separate       Use separate sidebands in --ifrelation mode
    --lo-min <frequency>        Select values by LO frequency
    --lo-max <frequency>        Select values by LO frequency
    --prefix <prefix>           Output filename prefix
    --json                      Also write JSON (for receiver info file)
    --verbose, -v               Verbose
    --quiet, -q                 Quiet
    --oversample <factor>       Oversample prior to filtering
    --ignore-over <value>       Ingore values greater than this
    --ignore-under <value>      Ingore values less than this
    --two-d                     Include LO and IF in output (smoothing etc. won't work with this)
"""


from __future__ import print_function

from collections import namedtuple
import logging
import re
from statistics import mean, median, stdev
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

    ignore_over = None
    if args['--ignore-over']:
        ignore_over = float(args['--ignore-over'])

    ignore_under = None
    if args['--ignore-under']:
        ignore_under = float(args['--ignore-under'])

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

                values_lsb = []
                values_usb = []

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

                        if (ignore_over is not None) and (t_rx > ignore_over):
                            continue

                        if (ignore_under is not None) and (t_rx < ignore_under):
                            continue

                        if match.group(2) == 'L':
                            values_lsb.append(t_rx)

                        elif match.group(2) == 'U':
                            values_usb.append(t_rx)

                data.append(Measurement(
                    lo_freq,
                    if_freq,
                    (None if not values_lsb else mean(values_lsb)),
                    (None if not values_usb else mean(values_usb))))

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

    # Apply clipping after sorting by LO?
    if args['--clip']:
        los = sorted(set(x.lo for x in data))
        filtered = []

        for lo in los:
            lo_values = []
            for entry in data:
                if entry.lo == lo:
                    lo_values.append(entry)

            if lo_values:
                filtered.extend(clipped_measurements(
                    lo_values,
                    tol_n_stdev=float(args['--clip-n-stdev'])))

        data = filtered

    # Select a particular IF?
    if args['--if']:
        if_request = float(args['--if'])
        filtered = []

        for entry in data:
            if not abs(entry.if_ - if_request) < 0.05:
                continue
            filtered.append(entry)

        data = filtered

    # Select by LO?
    if args['--lo-min'] or args['--lo-max']:
        lo_min = float(args['--lo-min'])
        lo_max = float(args['--lo-max'])
        filtered = []

        for entry in data:
            if not (lo_min <= entry.lo <= lo_max):
                continue
            filtered.append(entry)

        data = filtered

    base_suffix = ''

    if args['--ifrelation']:
        key = 'if_'
        if args['--ifrelation-separate']:
            sidebands = ('lsb', 'usb')
        else:
            sidebands = ('mean',)

        base_suffix = '{}_{}'.format(base_suffix, 'if')

        filtered = []

        ifs = sorted(set(x.if_ for x in data))

        for if_ in ifs:
            values_lsb = []
            values_usb = []
            for entry in data:
                if entry.if_ == if_:
                    if entry.lsb is not None:
                        values_lsb.append(entry.lsb)
                    if entry.usb is not None:
                        values_usb.append(entry.usb)
            filtered.append(Measurement(
                None, if_,
                (None if not values_lsb else mean(values_lsb)),
                (None if not values_usb else mean(values_usb))))

        data = subtract_min(filtered)

        if args['--oversample']:
            data = oversample_data(data, int(args['--oversample']), have_lo=False)

    else:
        if args['--two-d']:
            key = ('lo', 'if_')
            data = sorted(data, key=lambda x: (x.lo, x.if_))
            base_suffix = '{}_{}'.format(base_suffix, 'loif')

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

        if args['--oversample']:
            data = oversample_data(data, int(args['--oversample']), have_lsb=have_lsb, have_usb=have_usb)

    for sideband in sidebands:
        suffix = base_suffix
        if sideband == 'mean':
            data_sb = [(getattr(x, key), (x.lsb + x.usb) / 2.0) for x in data]
        else:
            if isinstance(key, tuple):
                data_sb = [(tuple(getattr(x, k) for k in key), getattr(x, sideband)) for x in data]
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

        if pol is not None:
            suffix = '{}_{}'.format(suffix, pol)

        outfile = '{}trx_{}{}.txt'.format(prefix, sideband, suffix)
        logger.info('Writing %s', outfile)
        prev_value = None
        with open(outfile, 'w') as f:
            for (freq, value) in data_sb:
                if value is not None:
                    if isinstance(freq, tuple):
                        if (prev_value is not None) and (prev_value != freq[0]):
                            print('', file=f)
                        prev_value = freq[0]
                        print(' '.join(str(x) for x in freq), '{:.1f}'.format(value), file=f)
                    else:
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
    allow_below = True
    if ref_func == 'min':
        func = min
        comparison = abs
    elif ref_func == 'median':
        func = median
        comparison = lambda x: x
    elif ref_func == 'medianbothsides':
        func = median
        comparison = lambda x: x
        allow_below = False
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
        if (
                (comparison(data[i][1] - ref) < tolerance * ref)
                and (allow_below or
                (ref - comparison(data[i][1]) < tolerance * ref))):
            smoothed.append([data[i][0], data[i][1]])

    return smoothed


def smooth_mean(data, n):
    return smooth_func(data, n, mean)


def smooth_median(data, n):
    return smooth_func(data, n, median)


def subtract_min(data):
    min_lsb = None
    min_usb = None
    for entry in data:
        if (entry.lsb is not None) and ((min_lsb is None) or (entry.lsb < min_lsb)):
            min_lsb = entry.lsb
        if (entry.usb is not None) and ((min_usb is None) or (entry.usb < min_usb)):
            min_usb = entry.usb

    return [x._replace(
        lsb=(None if min_lsb is None else (x.lsb - min_lsb)),
        usb=(None if min_usb is None else (x.usb - min_usb))
    ) for x in data]


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


def oversample_data(data, factor, have_lo=True, have_lsb=True, have_usb=True):
    resampled = []

    prev = None
    for meas in data:
        if prev:
            for x in range(1, factor):
                mf = float(x) / float(factor)
                pf = 1.0 - mf
                resampled.append(Measurement(
                    ((pf * prev.lo + mf * meas.lo) if have_lo else None),
                    (pf * prev.if_ + mf * meas.if_),
                    ((pf * prev.lsb + mf * meas.lsb) if have_lsb else None),
                    ((pf * prev.usb + mf * meas.usb) if have_usb else None),
                ))

        resampled.append(meas)
        prev = meas

    return resampled


def clipped_measurements(values, tol_n_stdev=2):
    if not values:
        return []

    values_lsb = []
    values_usb = []
    for value in values:
        if value.lsb is not None:
            values_lsb.append(value.lsb)
        if value.usb is not None:
            values_usb.append(value.usb)

    median_lsb = median(values_lsb)
    stdev_lsb = stdev(values_lsb)
    min_lsb = median_lsb - tol_n_stdev * stdev_lsb
    max_lsb = median_lsb + tol_n_stdev * stdev_lsb

    median_usb = median(values_usb)
    stdev_usb = stdev(values_usb)
    min_usb = median_usb - tol_n_stdev * stdev_usb
    max_usb = median_usb + tol_n_stdev * stdev_usb

    return [
        x._replace(
            lsb=(x.lsb if (min_lsb < x.lsb < max_lsb) else None),
            usb=(x.usb if (min_usb < x.usb < max_usb) else None),
        )
        for x in values]


if __name__ == '__main__':
    main()
