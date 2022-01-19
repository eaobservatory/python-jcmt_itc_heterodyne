#!/usr/bin/env python2

# Copyright (C) 2018 East Asian Observatory
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
    combine_rxinfo.py [-v|-q] --instrument <inst> --date <date> --dir <dir> --outdir <dir> [--median | --mean | --merged]
    combine_rxinfo.py [-v|-q] --instrument <inst> --date-start <date> --date-end <date> [--date-exclude <date>...] --dir <dir> --outdir <dir> [--median | --mean | --merged]

Options:
    --instrument <inst>     Instrument name
    --date <date>           Single date
    --date-start <date>     Start date
    --date-end <date>       End date
    --date-exclude <date>...  Dates to exclude
    --dir <dir>             Input directory
    --outdir <dir>          Output directory
    --verbose, -v           Verbose
    --quiet, -q             Quiet
    --median                Generate median rather than per-receptor data
    --mean                  Generate mean rather than per-receptor data
    --merged                Store per-receptor data in one file
"""

from __future__ import absolute_import, division, print_function

from collections import defaultdict, namedtuple
from datetime import datetime, timedelta
import json
import os.path
import logging
import re
import sys

import numpy as np
from docopt import docopt

from omp.db.part.arc import ArcDB

logger = logging.getLogger(sys.argv[0])

ReceiverParam = namedtuple('ReceiverParam', ('receptors', 'filter_t_sys'))

rx_params = {
    'ALAIHI': ReceiverParam(['NA0', 'NA1'], True),
    'UU': ReceiverParam(['NU0L', 'NU1L', 'NU0U', 'NU1U'], True),
    'AWEOWEO': ReceiverParam(['NW0L', 'NW1L', 'NW0U', 'NW1U'], True),
}


def main():
    args = docopt(__doc__)
    logging.basicConfig(level=(
        logging.DEBUG if args['--verbose'] else (
            logging.WARNING if args['--quiet'] else logging.INFO)))

    if args['--date']:
        date_start = date_end = datetime.strptime(args['--date'], '%Y%m%d')
    else:
        date_start = datetime.strptime(args['--date-start'], '%Y%m%d')
        date_end = datetime.strptime(args['--date-end'], '%Y%m%d')

        date_exclude = [
            [datetime.strptime(x, '%Y%m%d') for x in y.split('-')]
            for y in args['--date-exclude']]

    dir_ = args['--dir']
    outdir = args['--outdir']
    use_median = args['--median']
    use_mean = args['--mean']
    store_merged = args['--merged']

    if not os.path.exists(outdir):
        raise Exception('Specified output directory does not exist')

    instrument = args['--instrument']

    rxinfo = load_rxinfo(date_start, date_end, dir_)

    obsinfo = query_db(date_start, date_end, instrument)

    output = combine_rx_db(
        instrument, rxinfo, obsinfo, date_exclude=date_exclude,
        use_median=use_median, use_mean=use_mean,
        store_merged=store_merged)

    for (key, data) in output.items():
        with open(os.path.join(outdir, 'merged_{}_{}.txt'.format(*key)), 'w') as f:
            for line in data:
                print(*line, file=f)


def combine_rx_db(
        instrument, rxinfo, obsinfo, date_exclude,
        use_median, use_mean, store_merged):
    output = defaultdict(list)

    rx_param = rx_params.get(instrument.upper(), ReceiverParam(None, False))

    for obs in obsinfo:
        if date_exclude:
            date = datetime.strptime(str(obs['utdate']), '%Y%m%d')
            excluded = True
            for exclusion in date_exclude:
                if (date >= exclusion[0]) and (date <= exclusion[1]):
                    break
            else:
                excluded = False

            if excluded:
                continue

        rxdate = rxinfo.get(str(obs['utdate']))
        if rxdate is None:
            logger.warning('Nothing found for date %i', obs['utdate'])
            continue

        rxobs = rxdate.get(str(obs['obsnum']))
        if rxobs is None:
            logger.warning(
                'Nothing found for date %i obs %i',
                obs['utdate'], obs['obsnum'])
            continue

        rxss = rxobs.get(str(obs['subsysnr']))
        if rxss is None:
            logger.warning(
                'Nothing found for date %i obs %i ss %i',
                obs['utdate'], obs['obsnum'], obs['subsysnr'])
            continue

        if use_median or use_mean:
            if use_median:
                recep = 'median'
                t_rx = np.median(rxss['t_rx']).item()
                t_sys = np.median(rxss['t_sys']).item()

            elif use_mean:
                recep = 'mean'
                t_rx = mean_valid(rxss['t_rx'])
                t_sys = mean_valid(rxss['t_sys'])

            else:
                raise Exception('Aggregate method not defined')

            out_key = (recep, obs['obs_sb'])
            out_data = [obs[x] for x in ['utdate', 'obsnum', 'subsysnr', 'lofreq', 'iffreq', 'rffreq']]
            out_data.extend([t_rx, t_sys])
            out_data.extend(obs[x] for x in ['wvmtau', 'elevation', 'sw_mode'])

            output[out_key].append(out_data)

        elif store_merged:
            out_key = (instrument.lower(), 'merged')
            receptors = rx_param.receptors
            if receptors is None:
                raise Exception('Receptors unknown for this instrument')
            out_recep = {}
            for (recep, t_rx, t_sys) in zip(rxss['recep'], rxss['t_rx'], rxss['t_sys']):
                if 0.0 < (t_sys if rx_param.filter_t_sys else t_rx) < 1000.0:
                    out_recep[recep] = t_sys
            out_data = [obs[x] for x in ['utdate', 'obsnum', 'subsysnr', 'lofreq', 'iffreq', 'rffreq']]
            out_data.extend([out_recep.get(x) for x in receptors])
            out_data.extend(obs[x] for x in ['wvmtau', 'elevation', 'sw_mode'])

            output[out_key].append(out_data)

        else:
            for (recep, t_rx, t_sys) in zip(rxss['recep'], rxss['t_rx'], rxss['t_sys']):
                if 0.0 < (t_sys if rx_param.filter_t_sys else t_rx) < 1000.0:
                    out_key = (recep, obs['obs_sb'])
                    out_data = [obs[x] for x in ['utdate', 'obsnum', 'subsysnr', 'lofreq', 'iffreq', 'rffreq']]
                    out_data.extend([t_rx, t_sys])
                    out_data.extend(obs[x] for x in ['wvmtau', 'elevation', 'sw_mode'])

                    output[out_key].append(out_data)

    return output


def load_rxinfo(date_start, date_end, dir_):
    if not os.path.exists(dir_):
        raise Exception('Specified input directory does not exist')

    ans = {}

    date = date_start
    while date <= date_end:
        date_str = date.strftime('%Y%m%d')

        file_ = os.path.join(dir_, 'rxinfo_{}.json'.format(date_str))

        if os.path.exists(file_):
            logger.info('Loading information for date %s', date_str)

            with open(file_, 'r') as f:
                ans[date_str] = json.load(f)

        date = date + timedelta(days=1)

    return ans


def query_db(date_start, date_end, instrument):
    omp = ArcDB()

    ans = []

    logger.info(
        'Querying database for %s - %s (%s)',
        date_start.strftime('%Y-%m-%d'),
        date_end.strftime('%Y-%m-%d'),
        instrument)

    with omp.db.transaction() as c:
        c.execute(
            'SELECT utdate, obsnum, subsysnr, obs_sb, iffreq'
            ', (lofreqs + lofreqe) / 2 AS lofreq'
            ', (freq_sig_lower + freq_sig_upper) / 2 AS rffreq'
            ', (wvmtaust + wvmtauen) / 2 AS wvmtau'
            ', (elstart + elend) / 2 AS elevation'
            ', sw_mode'
            ' FROM jcmt.COMMON JOIN jcmt.ACSIS ON COMMON.obsid = ACSIS.obsid'
            ' WHERE (utdate BETWEEN %s AND %s)'
            ' AND INSTRUME = %s'
            ' ORDER BY utdate ASC, obsnum ASC, subsysnr ASC',
            [
                int(date_start.strftime('%Y%m%d')),
                int(date_end.strftime('%Y%m%d')),
                instrument,
            ])

        cols = c.column_names

        while True:
            row = c.fetchone()
            if row is None:
                break

            ans.append(dict(zip(cols, row)))

    return ans


def mean_valid(values):
    valid = [x for x in values if -1000000.0 < x < 1000000.0]

    if not valid:
        return None

    return np.mean(valid).item()


if __name__ == '__main__':
    main()
