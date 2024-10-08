# Copyright (C) 2007-2009 Science and Technology Facilities Council.
# Copyright (C) 2015-2024 East Asian Observatory
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
from math import acos, atan, ceil, cos, degrees, exp, pow, radians, sqrt

from .error import HeterodyneITCError
from .receiver import HeterodyneReceiver
from .version import version


default_time_between_refs = 30.0
speed_of_light = 299792458

# J_m: mean radiation temperature of sky.
j_m = 260
# J_tel: mean radiation temperature of telescope enclosure.
j_tel = 265

DurationParam = namedtuple(
    'DurationParam',
    ('a', 'b', 'c', 'd', 'e', 'block_min'))


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
        (GRID, FRSW),
        (JIGGLE, PSSW),
        (JIGGLE, BMSW),
        (JIGGLE, FRSW),
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

    RV_DEF_OPT = 1
    RV_DEF_RAD = 2

    int_time_minimum = 0.1

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

    def velocity_to_redshift(self, velocity, velocity_definition):
        """
        Convert a radial velocity (in km/s) to a reshift value.
        """

        # Scale: 10^3 (km/s)
        v = velocity * 1.0e3

        if v >= speed_of_light:
            raise HeterodyneITCError('Radial velocity is too high.')

        if velocity_definition == self.RV_DEF_OPT:
            return v / speed_of_light

        elif velocity_definition == self.RV_DEF_RAD:
            return v / (speed_of_light - v)

        raise HeterodyneITCError('Invalid radial velocity definition.')

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
            if_freq=None, sideband=None,
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
            separate_offs=separate_offs, continuum_mode=continuum_mode,
            if_freq=if_freq, sideband=sideband)

        result = output['elapsed_time']

        if with_extra_output:
            extra = output['extra']
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
            if_freq=None, sideband=None,
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
            separate_offs=separate_offs, continuum_mode=continuum_mode,
            if_freq=if_freq, sideband=sideband)

        result = output['rms']

        if with_extra_output:
            extra = output['extra']
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
            if_freq=None, sideband=None,
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
            separate_offs=separate_offs, continuum_mode=continuum_mode,
            if_freq=if_freq, sideband=sideband)

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
            separate_offs, continuum_mode, if_freq, sideband):
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
        self._check_receiver_options(
            receiver, is_dsb, dual_polarization, sw_mode)

        try:
            extra_output = {}

            t_sys = self._calculate_t_sys(
                receiver=receiver, freq=freq, tau_225=tau_225,
                zenith_angle_deg=zenith_angle_deg, is_dsb=is_dsb,
                if_freq=if_freq, sideband=sideband,
                extra_output=extra_output)

            extra_output['t_sys'] = t_sys

            elapsed_times = []
            rmss = []

            passes = 1

            if map_mode != self.RASTER:
                basket_weave = False
                n_rows = 1

            else:
                array_info = HeterodyneReceiver.get_receiver_info(
                    receiver).array

                if basket_weave:
                    passes = 2

                    if calc_mode == self.INT_TIME_TO_RMS:
                        basket_split = self._split_basket_weave_int_time(
                            int_time=input_, receiver=receiver,
                            freq_res=freq_res,
                            dual_polarization=dual_polarization,
                            continuum_mode=continuum_mode,
                            dim_x=dim_x, dim_y=dim_y, dx=dx, dy=dy,
                            array_info=array_info,
                            array_overscan=array_overscan,
                            t_sys=t_sys)

                    elif calc_mode == self.ELAPSED_TO_RMS:
                        basket_split = self._split_basket_weave_elapsed_time(
                            elapsed_time=input_, receiver=receiver,
                            freq_res=freq_res,
                            dual_polarization=dual_polarization,
                            continuum_mode=continuum_mode,
                            dim_x=dim_x, dim_y=dim_y, dx=dx, dy=dy,
                            array_info=array_info,
                            array_overscan=array_overscan,
                            t_sys=t_sys)

            for pass_ in range(0, passes):
                pass_extra = {} if (passes > 1) else extra_output

                if map_mode != self.RASTER:
                    dy_adjusted = dy

                else:
                    if pass_ == 0:
                        # Non-basket weave, or primary basket-weave direction.
                        (n_rows, n_points, dy_adjusted) = self._get_raster_parameters(
                            dim_x, dim_y, dx, dy, array_info, array_overscan)

                    else:
                        # Secondary basket-weave direction: scan along "dim_y"
                        # but with overscan_x / dx
                        # still along scan direction (y)
                        # (and overscan_y / dy
                        # still across scan direction (x)).
                        (n_rows, n_points, dy_adjusted) = self._get_raster_parameters(
                            dim_y, dim_x, dx, dy, array_info, array_overscan)

                    pass_extra['raster_n_points'] = n_points
                    pass_extra['raster_n_rows'] = n_rows

                if calc_mode == self.RMS_TO_TIME:
                    rms = input_
                    if basket_weave:
                        rms *= sqrt(2.0)

                    int_time = self._integration_time_for_rms(
                        rms=rms,
                        receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
                        n_points=n_points, separate_offs=separate_offs,
                        dual_polarization=dual_polarization,
                        t_sys=t_sys, freq_res=freq_res, dy=dy_adjusted)

                    self._check_int_time(
                        int_time, 'requested target sensitivity',
                        basket_weave=basket_weave)

                    pass_extra['int_time'] = int_time

                    elapsed_time = self._elapsed_time_for_integration_time(
                        time=int_time, n_rows=n_rows,
                        map_mode=map_mode, sw_mode=sw_mode,
                        n_points=n_points, separate_offs=separate_offs,
                        continuum_mode=continuum_mode,
                        extra_output=pass_extra)

                    elapsed_times.append(elapsed_time)

                elif calc_mode == self.INT_TIME_TO_RMS:
                    int_time = input_
                    if basket_weave:
                        int_time *= basket_split[pass_]
                        pass_extra['int_time'] = int_time

                    # If basket weaving, this will have been checked in
                    # _split_basket_weave_int_time, so only mention std. limit.
                    if int_time < self.int_time_minimum:
                        raise HeterodyneITCError(
                            'The requested integration time per point '
                            'is less than {0:.3f} seconds which is the '
                            'minimum possible sample time. '
                            'Please increase the integration time per point '
                            'to at least {0:.3f} seconds.'.format(
                                self.int_time_minimum))

                    rms = self._rms_in_integration_time(
                        time=int_time,
                        receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
                        n_points=n_points, separate_offs=separate_offs,
                        dual_polarization=dual_polarization,
                        t_sys=t_sys, freq_res=freq_res, dy=dy_adjusted)

                    elapsed_time = self._elapsed_time_for_integration_time(
                        time=int_time, n_rows=n_rows,
                        map_mode=map_mode, sw_mode=sw_mode,
                        n_points=n_points, separate_offs=separate_offs,
                        continuum_mode=continuum_mode,
                        extra_output=pass_extra)

                    rmss.append(rms)
                    elapsed_times.append(elapsed_time)

                elif calc_mode == self.ELAPSED_TO_RMS:
                    elapsed_time = input_
                    if basket_weave:
                        elapsed_time *= basket_split[pass_]

                    int_time = self._integration_time_for_elapsed_time(
                        elapsed=elapsed_time, n_rows=n_rows,
                        map_mode=map_mode, sw_mode=sw_mode,
                        n_points=n_points, separate_offs=separate_offs,
                        continuum_mode=continuum_mode,
                        extra_output=pass_extra)

                    self._check_int_time(
                        int_time, 'requested elapsed time',
                        basket_weave=basket_weave)

                    pass_extra['int_time'] = int_time

                    rms = self._rms_in_integration_time(
                        time=int_time,
                        receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
                        n_points=n_points, separate_offs=separate_offs,
                        dual_polarization=dual_polarization,
                        t_sys=t_sys, freq_res=freq_res, dy=dy_adjusted)

                    rmss.append(rms)

                if passes > 1:
                    assert pass_extra is not extra_output
                    for (key, value) in pass_extra.items():
                        extra_output['{}_{}'.format(key, pass_ + 1)] = value

            return {
                'rms': None if not rmss else (
                    self._combine_rms(rmss)),
                'elapsed_time': None if not elapsed_times else (
                    sum(elapsed_times)),
                'extra': extra_output,
            }

        except ZeroDivisionError:
            raise HeterodyneITCError(
                'Division by zero error occurred during calculation.')

        except ValueError as e:
            if e.args[0] == 'math domain error':
                raise HeterodyneITCError(
                    'Negative square root error occurred during calculation.')
            raise

    def _combine_rms(self, rmss):
        """
        Calculate RMS for combination of observations.
        """

        if 1 == len(rmss):
            return rmss[0]

        sum_ = 0.0

        for rms in rmss:
            sum_ += pow(rms, -2)

        return pow(sum_, -0.5)

    def _get_raster_parameters(
            self, dim_x, dim_y, dx, dy, array_info, array_overscan):
        """
        Obtain raster map parameters: n_rows, n_points and adjusted dy.
        """

        overscan_x = 0.0
        overscan_y = 0.0

        if (array_info is not None) and array_overscan:
            overscan_x = 0.5 * array_info.size

        dy_adjusted = dy

        # TODO: should probably be ceil rather than floor + 1
        n_points = int((dim_x + 2 * overscan_x) / dx) + 1

        if ((array_info is not None)
                and ((dim_y + 2 * overscan_y) <= array_info.footprint)):
            # Map height less than array footprint: do one scan
            # and set dy=footprint to ensure multiscan factor
            # is 1.
            # TODO: better to calculate multiscan here rather
            # than pass dy to calculation routines?
            n_rows = 1
            dy_adjusted = array_info.footprint

        else:
            n_rows = int((dim_y + 2 * overscan_y) / dy) + 1

        return (n_rows, n_points, dy_adjusted)

    def _split_basket_weave_int_time(self, **kwargs):
        """
        Attempt to determine how best to split the given integration
        time into two directions of a basket weaved raster.  Returns
        a list giving the fraction of time to spend in each direction.
        """

        best_frac = self._split_basket_weave_search(
            lambda frac: self._split_basket_weave_int_rms_ratio(
                frac=frac, **kwargs))

        return [best_frac, 1.0 - best_frac]

    def _split_basket_weave_elapsed_time(self, **kwargs):
        """
        Attempt to determine how best to split the given elapsed time
        into two directions of a basket weaved raster.  Returns
        a list giving the fraction of time to spend in each direction.
        """

        best_frac = self._split_basket_weave_search(
            lambda frac: self._split_basket_weave_elapsed_rms_ratio(
                frac=frac, **kwargs))

        return [best_frac, 1.0 - best_frac]

    def _split_basket_weave_search(self, func):
        best_frac = None
        best_ratio = None

        frac_min = 0.01
        frac_max = 1.00
        frac_step = 0.05

        for step in range(0, 4):
            frac = frac_min
            frac_valid_min = None
            frac_valid_max = None
            while frac < frac_max:
                try:
                    rms_ratio = func(frac)

                    if ((best_ratio is None)
                            or (abs(rms_ratio - 1.0) < abs(best_ratio - 1))):
                        best_frac = frac
                        best_ratio = rms_ratio

                    frac_valid_max = frac
                    if frac_valid_min is None:
                        frac_valid_min = frac

                except HeterodyneITCError:
                    pass

                frac += frac_step

            if best_frac is None:
                raise HeterodyneITCError(
                    'The basket weave splitting algorithm was unable to '
                    'divide the given time between the two scan directions. '
                    'Please try increasing the time '
                    'or deselecting basket weave '
                    'in case the integration time per point '
                    'would have been below the minimum possible sample time '
                    'of {:.3f} seconds in either scan direction.'.format(
                        self.int_time_minimum))

            frac_step /= 10.0
            frac_min = max(frac_valid_min, best_frac - 15 * frac_step)
            frac_max = max(frac_valid_min, best_frac + 16 * frac_step)

        return best_frac

    def _split_basket_weave_int_rms_ratio(
            self, frac, int_time, receiver, freq_res,
            dual_polarization, continuum_mode,
            dim_x, dim_y, dx, dy, array_info, array_overscan,
            t_sys):
        # Assumed parameters for raster mode.
        map_mode = self.RASTER
        sw_mode = self.PSSW
        separate_offs = False

        # First direction.
        int_part = frac * int_time

        (n_rows, n_points, dy_adjusted) = self._get_raster_parameters(
            dim_x, dim_y, dx, dy, array_info, array_overscan)

        self._check_int_time(int_part, 'splitting algorithm')

        rms_1 = self._rms_in_integration_time(
            time=int_part,
            receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
            n_points=n_points, separate_offs=separate_offs,
            dual_polarization=dual_polarization,
            t_sys=t_sys, freq_res=freq_res, dy=dy_adjusted)

        # Second direction.
        int_part = (1.0 - frac) * int_time

        (n_rows, n_points, dy_adjusted) = self._get_raster_parameters(
            dim_y, dim_x, dx, dy, array_info, array_overscan)

        self._check_int_time(int_part, 'splitting algorithm')

        rms_2 = self._rms_in_integration_time(
            time=int_part,
            receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
            n_points=n_points, separate_offs=separate_offs,
            dual_polarization=dual_polarization,
            t_sys=t_sys, freq_res=freq_res, dy=dy_adjusted)

        return rms_1 / rms_2

    def _split_basket_weave_elapsed_rms_ratio(
            self, frac, elapsed_time, receiver, freq_res,
            dual_polarization, continuum_mode,
            dim_x, dim_y, dx, dy, array_info, array_overscan,
            t_sys):
        # Assumed parameters for raster mode.
        map_mode = self.RASTER
        sw_mode = self.PSSW
        separate_offs = False

        # First direction.
        elapsed_part = frac * elapsed_time

        (n_rows, n_points, dy_adjusted) = self._get_raster_parameters(
            dim_x, dim_y, dx, dy, array_info, array_overscan)

        int_time = self._integration_time_for_elapsed_time(
            elapsed=elapsed_part, n_rows=n_rows,
            map_mode=map_mode, sw_mode=sw_mode,
            n_points=n_points, separate_offs=separate_offs,
            continuum_mode=continuum_mode)

        self._check_int_time(int_time, 'splitting algorithm')

        rms_1 = self._rms_in_integration_time(
            time=int_time,
            receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
            n_points=n_points, separate_offs=separate_offs,
            dual_polarization=dual_polarization,
            t_sys=t_sys, freq_res=freq_res, dy=dy_adjusted)

        # Second direction.
        elapsed_part = (1.0 - frac) * elapsed_time

        (n_rows, n_points, dy_adjusted) = self._get_raster_parameters(
            dim_y, dim_x, dx, dy, array_info, array_overscan)

        int_time = self._integration_time_for_elapsed_time(
            elapsed=elapsed_part, n_rows=n_rows,
            map_mode=map_mode, sw_mode=sw_mode,
            n_points=n_points, separate_offs=separate_offs,
            continuum_mode=continuum_mode)

        self._check_int_time(int_time, 'splitting algorithm')

        rms_2 = self._rms_in_integration_time(
            time=int_time,
            receiver=receiver, map_mode=map_mode, sw_mode=sw_mode,
            n_points=n_points, separate_offs=separate_offs,
            dual_polarization=dual_polarization,
            t_sys=t_sys, freq_res=freq_res, dy=dy_adjusted)

        return rms_1 / rms_2

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

    def _check_receiver_options(
            self, receiver, is_dsb, dual_polarization, sw_mode):
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

        if sw_mode == self.FRSW:
            if not rx_info.frsw_available:
                raise HeterodyneITCError(
                    'This receiver does not support frequency switching.')

    def _check_int_time(self, int_time, origin, basket_weave=False):
        """
        Check whether the integration time is allowed.

        :param int_time: the time to check
        :param origin: text used in the error message
        :param basket_weave: whether to mention basket weaving in the message

        :raises HeterodyneITCError: if the time is less than 0.1
        """

        if int_time < self.int_time_minimum:
            raise HeterodyneITCError(
                'The {} led to an integration time of {:.3f} seconds per '
                'point. '
                'This is less than {:.3f} seconds which is the minimum '
                'possible sample time{}. '
                'Please try adjusting the input parameters to '
                'increase the integration time per point{}.'.format(
                    origin, int_time, self.int_time_minimum,
                    (' in each basket weave direction' if basket_weave else ''),
                    (' or deselecting basket weave' if basket_weave else '')))

    def _get_efficiencies_temperatures(
            self, receiver, freq, tau_225, zenith_angle_deg,
            extra_output=None):
        """
        Get efficiency and temperature values for a system temperature
        calculation.
        """

        t_im = 0.0

        tau = HeterodyneReceiver.get_interpolated_opacity(
            tau_225=tau_225, freq=freq)

        eta_sky = exp(- tau / cos(radians(zenith_angle_deg)))

        t_sky = j_m * (1 - eta_sky)

        eta_tel = HeterodyneReceiver.get_receiver_info(receiver).eta_tel

        t_tel = j_tel * (1 - eta_tel)

        if extra_output is not None:
            extra_output['tau'] = tau
            extra_output['eta_sky'] = eta_sky

        return (eta_sky, eta_tel, t_sky, t_tel, t_im)

    def _calculate_t_sys(
            self, receiver, freq, tau_225, zenith_angle_deg,
            is_dsb, if_freq, sideband, extra_output=None):
        """
        Calculate the system temperature.

        "extra_output" can optionally be a dictionary into which extra
        data are written, e.g. T_rx.
        """

        (eta_sky, eta_tel, t_sky, t_tel, t_im) = self._get_efficiencies_temperatures(
            receiver, freq, tau_225, zenith_angle_deg,
            extra_output=extra_output)

        t_rx = HeterodyneReceiver.get_interpolated_t_rx(
            receiver=receiver, sky_freq=freq,
            if_freq=if_freq, sideband=sideband,
            extra_output=extra_output)

        if extra_output is not None:
            extra_output['t_rx'] = t_rx

        if not is_dsb:
            # Single sideband mode.

            return (
                (t_rx + eta_tel * t_sky + t_tel + t_im) /
                (eta_sky * eta_tel))

        else:
            # Dual sideband mode.

            return (
                2.0 * (t_rx + eta_tel * t_sky + t_tel) /
                (eta_sky * eta_tel))

    def _estimate_t_rx_from_t_sys(
            self, receiver, freq, tau_225, zenith_angle_deg,
            is_dsb, if_freq, sideband, t_sys, extra_output=None):
        """
        Estimate receiver temperature from a measurement of system temperature.

        This applies the inverse relation of the `_calculate_t_sys` method.
        """

        (eta_sky, eta_tel, t_sky, t_tel, t_im) = self._get_efficiencies_temperatures(
            receiver, freq, tau_225, zenith_angle_deg,
            extra_output=extra_output)

        numerator = t_sys * eta_sky * eta_tel

        if not is_dsb:
            # Single sideband mode.

            numerator -= t_im

        else:
            # Dual sideband mode.

            numerator /= 2.0

        return numerator - (eta_tel * t_sky + t_tel)

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

        # Set np_shared to 1 if separate offs requested, or if mode
        # is FRSW as it does not have offset positions.
        if separate_offs or (sw_mode == self.FRSW):
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
            multiscan = sqrt(
                dy / (array_info.footprint * array_info.fraction_available))

        rms = (
            multiscan * het_fudge * het_dfact *
            sqrt(1 + 1 / sqrt(np_shared)) * t_sys /
            sqrt(freq_res * 1.0e6 * time))

        # Apply correction for dual polarization.
        if dual_polarization:
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

            time = time * (i_rms / rms) ** 2

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
        block_min = 30

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
            block_min = 45

        elif (sw_mode == self.FRSW and (
                map_mode == self.JIGGLE or map_mode == self.GRID)):
            a = 67
            b = 1.023

        else:
            raise HeterodyneITCError(
                'Duration parameters unknown for '
                'map mode {0} and switching mode {1}'.format(
                    map_mode, sw_mode))

        return DurationParam(a=a, b=b, c=c, d=d, e=e, block_min=block_min)

    def _elapsed_time_for_integration_time(
            self, time, n_rows,
            map_mode, sw_mode,
            n_points, separate_offs,
            continuum_mode,
            extra_output=None):
        """
        Calculate the elapsed time of an observation.

        n_rows should be 1 for non-raster observations.
        """

        param = self._get_duration_param(
            map_mode=map_mode, sw_mode=sw_mode,
            n_points=n_points, separate_offs=separate_offs,
            continuum_mode=continuum_mode)

        time_src = param.e * n_rows * (
                param.b * n_points * time +
                param.c * sqrt(n_points) * time +
                param.d)

        if extra_output is not None:
            extra_output['time_src'] = time_src

        overhead = self._estimate_overhead(param, time_src, from_total=False)

        return time_src + overhead

    def _integration_time_for_elapsed_time(
            self, elapsed, n_rows,
            map_mode, sw_mode,
            n_points, separate_offs,
            continuum_mode,
            extra_output=None):
        """
        Calculate the integration time of an observation based on the
        elapsed time.

        n_rows should be 1 for non-raster observations.
        """

        param = self._get_duration_param(
            map_mode=map_mode, sw_mode=sw_mode,
            n_points=n_points, separate_offs=separate_offs,
            continuum_mode=continuum_mode)

        overhead = self._estimate_overhead(param, elapsed, from_total=True)

        time_src = elapsed - overhead

        if extra_output is not None:
            extra_output['time_src'] = time_src

        time = (
            (time_src / param.e - n_rows * param.d) /
            (n_rows * (param.b * n_points + param.c * sqrt(n_points))))

        return time

    def _estimate_overhead(self, param, time_sec, from_total=False):
        """
        Estimate observing overhead in seconds.
        """

        block_sec = param.block_min * 60.0

        overhead_sec = param.e * param.a

        if from_total:
            block_sec += overhead_sec

        return overhead_sec * ceil(time_sec / block_sec)
