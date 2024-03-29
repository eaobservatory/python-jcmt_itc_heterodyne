#!/usr/bin/env python2

# Copyright (C) 2019 East Asian Observatory
# All Rights Reserved.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful,but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,51 Franklin
# Street, Fifth Floor, Boston, MA  02110-1301, USA

"""
Usage:
    make_comparison.py [-v|-q] --dir <dir> --outdir <dir> --receiver <receiver> [--sideband] [--if] [--modeldate <date>]

Options:
    --dir <dir>             Input directory
    --outdir <dir>          Output directory
    --verbose, -v           Verbose
    --quiet, -q             Quiet
    --sideband              Sideband-specific operation
    --if                    IF-specific operation
    --receiver <receiver>   Receiver name
    --modeldate <date>      Specific date model
"""

from __future__ import absolute_import, division, print_function

import os
import logging
import sys
import re

from docopt import docopt

from jcmt_itc_heterodyne import HeterodyneITC, HeterodyneITCError, HeterodyneReceiver

logger = logging.getLogger(sys.argv[0])


def main():
    args = docopt(__doc__)
    logging.basicConfig(level=(
        logging.DEBUG if args['--verbose'] else (
            logging.WARNING if args['--quiet'] else logging.INFO)))

    dir_ = args['--dir']
    outdir = args['--outdir']
    receiver = args['--receiver']
    sideband_specific = args['--sideband']
    if_specific = args['--if']

    if not os.path.exists(dir_):
        raise Exception('Specified input directory does not exist')

    if not os.path.exists(outdir):
        raise Exception('Specified output directory does not exist')

    # To read a specific info file:
    model_date = args['--modeldate']
    if model_date is not None:
        HeterodyneReceiver._read_receiver_info(
            'lib/jcmt_itc_heterodyne/data/receiver_info_{}.json'.format(model_date))

    info = load_combined(dir_)

    results = apply_itc(
        info, receiver=receiver, sideband_specific=sideband_specific,
        if_specific=if_specific)

    for (key, input_) in info.items():
        output = results[key]
        assert len(input_) == len(output)

        with open(os.path.join(outdir, 'comparison_{}_{}.txt'.format(*key)), 'w') as f:
            for input_entry, output_entry in zip(input_, output):
                if output_entry is None:
                    continue
                entry = [input_entry[x] for x in ['rffreq', 't_rx', 't_sys']]
                entry.extend(output_entry[x] for x in ['t_rx', 't_sys', 'eta_sky'])
                entry.append(input_entry['lofreq'])
                print(*entry, file=f)


def load_combined(dir_):
    pattern = re.compile('^merged_(H\d+|median|mean)_([LU]SB)\.txt$')

    ans = {}

    for file_ in os.listdir(dir_):
        m = pattern.search(file_)
        if not m:
            logger.warning('Did not understand file name %s', file_)
            continue

        (receptor, sideband) = m.groups()
        logger.info('Processing file %s: (%s, %s)', file_, receptor, sideband)

        key = (receptor, sideband)
        ans[key] = data = []

        with open(os.path.join(dir_, file_), 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if 'None' in line:
                    continue

                columns = line.split(' ')

                entry = dict(zip(
                    ['utdate', 'obsnum', 'subsysnr'],
                    [int(x) for x in columns[0:3]]))
                entry.update(zip(
                    ['lofreq', 'iffreq', 'rffreq', 't_rx', 't_sys', 'wvmtau', 'elevation'],
                    [float(x) for x in columns[3:10]]))

                data.append(entry)

    return ans


def apply_itc(info, receiver, sideband_specific, if_specific):
    ans = {}

    itc = HeterodyneITC()
    receiver = getattr(HeterodyneReceiver, receiver)

    for (key, data) in info.items():
        (receptor, sideband) = key
        ans[key] = result = []

        for entry in data:
            try:
                output = {}

                t_sys = itc._calculate_t_sys(
                    receiver, entry['rffreq'], entry['wvmtau'], 90 - entry['elevation'], False,
                    if_freq=(entry['iffreq'] if if_specific else None),
                    sideband=(sideband if sideband_specific else None),
                    extra_output=output)

                output['t_sys'] = t_sys

                result.append(output)

            except HeterodyneITCError:
                logger.exception('Error calculating t_sys')

                result.append(None)

    return ans


if __name__ == '__main__':
    main()
