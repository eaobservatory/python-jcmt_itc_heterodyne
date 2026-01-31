# Copyright (C) 2026 East Asian Observatory
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

from math import exp

h = 6.62607015E-34
k = 1.380649E-23


def t_sys_correction_factor(
        eta_tel, frequency_hz, tau_freq, am,
        t_load_k, t_spill_k, t_air_k):
    """
    Calculate system temperature chopper wheel correction factor.

    This method aims to replicate the correction factor calculation
    applied by ACSIS to its system temperature calculation (for
    applicable instruments).
    """

    t_atm_k = t_air_k - 10

    j_load = brightness_temperature(frequency_hz, t_load_k)
    j_spill = brightness_temperature(frequency_hz, t_spill_k)
    j_atm = brightness_temperature(frequency_hz, t_atm_k)

    c = 1.0
    c += ((1 - eta_tel) / eta_tel) * ((j_load - j_spill) / j_load) * exp(tau_freq * am)
    c += ((j_load - j_atm) / j_load) * (exp(tau_freq * am) - 1)

    return c


def brightness_temperature(frequency_hz, physical):
    temp = h * frequency_hz / k

    return temp / (exp(temp / physical) - 1)
