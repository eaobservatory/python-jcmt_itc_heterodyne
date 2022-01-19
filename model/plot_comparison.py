#!/usr/bin/env python2

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
    plot_comparison.py [-v|-q] --plot <plotfile> [--ymax <ymax>] [--include-fitted | --ratio | --histogram]  --receiver <receiver> [--sideband] [--freq-bin <size>] [--freq-min <freq>] [--freq-max <freq>] <file>...

Options:
    --plot <plotfile>       Filename for generated plot
    --ymax <ymax>           Maximum value on Y-axis [default: 3000.0]
    --include-fitted        Included fitted data points
    --ratio                 Plot as ratio rather than data + model line
    --histogram             Plot ratio as a histogram
    --verbose, -v           Verbose
    --quiet, -q             Quiet
    --sideband              Sideband-specific operation
    --receiver <receiver>   Receiver name
    --freq-bin <size>       Size of frequency bins (GHz) [default: 1.0]
    --freq-min <freq>       Minimum frequency (GHz)
    --freq-max <freq>       Maximum frequency (GHz)
"""

from __future__ import absolute_import, division, print_function

from collections import defaultdict, namedtuple
import logging
import re
import sys

from docopt import docopt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

from jcmt_itc_heterodyne import \
    HeterodyneITC, HeterodyneITCError, HeterodyneReceiver

DataPoint = namedtuple('DataPoint', (
    'sideband', 'freq', 't_rx', 't_sys', 't_rx_model', 't_sys_model', 'eta_sky'))

logger = logging.getLogger(sys.argv[0])


def main():
    args = docopt(__doc__)
    logging.basicConfig(level=(
        logging.DEBUG if args['--verbose'] else (
            logging.WARNING if args['--quiet'] else logging.INFO)))

    receiver = getattr(HeterodyneReceiver, args['--receiver'])

    ymax = float(args['--ymax'])

    sideband_specific = args['--sideband']

    frequency = defaultdict(list)
    freq_bin_size = float(args['--freq-bin'])
    freq_min = (None if args['--freq-min'] is None else float(args['--freq-min']))
    freq_max = (None if args['--freq-max'] is None else float(args['--freq-max']))

    pattern = re.compile('_([LU]SB)\.txt$')

    for filename in args['<file>']:
        if not sideband_specific:
            sideband = None

        else:
            m = pattern.search(filename)

            if not m:
                logger.warning('Did not understand file name %s', file_)
                continue

            (sideband,) = m.groups()

        logger.debug('Reading file %s (sideband %s)', filename, sideband)
        with open(filename, 'r') as f:
            for line in f:
                point = DataPoint(sideband, *[float(x) for x in line.strip().split(' ')])
                freq_bin = int((point.freq / freq_bin_size) + 0.5)
                frequency[freq_bin].append(point)

    itc = HeterodyneITC()

    with PdfPages(args['--plot']) as multipage:
        for freq_bin_key in sorted(frequency.keys()):
            freq_bin = freq_bin_key * freq_bin_size
            if (freq_min is not None) and (freq_bin < freq_min):
                continue
            if (freq_max is not None) and (freq_bin > freq_max):
                continue

            logger.debug('Plotting graph for {} GHz'.format(freq_bin))
            data = frequency[freq_bin_key]
            plt.figure()
            plt.title('{} GHz'.format(freq_bin))

            if not args['--histogram']:
                plt.ylim(0.0, ymax)
                plt.xlim(1.0, 0.0)
                plt.xlabel('Sky efficiency')
            else:
                plt.xlim(0.0, ymax)

            if not args['--ratio'] and not args['--histogram']:
                plt.ylabel('System temperature / K')

                for (sideband, color) in (zip(('LSB', 'USB'), ('g', 'y')) if sideband_specific else ((None, 'g'),)):
                    try:
                        for (freq, line_label, line_style) in (
                                (freq_bin - 0.5 * freq_bin_size, 'lower', 'dotted'),
                                (freq_bin, None, 'solid'),
                                (freq_bin + 0.5 * freq_bin_size, 'upper', 'dashed')):
                            model_eta_sky = []
                            model_t_sys = []

                            for tau_225 in np.arange(0.00, 0.50, 0.005):
                                extra = {}
                                model_t_sys.append(itc._calculate_t_sys(
                                    receiver, freq, tau_225, 60.0,
                                    False, None, sideband=sideband,
                                    extra_output=extra))
                                model_eta_sky.append(extra['eta_sky'])

                            label = 'model'
                            if sideband is not None:
                                label = '{} {}'.format(label, sideband)
                            if line_label is not None:
                                label = '{} {}'.format(label, line_label)

                            plt.plot(model_eta_sky, model_t_sys, color=color, linestyle=line_style, label=label)

                    except HeterodyneITCError:
                        pass

                if not sideband_specific:
                    plt.scatter(
                        [x.eta_sky for x in data], [x.t_sys for x in data],
                        marker='.', alpha=0.25, color='r', label='data')
                else:
                    for (sideband, color) in zip(('LSB', 'USB'), ('r', 'b')):
                        sb_data = [x for x in data if x.sideband == sideband]
                        if sb_data:
                            plt.scatter(
                                [x.eta_sky for x in sb_data], [x.t_sys for x in sb_data],
                                marker='.', alpha=0.25, color=color, label='data {}'.format(sideband))

                if args['--include-fitted']:
                    plt.scatter(
                        [x.eta_sky for x in data], [x.t_sys_model for x in data],
                        marker='.', alpha=0.25, color='k', label='fitted')

            else:
                if not args['--histogram']:
                    plt.ylabel('System temperature ratio (measured / model)')

                    plt.plot([1.0, 0.0], [1.0, 1.0], color='k')

                else:
                    plt.xlabel('System temperature ratio (measured / model)')

                if not sideband_specific:
                    t_sys_ratio = [x.t_sys / x.t_sys_model for x in data]

                    if not args['--histogram']:
                        plt.scatter(
                            [x.eta_sky for x in data], t_sys_ratio,
                            marker='.', alpha=0.25, color='r', label='ratio')
                    else:
                        plt.hist(t_sys_ratio, color='r', label='ratio')

                else:
                    for (sideband, color) in zip(('LSB', 'USB'), ('r', 'b')):
                        sb_data = [x for x in data if x.sideband == sideband]
                        if sb_data:
                            t_sys_ratio = [x.t_sys / x.t_sys_model for x in sb_data]

                            if not args['--histogram']:
                                plt.scatter(
                                    [x.eta_sky for x in sb_data], t_sys_ratio,
                                    marker='.', alpha=0.25, color=color, label='ratio {}'.format(sideband))
                            else:
                                plt.hist(t_sys_ratio, alpha=0.5, color=color, label='ratio {}'.format(sideband))

            plt.legend(loc="upper left")

            multipage.savefig()
            plt.close()


if __name__ == '__main__':
    main()
