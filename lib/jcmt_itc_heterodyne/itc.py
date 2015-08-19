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

from collections import namedtuple, OrderedDict
from math import acos, atan, cos, degrees, exp, radians, sqrt

from .receiver import HeterodyneReceiver
from .version import version


default_time_between_refs = 30.0
speed_of_light = 299792458


DurationParam = namedtuple(
    'DurationParam',
    ('a', 'b', 'c', 'd', 'e'))


class HeterodyneITCError(Exception):
    pass


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

    jiggle_patterns = OrderedDict((
        ('3 x 3', 9),
        ('5 x 5', 25),
        ('7 x 7', 49),
        ('9 x 9', 81),
        ('11 x 11', 121),
    ))

    RMS_TO_TIME = 1
    INT_TIME_TO_RMS = 2
    ELAPSED_TO_RMS = 3

    def __init__(self, time_between_refs=None):
        """
        Construct ITC object.
        """

        if time_between_refs is None:
            self.time_between_refs = default_time_between_refs
        else:
            self.time_between_refs = time_between_refs

    def get_version(self):
        """
        Get the module version.
        """

        return version

    def get_valid_modes(self):
        """
        Get set of valid observing modes.

        Returns a set of (map_mode, sw_mode) tuples.
        """

        return self.valid_modes.copy()

    def get_jiggle_patterns(self):
        """
        Get ordered dictionary of jiggle patterns for non-array
        receivers.
        """

        return self.jiggle_patterns.copy()

    def velocity_to_freq_res(self, freq, velocity):
        """
        Convert a velocity (in km/s) to a frequency resolution
        (in MHz) for a given frequency (in GHz).
        """

        # Scale: 10^3 (km/s) * 10^9 (GHz) / 10^6 (MHz) = 10^6
        return 1.0e6 * velocity * freq / speed_of_light

    def freq_res_to_velocity(self, freq, freq_res):
        """
        Convert a frequency resolution (in MHz) to a velocity
        resolution (in km/s) at a given frequency (in GHz).
        """

        # Scale: 10^6 (MHz) / 10^9 (GHz) / 10^3 (km/s) = 10^-6
        return 1.0e-6 * speed_of_light * freq_res / freq

    def estimate_zenith_angle_deg(self, declination_deg):
        """
        Estimate zenith angle for a source at a given declination.
        """

        return degrees(acos(0.9 * cos(radians(declination_deg - 19.823))))

    def calculate_time(
            self, rms,
            receiver, map_mode, sw_mode,
            freq, freq_res,
            tau_225, zenith_angle_deg, is_dsb, dual_polarization,
            n_points,
            dim_x, dim_y, dx, dy, basket_weave,
            separate_offs, continuum_mode,
            with_extra_output=False):
        """
        Calculate the observing time required for a given RMS.

        If "with_extra_output" is specified then a tuple of the
        elapsed time and a dictionary of extra output is returned.
        """

        output = self._calculate(
            calc_mode=self.RMS_TO_TIME, input_=rms,
            receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
            freq=freq, freq_res=freq_res,
            tau_225=tau_225, zenith_angle_deg=zenith_angle_deg,
            is_dsb=is_dsb, dual_polarization=dual_polarization,
            n_points=n_points,
            dim_x=dim_x, dim_y=dim_y, dx=dx, dy=dy,
            basket_weave=basket_weave, array_overscan=True,
            separate_offs=separate_offs, continuum_mode=continuum_mode)

        result = output['elapsed_time']

        if with_extra_output:
            extra = output['extra']
            extra['int_time'] = output['int_time']
            return (result, extra)

        return result

    def calculate_rms_for_elapsed_time(
            self, elapsed_time,
            receiver, map_mode, sw_mode,
            freq, freq_res,
            tau_225, zenith_angle_deg, is_dsb, dual_polarization,
            n_points,
            dim_x, dim_y, dx, dy, basket_weave,
            separate_offs, continuum_mode,
            with_extra_output=False):
        """
        Calculate the RMS obtained in a given elapsed time.

        If "with_extra_output" is specified then a tuple of the
        RMS and a dictionary of extra output is returned.
        """

        output = self._calculate(
            calc_mode=self.ELAPSED_TO_RMS, input_=elapsed_time,
            receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
            freq=freq, freq_res=freq_res,
            tau_225=tau_225, zenith_angle_deg=zenith_angle_deg,
            is_dsb=is_dsb, dual_polarization=dual_polarization,
            n_points=n_points,
            dim_x=dim_x, dim_y=dim_y, dx=dx, dy=dy,
            basket_weave=basket_weave, array_overscan=True,
            separate_offs=separate_offs, continuum_mode=continuum_mode)

        result = output['rms']

        if with_extra_output:
            extra = output['extra']
            extra['int_time'] = output['int_time']
            return (result, extra)

        return result

    def calculate_rms_for_int_time(
            self, int_time,
            receiver, map_mode, sw_mode,
            freq, freq_res,
            tau_225, zenith_angle_deg, is_dsb, dual_polarization,
            n_points,
            dim_x, dim_y, dx, dy, basket_weave,
            separate_offs, continuum_mode,
            with_extra_output=False):
        """
        Calculate the RMS obtained in a given integration time.

        If "with_extra_output" is specified then a tuple of the
        RMS and a dictionary of extra output is returned.
        """

        output = self._calculate(
            calc_mode=self.INT_TIME_TO_RMS, input_=int_time,
            receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
            freq=freq, freq_res=freq_res,
            tau_225=tau_225, zenith_angle_deg=zenith_angle_deg,
            is_dsb=is_dsb, dual_polarization=dual_polarization,
            n_points=n_points,
            dim_x=dim_x, dim_y=dim_y, dx=dx, dy=dy,
            basket_weave=basket_weave, array_overscan=True,
            separate_offs=separate_offs, continuum_mode=continuum_mode)

        result = output['rms']

        if with_extra_output:
            extra = output['extra']
            extra['elapsed_time'] = output['elapsed_time']
            return (result, extra)

        return result

    def _calculate(
            self, calc_mode, input_,
            receiver, map_mode, sw_mode,
            freq, freq_res,
            tau_225, zenith_angle_deg, is_dsb, dual_polarization,
            n_points,
            dim_x, dim_y, dx, dy, basket_weave, array_overscan,
            separate_offs, continuum_mode):
        """
        Perform ITC calculation.

        For raster maps:
        dim_x and dim_y are the dimensions of the map (in arc-seconds, and
        'x' being the direction along the scan when not basket weaving).
        dx and dy are the pixel size (in arc-seconds) except for array
        receivers where dx defines square pixels and dy defines the step
        made by the array between scans.

        Otherwise:
        n_points should be specified directly.
        """

        self._check_mode(receiver, map_mode, sw_mode, separate_offs)
        self._check_receiver_options(receiver, is_dsb, dual_polarization)

        extra_output = {}

        t_sys = self._calculate_t_sys(
            receiver=receiver, freq=freq, tau_225=tau_225,
            zenith_angle_deg=zenith_angle_deg, is_dsb=is_dsb,
            extra_output=extra_output)

        extra_output['t_sys'] = t_sys

        if map_mode == self.RASTER:
            overscan_x = 0.0
            overscan_y = 0.0

            array_info = HeterodyneReceiver.get_receiver_info(receiver).array

            if (array_info is not None) and array_overscan:
                overscan_x = 0.5 * array_info.size

            passes = 2 if basket_weave else 1

        else:
            passes = 1
            n_rows = 1

        int_times = []
        elapsed_times = []
        rmss = []

        for pass_ in range(0, passes):
            dy_adjusted = dy

            if map_mode == self.RASTER:
                if pass_ == 0:
                    # Non-basket weave, or primary basket-weave direction.
                    # TODO: should probably be ceil rather than floor + 1
                    n_points = int((dim_x + 2 * overscan_x) / dx) + 1

                    if ((array_info is not None) and
                            ((dim_y + 2 * overscan_y) <=
                                array_info.footprint)):
                        # Map height less than array footprint: do one scan
                        # and set dy=footprint to ensure multiscan factor is 1.
                        # TODO: better to calculate multiscan here rather than
                        # pass dy to calculation routines?
                        n_rows = 1
                        dy_adjusted = array_info.footprint
                    else:
                        n_rows = int((dim_y + 2 * overscan_y) / dy) + 1

                else:
                    # Secondary basket-weave direction: scan along "dim_y"
                    # but with overscan_x / dx still along scan direction (y)
                    # (and overscan_y / dy still across scan direction (x)).
                    # TODO: should probably be ceil rather than floor + 1
                    n_points = int((dim_y + 2 * overscan_x) / dx) + 1

                    if ((array_info is not None) and
                            ((dim_x + 2 * overscan_y)
                                <= array_info.footprint)):
                        # Map width less than footprint: as above for non-BW.
                        n_rows = 1
                        dy_adjusted = array_info.footprint
                    else:
                        n_rows = int((dim_x + 2 * overscan_y) / dy) + 1

            if calc_mode == self.RMS_TO_TIME:
                int_time = self._integration_time_for_rms(
                    rms=input_,
                    receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
                    n_points=n_points, separate_offs=separate_offs,
                    dual_polarization=dual_polarization,
                    t_sys=t_sys, freq_res=freq_res, dy=dy_adjusted)

                elapsed_time = self._elapsed_time_for_integration_time(
                    time=int_time, n_rows=n_rows,
                    map_mode=map_mode, sw_mode=sw_mode,
                    n_points=n_points, separate_offs=separate_offs,
                    continuum_mode=continuum_mode)

                int_times.append(int_time)
                elapsed_times.append(elapsed_time)

            elif calc_mode == self.INT_TIME_TO_RMS:
                rms = self._rms_in_integration_time(
                    time=input_,
                    receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
                    n_points=n_points, separate_offs=separate_offs,
                    dual_polarization=dual_polarization,
                    t_sys=t_sys, freq_res=freq_res, dy=dy_adjusted)

                elapsed_time = self._elapsed_time_for_integration_time(
                    time=input_, n_rows=n_rows,
                    map_mode=map_mode, sw_mode=sw_mode,
                    n_points=n_points, separate_offs=separate_offs,
                    continuum_mode=continuum_mode)

                rmss.append(rms)
                elapsed_times.append(elapsed_time)

            elif calc_mode == self.ELAPSED_TO_RMS:
                int_time = self._integration_time_for_elapsed_time(
                    elapsed=input_, n_rows=n_rows,
                    map_mode=map_mode, sw_mode=sw_mode,
                    n_points=n_points, separate_offs=separate_offs,
                    continuum_mode=continuum_mode)

                rms = self._rms_in_integration_time(
                    time=int_time,
                    receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
                    n_points=n_points, separate_offs=separate_offs,
                    dual_polarization=dual_polarization,
                    t_sys=t_sys, freq_res=freq_res, dy=dy_adjusted)

                int_times.append(int_time)
                rmss.append(rms)

        return {
            'rms': None if not rmss else (sum(rmss) / passes),
            'int_time': None if not int_times else (sum(int_times) / passes),
            'elapsed_time': None if not elapsed_times else (
                sum(elapsed_times) / passes),
            'extra': extra_output,
        }

    def _check_mode(self, receiver, map_mode, sw_mode, separate_offs):
        """
        Check whether the given mode is supported.

        Raises HeterodyneITCError if the mode is not supported.
        """

        if (map_mode, sw_mode) not in self.valid_modes:
            raise HeterodyneITCError(
                'The combination of mapping and switching modes is invalid.')

        if separate_offs:
            if map_mode == self.RASTER:
                raise HeterodyneITCError(
                    'Separate offs should not be used in raster mode.')

            elif map_mode == self.GRID and sw_mode == self.PSSW:
                raise HeterodyneITCError(
                    'Separate offs should not be used in grid pssw.')

    def _check_receiver_options(self, receiver, is_dsb, dual_polarization):
        """
        Check whether the given receiver options are supported.

        Raises HeterodyneITCError if a problem is found.
        """

        rx_info = HeterodyneReceiver.get_receiver_info(receiver)

        if dual_polarization and (rx_info.n_mix < 2):
            raise HeterodyneITCError(
                'Dual polarization is not possible with this receiver.')

        if is_dsb:
            if not rx_info.dsb_available:
                raise HeterodyneITCError(
                    'This receiver does not support DSB operation.')

        else:
            if not rx_info.ssb_available:
                raise HeterodyneITCError(
                    'This receiver does not support SSB operation.')

    def _calculate_t_sys(
            self, receiver, freq, tau_225, zenith_angle_deg,
            is_dsb, extra_output=None):
        """
        Calculate the system temperature.

        "extra_output" can optionally be a dictionary into which extra
        data are written, e.g. T_rx.
        """

        t_im = 0.0

        t_rx = HeterodyneReceiver.get_interpolated_t_rx(
            receiver=receiver, freq=freq)

        tau = HeterodyneReceiver.get_interpolated_opacity(
            tau_225=tau_225, freq=freq)

        if extra_output is not None:
            extra_output['t_rx'] = t_rx
            extra_output['tau'] = tau

        nu_sky = exp(- tau / cos(radians(zenith_angle_deg)))

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

    def _rms_in_integration_time(
            self, time,
            receiver, map_mode, sw_mode,
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
            np_shared = int(self.time_between_refs / time)

            if np_shared < 1:
                np_shared = 1

            if np_shared > n_points:
                np_shared = n_points

        # Array overlap factor.
        multiscan = 1.0
        # For arrays, if the dy is less than the footprint, take the
        # overlap into account when rasterizing.
        array_info = HeterodyneReceiver.get_receiver_info(receiver).array
        if (map_mode == self.RASTER) and (array_info is not None):
            multiscan = 1.0 / sqrt(array_info.footprint / dy)

        rms = (
            multiscan * het_fudge * het_dfact *
            sqrt(1 + 1 / sqrt(np_shared)) * t_sys /
            sqrt(freq_res * 1.0e6 * time))

        # Apply correction for dual polarization.
        if receiver == HeterodyneReceiver.WD and dual_polarization:
            rms /= sqrt(2.0)

        return rms

    def _integration_time_for_rms(
            self, rms,
            receiver, map_mode, sw_mode,
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
            np_shared = int(self.time_between_refs / time)

            if np_shared < 1:
                np_shared = 1

            if np_shared > n_points:
                np_shared = n_points

        # Iterate in the case of GRID PSSW because np_shared depends on time.
        for step in range(0, 5):
            i_rms = self._rms_in_integration_time(
                time, receiver, map_mode, sw_mode,
                n_points, separate_offs, *args, **kwargs)

            # TODO: remove rounding to nearest 0.1 s?
            time = int(10 * time * (i_rms / rms) ** 2 + 0.5) / 10

            if map_mode == self.GRID and sw_mode == self.PSSW:
                np_shared_used = np_shared

                np_shared = int(self.time_between_refs / time)

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
            raise HeterodyneITCError(
                'Duration parameters unknown for '
                'map mode {0} and switching mode {1}'.format(
                    map_mode, sw_mode))

        return DurationParam(a=a, b=b, c=c, d=d, e=e)

    def _elapsed_time_for_integration_time(
            self, time, n_rows,
            map_mode, sw_mode,
            n_points, separate_offs,
            continuum_mode):
        """
        Calculate the elapsed time of an observation.

        n_rows should be 1 for non-raster observations.
        """

        param = self._get_duration_param(
            map_mode=map_mode, sw_mode=sw_mode,
            n_points=n_points, separate_offs=separate_offs,
            continuum_mode=continuum_mode)

        return param.e * (
            param.a + n_rows * (
                param.b * n_points * time +
                param.c * sqrt(n_points) * time +
                param.d)
        )

    def _integration_time_for_elapsed_time(
            self, elapsed, n_rows,
            map_mode, sw_mode,
            n_points, separate_offs,
            continuum_mode):
        """
        Calculate the integration time of an observation based on the
        elapsed time.

        n_rows should be 1 for non-raster observations.
        """

        param = self._get_duration_param(
            map_mode=map_mode, sw_mode=sw_mode,
            n_points=n_points, separate_offs=separate_offs,
            continuum_mode=continuum_mode)

        time = (
            (elapsed / param.e - param.a - n_rows * param.d) /
            (n_rows * (param.b * n_points + param.c * sqrt(n_points))))

        # TODO: remove rounding to nearest 0.1 s?
        return int(10 * time + 0.5) / 10
