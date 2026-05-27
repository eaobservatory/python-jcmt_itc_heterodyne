JCMT Heterodyne Integration Time Calculator
===========================================

Introduction
------------

This package contains the Python-based integration time calculator
for JCMT heterodyne instruments.  It is based on the original Perl
HITEC software.

Usage
-----

The integration time calculator (ITC) can be used in a Python program
via a `HeterodyneITC` object.
The main calculation methods are
`calculate_time`, `calculate_rms_for_elapsed_time` and
`calculate_rms_for_int_time`.
Each of these takes an optional `with_extra_output` argument.
If this is not specified, only the main answer is returned,
but if a true value is given, a `(result, extra)` pair is
returned, where `extra` is a dictionary of supplemental information.

Here is an example time calculation for a HARP jiggle-chop observation:

.. code-block:: python

    from jcmt_itc_heterodyne import \
        HeterodyneITC, HeterodyneITCError, HeterodyneReceiver

    itc = HeterodyneITC()

    try:
        (result, extra) = itc.calculate_time(
            rms=0.1,  # K TA*
            receiver=HeterodyneReceiver.HARP,
            map_mode=HeterodyneITC.JIGGLE,
            sw_mode=HeterodyneITC.BMSW,
            freq=345.796,  # GHz
            freq_res=0.488,  # MHz
            tau_225=0.1,
            zenith_angle_deg=30.0,
            is_dsb=False,
            dual_polarization=False,
            n_points=25,  # HARP5 pattern
            dim_x=None,
            dim_y=None,
            dx=None,
            dy=None,
            basket_weave=False,
            separate_offs=False,
            continuum_mode=False,
            sideband=None,
            if_freq=None,
            with_extra_output=True)

        print('Main result: {}'.format(result))
        print('Extra information: {!r}'.format(extra))

    except HeterodyneITCError as e:
        print('Error: {}'.format(e))

For raster observations, the size of the map is specified via
the `dim_x` and `dim_y` parameters.  The pixel size is given
by `dx` and `dy` for single pixel receivers.  For array receivers,
`dy` is the scan spacing and the size of the map is adjusted
based on the `array_overscan_x` and `array_overscan_y` parameters.
Along the scan direction, `array_overscan_x` adds half of the array
"size" (ignoring rotation), i.e. the "radius", at each end of the scan
(`dim_x`).  This parameter defaults to `True` since it matches
the behavior of the telescope control system.  In the other direction,
`array_overscan_y` adds extra rows so that points in the specified
size (`dim_y`) are observed as many times as the coverage
implied by the selected spacing (`dy`), based on the array "footprint"
(including rotation).  This parameter defaults to `False` and,
to include these extra rows, any observation must include the
corresponding additional size in the non-scan direction.
The modified size is returned in the `extra` parameter `overscanned_dim_y`.

The `HeterodyneITC` object also has various utility methods such
as `velocity_to_freq_res` and `estimate_zenith_angle_deg`.

License
-------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
