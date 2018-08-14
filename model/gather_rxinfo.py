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
    gather_rxinfo.py [-v|-q] --date <date> --outdir <dir>
    gather_rxinfo.py [-v|-q] --date-start <date> --date-end <date> --outdir <dir>

Options:
    --date <date>           Single date
    --date-start <date>     Start date
    --date-end <date>       End date
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

from astropy.io import fits
from docopt import docopt
import numpy as np
from starlink import hds

logger = logging.getLogger(sys.argv[0])
basedir = '/jcmtdata/raw/acsis/spectra'

pattern_obs = re.compile('^\d{5}$')
pattern_file = re.compile('^a\d{8}_\d{5}_(\d{2})_\d{4}\.sdf$')


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

    dir_ = args['--outdir']

    if not os.path.exists(dir_):
        raise Exception('Specified output directory does not exist')

    date = date_start
    while date <= date_end:
        date_str = date.strftime('%Y%m%d')
        logger.info('Reading information for date %s', date_str)

        nr = read_night(date_str)

        if nr is not None:
            with open(os.path.join(
                    dir_, 'rxinfo_{}.json'.format(date_str)), 'w') as f:
                json.dump(nr, f, indent=4, separators=(',', ': '))

        date = date + timedelta(days=1)


def read_night(utdate):
    nitdir = os.path.join(basedir, utdate)

    if not os.path.exists(nitdir):
        return None

    ans = {}

    for obs in os.listdir(nitdir):
        if not pattern_obs.match(obs):
            continue

        obsdir = os.path.join(nitdir, obs)
        info = defaultdict(list)

        try:
            for file_ in os.listdir(obsdir):
                m = pattern_file.match(file_)
                if not m:
                    continue

                subsys = int(m.group(1))

                info[subsys].append(read_file(os.path.join(obsdir, file_)))

        except:
            logger.exception(
                'Failed to read information for %s %s', utdate, obs)
            continue

        if not info:
            continue

        ans[str(int(obs))] = dict(
            (ss, take_average(values))
            for (ss, values) in info.items())

    return ans


def take_average(values):
    ans = values[0]

    if len(values) > 1:
        for param in ['t_sys', 't_rx']:
            ans[param] = np.array(
                [x[param] for x in values]).mean(axis=0).tolist()

    return ans


def read_file(filename):
    logger.debug('Reading information from file %s', filename)

    loc = hds.open(filename, 'read')

    acsis = loc.find('MORE').find('ACSIS')
    t_sys = acsis.find('TSYS').get()
    t_rx = acsis.find('TRX').get()
    recep = acsis.find('RECEPTORS').get()

    loc.annul()

    return {
        't_sys': np.average(t_sys, axis=0).tolist(),
        't_rx': np.average(t_rx, axis=0).tolist(),
        'recep': recep.tolist(),
    }


if __name__ == '__main__':
    main()
