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

from __future__ import absolute_import, division, print_function, \
    unicode_literals

import numpy as np
import matplotlib.pyplot as plt
import sys

from jcmt_itc_heterodyne import HeterodyneReceiver


def main():
    if (len(sys.argv) != 2):
        print('Usage: plot_sideband_trx RECEIVER', file=sys.stderr)
        sys.exit(1)

    receiver_name = sys.argv[1].upper()

    if not hasattr(HeterodyneReceiver, receiver_name):
        print(
            'Receiver name "{}" not recognized'.format(receiver_name),
            file=sys.stderr)
        sys.exit(1)

    plot_sideband_trx(receiver=getattr(HeterodyneReceiver, receiver_name))


def plot_sideband_trx(receiver):
    info = HeterodyneReceiver.get_receiver_info(receiver)

    freqs = np.arange(info.f_min, info.f_max, 0.01)

    plt.scatter(freqs, [
        HeterodyneReceiver.get_interpolated_t_rx(receiver, freq)
        for freq in freqs], color='green')

    t_rx = info.t_rx
    freq_if = info.f_if

    if info.t_rx_lo:
        plt.plot(
            [x[0] - freq_if for x in t_rx],
            [x[1] for x in t_rx], color='red')

        plt.plot(
            [x[0] + freq_if for x in t_rx],
            [x[1] for x in t_rx], color='blue')

    else:
        plt.plot(*zip(*t_rx), color='black')

    plt.show()


if __name__ == '__main__':
    main()
