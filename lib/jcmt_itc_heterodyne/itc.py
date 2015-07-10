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

from collections import namedtuple
from math import atan, cos, exp, radians, sqrt

from .receiver import HeterodyneReceiver


time_between_refs = 30.0
harp_array_size = 120.0
harp_f_angle = cos(atan(0.25))


DurationParam = namedtuple(
    'DurationParam',
    ('a', 'b', 'c', 'd', 'e'))


class HeterodyneITC(object):
    GRID = 1
    JIGGLE = 2
    RASTER = 3

    PSSW = 1
    BMSW = 2
    FRSW = 3

    valid_modes = set((
        (GRID, PSSW),
        (GRID, BMSW),
        (JIGGLE, PSSW),
        (JIGGLE, BMSW),
        (RASTER, PSSW),
    ))

    def __init__(self):
        """
        Construct ITC object.
        """

        pass

    def _calculate_t_sys(
            self, receiver, freq, tau_225, zenith_angle_deg,
            is_dsb):
        """
        Calculate the system temperature.
        """

        t_im = 0.0

        t_rx = HeterodyneReceiver.get_interpolated_t_rx(
            receiver=receiver, freq=freq)

        tau = HeterodyneReceiver.get_interpolated_opacity(
            tau_225=tau_225, freq=freq)

        # To duplicate behavior of HITEC, round the tau value.
        # It is unclear why HITEC does this!
        # TODO: remove this?
        if tau < 0.1:
            rounded_tau = round(tau, 3)
        else:
            rounded_tau = round(tau, 2)

        nu_sky = exp(- rounded_tau / cos(radians(zenith_angle_deg)))

        t_sky = 260.0 * (1 - nu_sky)

        nu_tel = HeterodyneReceiver.get_receiver_info(receiver).nu_tel

        t_tel = 265.0 * (1 - nu_tel)

        if not is_dsb:
            # Single sideband mode.

            if receiver == HeterodyneReceiver.HARP:
                # HITEC documentation said: 20110310: bypass ATM model for HARP
                # and use empirical fit to data based on a 345.796 GHz T_sys
                # for the tau and elevation in question.  Previous calculation
                # was:
                # t_sys = (
                #     (t_rx + nu_tel * t_sky + t_tel + t_im) /
                #     (nu_sky * nu_tel))

                # For 345.796 GHz reference:
                ref_freq = 345.796
                ref_t_rx = 90
                ref_t_atm = 260
                ref_t_amb = 265
                ref_f_850 = 3.3
                ref_nu_tel = 0.9

                ref_nu_sky = exp(- ref_f_850 * tau_225 /
                                 cos(radians(zenith_angle_deg)))

                ref_t_sky = ref_t_atm * (1 - ref_nu_sky)
                ref_t_tel = ref_t_amb * (1 - ref_nu_tel)

                t_sys_345 = (
                    (ref_t_rx + ref_nu_tel * ref_t_sky + ref_t_tel) /
                    (ref_nu_sky * ref_nu_tel))

                c2 = 3.75 - 3.66 * exp(-tau_225 /
                                       cos(radians(zenith_angle_deg)))
                c1 = -2.0
                c0 = t_sys_345 + 15

                x = freq - 345.796

                if freq < 329.5:
                    c0 *= 1.5
                elif freq < 333:
                    c0 *= 1.1
                elif freq > 372:
                    c0 *= 2.5
                elif freq > 366.25:
                    c0 *= 1.7

                return c2 * x * x + c1 * x + c0

            else:
                return (
                    (t_rx + nu_tel * t_sky + t_tel + t_im) /
                    (nu_sky * nu_tel))

        else:
            # Dual sideband mode.

            if receiver == HeterodyneReceiver.WD:
                # HITEC documentation said: RxWD has SSB T_Rx=600K.
                # Do nothing now, but may have to use the right DSB T_Rx
                # which could be half of the SSB T_Rx.  (t_rx = t_rx / 2.0)

                return (
                    2.0 * (t_rx + nu_tel * t_sky + t_tel) / (nu_sky * nu_tel))

            else:
                return (
                    2.0 * (t_rx + nu_tel * t_sky + t_tel) / (nu_sky * nu_tel))

    def _calculate_rms(
            self, time,
            instrument, map_mode, sw_mode,
            n_points, separate_offs,
            dual_polarization, t_sys, freq_res, dy):
        """
        Calculate the RMS from a given integration time accounting for
        shared or separate offs.

        For rasters the number of points should be set to the number of
        samples in a row.
        """

        # "Unexplained fudge factor", as it is called in "HITEC".
        het_fudge = 1.04

        # "Correlation factor".
        het_dfact = 1.23

        # Set np_shared to 1 if separate offs requested.
        if separate_offs:
            np_shared = 1
        else:
            np_shared = n_points

        # GRID PSSW forces shared if possible.
        if map_mode == self.GRID and sw_mode == self.PSSW:
            np_shared = int(time_between_refs / time)

            if np_shared < 1:
                np_shared = 1

            if np_shared > n_points:
                np_shared = n_points

        # Array overlap factor.
        multiscan = 1.0
        # For arrays, if the dy is less than the footprint, take the
        # overlap into account when rasterizing.
        if map_mode == self.RASTER and instrument == HeterodyneReceiver.HARP:
            multiscan = 1.0 / sqrt(harp_array_size * harp_f_angle / dy)

        rms = (
            multiscan * het_fudge * het_dfact *
            sqrt(1 + 1 / sqrt(np_shared)) * t_sys /
            sqrt(freq_res * 1.0e6 * time))

        # Apply correction for dual polarization.
        if instrument == HeterodyneReceiver.WD and dual_polarization:
            rms /= sqrt(2.0)

        return rms

    def _calculate_time(
            self, rms,
            instrument, map_mode, sw_mode,
            n_points, separate_offs,
            *args, **kwargs):
        """
        Calculate the integration time from a given RMS accounting for
        shared or separate offs.

        For rasters the number of points should be set to the number of
        samples in a row.
        """

        # Calculate RMS for a 1-second observation.
        time = 1

        # Set np_shared to 1 if separate offs requested.
        if separate_offs:
            np_shared = 1
        else:
            np_shared = n_points

        # GRID PSSW forces shared if possible.
        if map_mode == self.GRID and sw_mode == self.PSSW:
            np_shared = int(time_between_refs / time)

            if np_shared < 1:
                np_shared = 1

            if np_shared > n_points:
                np_shared = n_points

        # Iterate in the case of GRID PSSW because np_shared depends on time.
        for step in range(0, 5):
            i_rms = self._calculate_rms(
                time, instrument, map_mode, sw_mode,
                n_points, separate_offs, *args, **kwargs)

            time = int(10 * time * (i_rms / rms) ** 2 + 0.5) / 10

            if map_mode == self.GRID and sw_mode == self.PSSW:
                np_shared_used = np_shared

                np_shared = int(time_between_refs / time)

                if np_shared < 1:
                    np_shared = 1

                if np_shared > n_points:
                    np_shared = n_points

                if np_shared == np_shared_used:
                    break

            else:
                break

        return time

    def _get_duration_param(
            self,
            map_mode, sw_mode,
            n_points, separate_offs,
            continuum_mode):
        """
        Get the parameters for an elapsed time calculation.

        The parameters are for the generalized duration expresssion:

            e * [ a + (b*np*inttime + c*sqrt(np)*inttime + d) * rows ]

        Parameters a, b, c, d and e are dependent on the observation mode
        and are based on emperical fits.

        Typically c != 0 only for shared offs (including rasters) and
        d is used for rasters only.

        e is an overall factor for continuum mode (presently not well
        measured).
        """

        shared = not (n_points == 1 or separate_offs)

        # c and d are often 0.
        c = 0
        d = 0

        if continuum_mode:
            e = 1.2
        else:
            e = 1

        if map_mode == self.JIGGLE and sw_mode == self.BMSW:
            a = 100

            if shared:
                b = 1.27
                c = 1.27
            else:
                b = 2.3

        elif map_mode == self.GRID and sw_mode == self.BMSW:
            # HITEC comments said: don't really know, but assume non-shared
            # and slightly in between JIGGLE BMSW and JIGGLE PSSW.
            a = 100
            b = 2.37

        elif ((map_mode == self.JIGGLE and sw_mode == self.PSSW) or
                (map_mode == self.GRID and sw_mode == self.PSSW
                    and n_points == 1)):
            a = 80

            if shared:
                b = 1.75
            else:
                b = 2.45

        elif map_mode == self.GRID and sw_mode == self.PSSW and n_points != 1:
            # HITEC comments said: force shared curve for the calculation
            # since non-shared is not allowed.
            # (Non-shared version was a=190, b=2.0.)
            a = 80
            b = 2.65

        elif map_mode == self.RASTER and sw_mode == self.PSSW:
            # HITEC comments said: have not measured -- this assumed similar
            # to JIGGLE PSSW for a single row
            a = 80
            b = 1.05
            c = 1.05
            d = 18

        else:
            raise Exception('Duration parameters unknown for '
                            'map mode {0} and switching mode {1}'.format(
                                map_mode, sw_mode))

        return DurationParam(a=a, b=b, c=c, d=d, e=e)

    def _calculate_elapsed_time(
            self, time, rows,
            map_mode, sw_mode,
            n_points, separate_offs,
            continuum_mode):
        """
        Calculate the elapsed time of an observation.

        rows should be 1 for non-raster observations.
        """

        param = self._get_duration_param(
            map_mode=map_mode, sw_mode=sw_mode,
            n_points=n_points, separate_offs=separate_offs,
            continuum_mode=continuum_mode)

        return param.e * (
            param.a + rows * (
                param.b * n_points * time +
                param.c * sqrt(n_points) * time +
                param.d)
        )

    def _calculate_integration_time(
            self, elapsed, rows,
            map_mode, sw_mode,
            n_points, separate_offs,
            continuum_mode):
        """
        Calculate the integration time of an observation based on the
        elapsed time.

        rows should be 1 for non-raster observations.
        """

        param = self._get_duration_param(
            map_mode=map_mode, sw_mode=sw_mode,
            n_points=n_points, separate_offs=separate_offs,
            continuum_mode=continuum_mode)

        time = (
            (elapsed / param.e - param.a - rows * param.d) /
            (rows * (param.b * n_points + param.c * sqrt(n_points))))

        return int(10 * time + 0.5) / 10
