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
    combine_rxinfo.py [-v|-q] --instrument <inst> --date <date> --dir <dir> --outdir <dir>
    combine_rxinfo.py [-v|-q] --instrument <inst> --date-start <date> --date-end <date> --dir <dir> --outdir <dir>

Options:
    --instrument <inst>     Instrument name
    --date <date>           Single date
    --date-start <date>     Start date
    --date-end <date>       End date
    --dir <dir>             Input directory
    --outdir <dir>          Output directory
    --verbose, -v           Verbose
    --quiet, -q             Quiet
"""

from __future__ import absolute_import, division, print_function

from collections import defaultdict
from datetime import datetime, timedelta
import json
import os.path
import logging
import re
import sys

from docopt import docopt

from omp.db.part.arc import ArcDB

logger = logging.getLogger(sys.argv[0])


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

    dir_ = args['--dir']
    outdir = args['--outdir']

    if not os.path.exists(outdir):
        raise Exception('Specified output directory does not exist')

    rxinfo = load_rxinfo(date_start, date_end, dir_)

    obsinfo = query_db(date_start, date_end, args['--instrument'])

    output = combine_rx_db(rxinfo, obsinfo)

    for (key, data) in output.items():
        with open(os.path.join(outdir, 'merged_{}_{}.txt'.format(*key)), 'w') as f:
            for line in data:
                print(*line, file=f)


def combine_rx_db(rxinfo, obsinfo):
    output = defaultdict(list)

    for obs in obsinfo:
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

        for (recep, t_rx, t_sys) in zip(rxss['recep'], rxss['t_rx'], rxss['t_sys']):
            if 0.0 < t_rx < 1000.0:
                out_key = (recep, obs['obs_sb'])
                out_data = [obs[x] for x in ['utdate', 'obsnum', 'subsysnr', 'lofreq', 'iffreq', 'rffreq']]
                out_data.extend([t_rx, t_sys])
                out_data.extend(obs[x] for x in ['wvmtau', 'elevation'])

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


if __name__ == '__main__':
    main()
