# Copyright (C) 2007-2009 Science and Technology Facilities Council.
# Copyright (C) 2015 East Asian Observatory
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#
# This Python ITC is based on the original Perl "HITEC" software.

from __future__ import absolute_import, division, print_function, \
    unicode_literals

from codecs import latin_1_decode
from collections import namedtuple, OrderedDict
import json
from math import cos, radians
from pkgutil import get_data


ReceiverInfo = namedtuple(
    'ReceiverInfo',
    ('name', 'f_min', 'f_max', 'n_mix', 'ssb_available', 'dsb_available',
     'pixel_size', 'array', 'eta_tel', 't_rx'))

ArrayInfo = namedtuple(
    'ArrayInfo',
    ('size', 'f_angle', 'footprint', 'scan_spacings', 'jiggle_patterns'))


class HeterodyneReceiver(object):
    A3 = 1
    HARP = 2
    WD = 3

    # Data structure holding information for each receiver.  To be filled
    # the first time the data are needed.
    _info = OrderedDict()

    # Dictionary to contain the tau data at each 225 GHz opacity.  All entries
    # are initially None -- to be replaced with data read from the files as
    # needed.
    _tau_data = OrderedDict(((x, None) for x in
                             (0.03, 0.05, 0.065, 0.1, 0.16, 0.2, 0.25)))

    @classmethod
    def get_all_receivers(cls):
        if not cls._info:
            cls._read_receiver_info()

        return cls._info.copy()

    @classmethod
    def get_receiver_info(cls, receiver):
        if not cls._info:
            cls._read_receiver_info()

        return cls._info[receiver]

    @classmethod
    def get_receiver_names(cls):
        if not cls._info:
            cls._read_receiver_info()

        return OrderedDict((
            (receiver, info.name) for (receiver, info) in cls._info.items()
        ))

    @classmethod
    def get_interpolated_t_rx(cls, receiver, freq):
        """
        Get an interpolated receiver temperature value.

        Outside the range of data values given in the "receiver_info.json"
        file, the first or last values are given as appropriate.
        """

        freq_prev = None
        t_rx_prev = None

        for (freq_i, t_rx_i) in cls.get_receiver_info(receiver).t_rx:
            if freq <= freq_i:
                if freq_prev is None:
                    # This is the first value, so return it immediately.
                    return t_rx_i

                else:
                    # Perform interpolation.
                    return (
                        t_rx_prev +
                        (t_rx_i - t_rx_prev) * (freq - freq_prev) /
                        (freq_i - freq_prev))

            freq_prev = freq_i
            t_rx_prev = t_rx_i

        else:
            # Frequency is beyond the last value: return the last t_rx
            # value.
            return t_rx_prev

    @classmethod
    def get_interpolated_opacity(cls, tau_225, freq):
        """
        Get an interpolated opacity value for a given frequency at a given
        225 GHz opacity.

        This interpolates the values in the opacity data files to get
        opacities at the specified frequency, and then interpolates
        between the data files (or extrapolates beyond their range
        of 225 GHz opacity) to get a value for the specified 225 GHz
        opacity.
        """

        # Determine which pair of tau files span the given tau_225 value.  If
        # it is at the end of the range, use the first two or last two as
        # appropriate for extrapolation.
        tau_files = list(cls._tau_data.keys())

        for i in range(0, len(tau_files)):
            if tau_files[i] >= tau_225:
                if i == 0:
                    tau_values = (tau_files[0], tau_files[1])
                else:
                    tau_values = (tau_files[i - 1], tau_files[i])
                break
        else:
            tau_values = (tau_files[-2], tau_files[-1])

        # Now interpolate at each of these 225 GHz tau values to estimate
        # the tau at the given frequency.
        tau_freqs = []

        for tau_value in tau_values:
            prev_freq = None
            prev_tau = None

            for (freq_i, tau_freq) in cls.get_opacity_data(tau_value):
                if freq_i >= freq:
                    if prev_freq is None:
                        # Retain the first value.
                        tau_freqs.append(tau_freq)
                    else:
                        # Perform linear interpolation.
                        tau_freqs.append(
                            prev_tau +
                            ((tau_freq - prev_tau) * (freq - prev_freq) /
                                (freq_i - prev_freq)))
                    break

                prev_freq = freq_i
                prev_tau = tau_freq

            else:
                # Retain the last value.
                tau_freqs.append(tau_freq)

        # Finally interpolate (or extrapolate) between the values from the two
        # files.
        return (
            tau_freqs[0] +
            (tau_225 - tau_values[0]) * (tau_freqs[1] - tau_freqs[0]) /
            (tau_values[1] - tau_values[0]))

    @classmethod
    def get_opacity_data(cls, tau_225):
        """
        Get a list of (frequency, tau) pairs for a given 225 GHz opacity (tau)
        value.  This value must correspond to one of the tau data files
        contained within this package.
        """

        if cls._tau_data[tau_225] is None:
            cls._read_tau_file(tau_225)

        return cls._tau_data[tau_225]

    @classmethod
    def _read_receiver_info(cls):
        """
        Read receiver information from the "receiver_info.json" file
        and store it in the class's "_info" attribute.

        Should not be called if "_info" has already been set up.
        """

        # List specifying how to map the receiver names to the "enum" values
        # used by this class.  (And the ordering in which to display them.)
        receiver_names = [
            (cls.A3, 'RxA3'),
            (cls.HARP, 'HARP'),
            (cls.WD, 'RxWD'),
        ]

        receiver_data = json.loads(latin_1_decode(
            get_data('jcmt_itc_heterodyne', 'data/receiver_info.json'))[0])

        for (receiver, name) in receiver_names:
            receiver_info = receiver_data.get(name)
            if receiver_info is None:
                raise Exception('Could not find receiver information '
                                'for "{0}".'.format(name))

            info_obj = ReceiverInfo(name=name, **receiver_info)

            if info_obj.array is not None:
                array_obj = ArrayInfo(footprint=None, **info_obj.array)

                array_obj = array_obj._replace(
                    scan_spacings=OrderedDict(array_obj.scan_spacings),
                    jiggle_patterns=OrderedDict(array_obj.jiggle_patterns),
                    footprint=(array_obj.size *
                               cos(radians(array_obj.f_angle))))

                info_obj = info_obj._replace(array=array_obj)

            cls._info[receiver] = info_obj

    @classmethod
    def _read_tau_file(cls, tau):
        """
        Read a tau data file and store its values in the class's
        "_tau_data" dictionary.
        """

        if tau not in cls._tau_data:
            raise Exception('Do not expect tau data file at {0}.'.format(tau))

        tau_values = []

        for line in get_data(
                'jcmt_itc_heterodyne',
                'data/tau' + '{:.03f}.dat'.format(tau)[2:]
                ).splitlines():
            (freq, tau_freq) = line.split()

            tau_values.append((float(freq), float(tau_freq)))

        cls._tau_data[tau] = tau_values
