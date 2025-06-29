#!/usr/bin/env python
# coding: utf-8
# projections class - Perform CRS projections

import numpy as np
import math
import os
import pickle
import glob

from romgeo_lite import crs
from romgeo_lite import projections
from romgeo_lite import transformations


def _spline_params(xk, yk):
    # Return parameters of bicubic spline surface
    return (0.0,                  # Initial dummy parameter
            1.0,                  # Parameter 1
            xk,                   # Parameter 2
            xk**2,                # Parameter 3
            xk**3,                # Parameter 4
            yk,                   # Parameter 5
            xk * yk,              # Parameter 6
            xk**2 * yk,           # Parameter 7
            xk**3 * yk,           # Parameter 8
            yk**2,                # Parameter 9
            xk * yk**2,           # Parameter 10
            xk**2 * yk**2,        # Parameter 11
            xk**3 * yk**2,        # Parameter 12
            yk**3,                # Parameter 13
            xk * yk**3,           # Parameter 14
            xk**2 * yk**3,        # Parameter 15
            xk**3 * yk**3)        # Parameter 16


def _spline_grid(grid, cell_x, cell_y):
    # Return the 16 unknown coefficients of the interpolated surface
    return (0.0,                                  # Dummy parameter
            grid[cell_y - 1, cell_x],             # Parameter 1
            grid[cell_y - 1, cell_x + 1],         # Parameter 2
            grid[cell_y - 1, cell_x + 2],         # Parameter 3
            grid[cell_y - 1, cell_x + 3],         # Parameter 4
            grid[cell_y, cell_x],                 # Parameter 5
            grid[cell_y, cell_x + 1],             # Parameter 6
            grid[cell_y, cell_x + 2],             # Parameter 7
            grid[cell_y, cell_x + 3],             # Parameter 8
            grid[cell_y + 1, cell_x],             # Parameter 9
            grid[cell_y + 1, cell_x + 1],         # Parameter 10
            grid[cell_y + 1, cell_x + 2],         # Parameter 11
            grid[cell_y + 1, cell_x + 3],         # Parameter 12
            grid[cell_y + 2, cell_x],             # Parameter 13
            grid[cell_y + 2, cell_x + 1],         # Parameter 14
            grid[cell_y + 2, cell_x + 2],         # Parameter 15
            grid[cell_y + 2, cell_x + 3])         # Parameter 16


def _doBSInterpolation(x, y, minx, miny, stepx, stepy, grid):

    offset_x = abs((x - minx) / stepx)
    offset_y = abs((y - miny) / stepy)
    cell_x = int(offset_x)
    cell_y = int(offset_y)

    xk = minx + cell_x * stepx # {lambda of point 6 / East of point 6}
    yk = miny + cell_y * stepy # {phi of point 6 / North of point 6}

    # {relative coordinate of point X:}
    xk = (x - xk) / stepx
    yk = (y - yk) / stepy

    if cell_x < -1 or cell_x + 3 >= grid.shape[1] or cell_y < -1 or cell_y + 3 >= grid.shape[0]:
        return np.nan

    # Slice grid to coordinates
    az = transformations._spline_grid(grid, cell_x-1, cell_y)

    # {Parameters of bicubic spline surface}
    ff = transformations._spline_params(xk, yk)

    # Linear coefficients
    cf_1 = az[6]
    cf_2 = az[7]
    cf_3 = az[10]
    cf_4 = az[11]

    # Derivatives in the East-direction and the North-direction

    cf_5 = (-az[8] + 4 * az[7] - 3 * az[6]) / 2
    cf_6 = (3 * az[7] - 4 * az[6] + az[5]) / 2
    cf_7 = (-az[12] + 4 * az[11] - 3 * az[10]) / 2
    cf_8 = (3 * az[11] - 4 * az[10] + az[9]) / 2
    cf_9 = (-az[14] + 4 * az[10] - 3 * az[6]) / 2
    cf_10 = (-az[15] + 4 * az[11] -3 * az[7]) / 2
    cf_11 = (3 * az[10] - 4 * az[6] + az[2]) / 2
    cf_12 = (3 * az[11] - 4 * az[7] + az[3]) / 2

    # Equations for the cross derivative

    cf_13 = ((az[1] + az[11]) - (az[3] + az[9])) / 4
    cf_14 = ((az[2] + az[12]) - (az[4] + az[10])) / 4
    cf_15 = ((az[5] + az[15]) - (az[7] + az[13])) / 4
    cf_16 = ((az[6] + az[16]) - (az[8] + az[14])) / 4

    # Determining the 16 unknown coefficients of the interpolated surface

    shift_value = cf_1 * ff[1]
    shift_value += cf_5 * ff[2]
    shift_value += (-3 * cf_1 + 3 * cf_2 - 2 * cf_5 -cf_6) * ff[3]
    shift_value += (2 * cf_1 - 2 * cf_2 + cf_5 + cf_6) * ff[4]
    shift_value += cf_9 * ff[5]
    shift_value += cf_13 * ff[6]
    shift_value += (-3 * cf_9 + 3 * cf_10 - 2 * cf_13 - cf_14) * ff[7]
    shift_value += (2 * cf_9 - 2 * cf_10 + cf_13 + cf_14) * ff[8]
    shift_value += (-3 * cf_1 + 3 * cf_3 - 2 * cf_9 - cf_11) * ff[9]
    shift_value += (-3 * cf_5 + 3 *cf_7 - 2 * cf_13 - cf_15) * ff[10]
    shift_value += (9 * cf_1 - 9 * cf_2 - 9 * cf_3 + 9 * cf_4 + 6 * cf_5 + 3 * cf_6 - 6 * cf_7 - 3 * cf_8 +
                    6 * cf_9 - 6 * cf_10 + 3 * cf_11 - 3 * cf_12 + 4 * cf_13 + 2 * cf_14 + 2 * cf_15 + cf_16) * ff[11]
    shift_value += (-6 * cf_1 + 6 * cf_2 + 6 * cf_3 - 6 * cf_4 - 3 * cf_5 - 3 * cf_6 + 3 * cf_7 + 3 * cf_8 -
                    4 * cf_9 + 4 * cf_10 - 2 * cf_11 + 2 * cf_12 - 2 * cf_13 - 2 * cf_14 - cf_15 - cf_16) * ff[12]
    shift_value += (2 * cf_1 - 2 * cf_3 + cf_9 + cf_11) * ff[13]
    shift_value += (2 * cf_5 - 2 * cf_7 + cf_13 + cf_15) * ff[14]
    shift_value += (-6 * cf_1 + 6 * cf_2 + 6 * cf_3 - 6 * cf_4 - 4 * cf_5 - 2 * cf_6 + 4 * cf_7 + 2 * cf_8 -
                    3 * cf_9 + 3 * cf_10 - 3 * cf_11 + 3 * cf_12 - 2 * cf_13 - cf_14 - 2 * cf_15 - cf_16) * ff[15]
    shift_value += (4 * cf_1 - 4 * cf_2 - 4 * cf_3 + 4 * cf_4 + 2 * cf_5 + 2 * cf_6 - 2 * cf_7 - 2 * cf_8 +
                    2 * cf_9 - 2 * cf_10 + 2 * cf_11 - 2 * cf_12 + cf_13 + cf_14 + cf_15 + cf_16) * ff[16]

    return shift_value

# Numba JIT function to compute 4 parameter Helmert transformation (2D)

def _helmert_2d(east, north, tE, tN, dm, Rz):
    """
    Compute 4 parameter Helmert transformation (2D). Do not call directly.
    """
    m = 1 + dm * 1e-6
    # {Conversion '' to radians}
    rz = math.radians(Rz/3600)
    eastt = east * m * math.cos(rz) - north * m * math.sin(rz) + tE
    northt = north * m * math.cos(rz) + east * m * math.sin(rz) + tN

    return eastt, northt

# Numba JIT function to compute 7 parameter Helmert transformation (3D)    

def _helmert_7(x, y, z, cx, cy, cz, scale, rx, ry, rz):
    """
    Compute 7 parameter Helmert transformation (3D). Do not call directly.
    """
    x1 = cx + scale * (x + rz * y - ry * z)
    y1 = cy + scale * (-rz * x + y + rx * z)
    z1 = cz + scale * (ry * x - rx * y + z)

    return x1, y1, z1


def _etrs_to_st70(lat, lon, z, E0, N0, PHI0, LAMBDA0, k0, a, b, tE, tN, dm, Rz, shifts_grid, mine, minn, stepe, stepn, heights_grid, minla, minphi, stepla, stepphi):
    en = projections._geodetic_to_stereographic(lat, lon, E0, N0, PHI0, LAMBDA0, k0, a, b,)
    h = transformations._helmert_2d(en[0], en[1], tE, tN, dm, Rz)

    e_shift = transformations._doBSInterpolation(h[0], h[1], mine, minn, stepe, stepn, shifts_grid[0])
    n_shift = transformations._doBSInterpolation(h[0], h[1], mine, minn, stepe, stepn, shifts_grid[1])
    h_shift = transformations._doBSInterpolation(lon, lat, minla, minphi, stepla, stepphi, heights_grid[0])

    return  h[0] + e_shift, h[1] + n_shift, z - h_shift


def _etrs_to_st70_en(e, n, height, E0, N0, PHI0, LAMBDA0, k0, a, b, tE, tN, dm, Rz, shifts_grid, mine, minn, stepe, stepn, heights_grid, minla, minphi, stepla, stepphi):
    latlon = projections._stereographic_to_geodetic(e, n, E0, N0, PHI0, LAMBDA0, k0, a, b)
    h = transformations._helmert_2d(e, n, tE, tN, dm, Rz)

    e_shift = transformations._doBSInterpolation(h[0], h[1], mine, minn, stepe, stepn, shifts_grid[0])
    n_shift = transformations._doBSInterpolation(h[0], h[1], mine, minn, stepe, stepn, shifts_grid[1])
    h_shift = transformations._doBSInterpolation(latlon[1], latlon[0], minla, minphi, stepla, stepphi, heights_grid[0])

    return latlon[0], latlon[1], height + h_shift, h[1] + n_shift, h[0] + e_shift, e_shift, n_shift


def _st70_to_etrs(e, n, height, E0, N0, PHI0, LAMBDA0, k0, a, b, tE, tN, dm, Rz, shifts_grid, mine, minn, stepe, stepn, heights_grid, minla, minphi, stepla, stepphi):

    e_shift = transformations._doBSInterpolation(e, n, mine, minn, stepe, stepn, shifts_grid[0])
    n_shift = transformations._doBSInterpolation(e, n, mine, minn, stepe, stepn, shifts_grid[1])

    h = transformations._helmert_2d(e - e_shift, n - n_shift, tE, tN, dm, Rz)

    latlon = projections._stereographic_to_geodetic(h[0], h[1], E0, N0, PHI0, LAMBDA0, k0, a, b)

    h_shift = transformations._doBSInterpolation(latlon[1], latlon[0], minla, minphi, stepla, stepphi, heights_grid[0])

    return  latlon[0], latlon[1], height + h_shift


def _st70_to_utm(e, n, height, E0, N0, PHI0, LAMBDA0, k0, a, b, tE, tN, dm, Rz, shifts_grid, mine, minn, stepe, stepn, heights_grid, minla, minphi, stepla, stepphi, zone):
    lat, lon, height = transformations._st70_to_etrs(e, n, height, E0, N0, PHI0, LAMBDA0, k0, a, b, tE, tN, dm, Rz, shifts_grid, mine, minn, stepe, stepn, heights_grid, minla, minphi, stepla, stepphi)

    utm = projections._tm_latlon2en(lat, lon, 500000.0, 0.0, 0.0, math.radians(zone * 6.0 - 183.0), 0.9996, a, b)

    return utm[0], utm[1], height

class Transform:

    def __init__(self, filename=None):    # intialise constants

        if filename is None:
            filename = sorted(glob.glob(os.path.join(os.path.dirname(__file__), 'data', 'rom_grid3d_*.spg')))[-1]

        with open(filename, 'rb') as f:
            grid_data = pickle.load(f)

        self.params = grid_data['params']
        self.grid_version = grid_data['params']['version']

        self.grid = {}
        self.grid['name'] = grid_data['grids']['geodetic_shifts']['name']
        self.grid['source'] = grid_data['grids']['geodetic_shifts']['source']
        self.grid['target'] = grid_data['grids']['geodetic_shifts']['target']

        self.geoid = {}
        self.geoid['name'] = grid_data['grids']['geoid_heights']['name']
        self.geoid['source'] = grid_data['grids']['geoid_heights']['source']
        self.geoid['target'] = grid_data['grids']['geoid_heights']['target']

        self.grid_shifts = grid_data['grids']['geodetic_shifts']
        self.geoid_heights = grid_data['grids']['geoid_heights']
        self.load_grids(grid_data)

        self.helmert = {}

        self.source = grid_data['grids']['geodetic_shifts']['source']
        self.source_epsg = 4258

        if 'krasov' in self.grid['name']:
            self.dest = 'st70'
            self.dest_epsg = 3844
        else:
            raise NotImplementedError(f'Target CRS {self.grid["target"]} unsupported')

        self.helmert['etrs2stereo'] = grid_data['params']['helmert']['os_' + self.dest]
        self.helmert['stereo2etrs'] = grid_data['params']['helmert'][self.dest + '_os']

        self.crs = crs.crs(self.dest_epsg, self.source_epsg)
        self.projection = self.crs.projection

        self.set_ellipsoid_param()

    def load_grids(self, grid_data):
        self.gpu = False

    def set_ellipsoid_param(self):

        self.a = float(self.crs.projection['a'])
        self.b = float(self.crs.projection['b'])
        self.f = float(self.crs.projection['f'])
        self.k0 = float(self.crs.projection['k'])

        for axis in self.crs.axes:
            axis_direction = axis.abbrev[0].lower()

            if axis_direction in ('x', 'y'):

                if axis.name[0].lower() == 'e':
                    self.E0 = float(self.crs.projection[f'{axis_direction}_0'])
                elif axis.name[0].lower() == 'n':
                    self.N0 = float(self.crs.projection[f'{axis_direction}_0'])

        self.PHI0 = math.radians(self.crs.projection['lat_0'])
        self.LAMBDA0 = math.radians(self.crs.projection['lon_0'])

    def helmert_2d(self, east, north, transform='etrs2stereo'):
        return _helmert_2d(east, north, **self.helmert[transform])

    @staticmethod
    def _bulk_etrs_to_st70(lat, lon, z, e, n, height,
                        E0, N0, PHI0, LAMBDA0, k0, a, b,
                        tE, tN, dm, Rz,
                        shifts_grid, mine, minn, stepe, stepn,
                        heights_grid, minla, minphi, stepla, stepphi):

        lat = np.asarray(lat, dtype=np.float64)
        lon = np.asarray(lon, dtype=np.float64)
        z = np.asarray(z, dtype=np.float64)
        e = np.asarray(e, dtype=np.float64)
        n = np.asarray(n, dtype=np.float64)
        height = np.asarray(height, dtype=np.float64)
        shifts_grid = np.asarray(shifts_grid, dtype=np.float64)
        heights_grid = np.asarray(heights_grid, dtype=np.float64)

        for i in range(e.shape[0]):
            e[i], n[i], height[i] = transformations._etrs_to_st70(
                lat[i], lon[i], z[i],
                E0, N0, PHI0, LAMBDA0, k0, a, b,
                tE, tN, dm, Rz,
                shifts_grid, mine, minn, stepe, stepn,
                heights_grid, minla, minphi, stepla, stepphi
            )

    @staticmethod
    def _bulk_st70_to_etrs(e, n, height, lat, lon, z,
                        E0, N0, PHI0, LAMBDA0, k0, a, b,
                        tE, tN, dm, Rz,
                        shifts_grid, mine, minn, stepe, stepn,
                        heights_grid, minla, minphi, stepla, stepphi):

        e = np.asarray(e, dtype=np.float64)
        n = np.asarray(n, dtype=np.float64)
        height = np.asarray(height, dtype=np.float64)
        lat = np.asarray(lat, dtype=np.float64)
        lon = np.asarray(lon, dtype=np.float64)
        z = np.asarray(z, dtype=np.float64)
        shifts_grid = np.asarray(shifts_grid, dtype=np.float64)
        heights_grid = np.asarray(heights_grid, dtype=np.float64)

        for i in range(e.shape[0]):
            lat[i], lon[i], z[i] = transformations._st70_to_etrs(
                e[i], n[i], height[i],
                E0, N0, PHI0, LAMBDA0, k0, a, b,
                tE, tN, dm, Rz,
                shifts_grid, mine, minn, stepe, stepn,
                heights_grid, minla, minphi, stepla, stepphi
            )

    @staticmethod
    def _bulk_st70_to_utm(e, n, height, utm_e, utm_n, z,
                        E0, N0, PHI0, LAMBDA0, k0, a, b,
                        tE, tN, dm, Rz,
                        shifts_grid, mine, minn, stepe, stepn,
                        heights_grid, minla, minphi, stepla, stepphi,
                        zone):

        e = np.asarray(e, dtype=np.float64)
        n = np.asarray(n, dtype=np.float64)
        height = np.asarray(height, dtype=np.float64)
        utm_e = np.asarray(utm_e, dtype=np.float64)
        utm_n = np.asarray(utm_n, dtype=np.float64)
        z = np.asarray(z, dtype=np.float64)
        shifts_grid = np.asarray(shifts_grid, dtype=np.float64)
        heights_grid = np.asarray(heights_grid, dtype=np.float64)

        for i in range(e.shape[0]):
            utm_e[i], utm_n[i], z[i] = transformations._st70_to_utm(
                e[i], n[i], height[i],
                E0, N0, PHI0, LAMBDA0, k0, a, b,
                tE, tN, dm, Rz,
                shifts_grid, mine, minn, stepe, stepn,
                heights_grid, minla, minphi, stepla, stepphi,
                zone
            )


    def etrs_to_st70(self, lat, lon, z, e, n, height):
        self._bulk_etrs_to_st70(
            np.asarray(lat, dtype=np.float64),
            np.asarray(lon, dtype=np.float64),
            np.asarray(z, dtype=np.float64),
            np.asarray(e, dtype=np.float64),
            np.asarray(n, dtype=np.float64),
            np.asarray(height, dtype=np.float64),
            np.float64(self.E0), np.float64(self.N0),
            np.float64(self.PHI0), np.float64(self.LAMBDA0),
            np.float64(self.k0), np.float64(self.a), np.float64(self.b),
            np.float64(self.helmert['etrs2stereo']['tE']),
            np.float64(self.helmert['etrs2stereo']['tN']),
            np.float64(self.helmert['etrs2stereo']['dm']),
            np.float64(self.helmert['etrs2stereo']['Rz']),
            np.asarray(self.grid_shifts['grid'], dtype=np.float64),
            np.float64(self.grid_shifts['metadata']['mine']),
            np.float64(self.grid_shifts['metadata']['minn']),
            np.float64(self.grid_shifts['metadata']['stepe']),
            np.float64(self.grid_shifts['metadata']['stepn']),
            np.asarray(self.geoid_heights['grid'], dtype=np.float64),
            np.float64(self.geoid_heights['metadata']['minla']),
            np.float64(self.geoid_heights['metadata']['minphi']),
            np.float64(self.geoid_heights['metadata']['stepla']),
            np.float64(self.geoid_heights['metadata']['stepphi'])
        )

    def st70_to_etrs(self, e, n, height, lat, lon, z):
        self._bulk_st70_to_etrs(
            np.asarray(e, dtype=np.float64),
            np.asarray(n, dtype=np.float64),
            np.asarray(height, dtype=np.float64),
            np.asarray(lat, dtype=np.float64),
            np.asarray(lon, dtype=np.float64),
            np.asarray(z, dtype=np.float64),
            np.float64(self.E0), np.float64(self.N0),
            np.float64(self.PHI0), np.float64(self.LAMBDA0),
            np.float64(self.k0), np.float64(self.a), np.float64(self.b),
            np.float64(self.helmert['stereo2etrs']['tE']),
            np.float64(self.helmert['stereo2etrs']['tN']),
            np.float64(self.helmert['stereo2etrs']['dm']),
            np.float64(self.helmert['stereo2etrs']['Rz']),
            np.asarray(self.grid_shifts['grid'], dtype=np.float64),
            np.float64(self.grid_shifts['metadata']['mine']),
            np.float64(self.grid_shifts['metadata']['minn']),
            np.float64(self.grid_shifts['metadata']['stepe']),
            np.float64(self.grid_shifts['metadata']['stepn']),
            np.asarray(self.geoid_heights['grid'], dtype=np.float64),
            np.float64(self.geoid_heights['metadata']['minla']),
            np.float64(self.geoid_heights['metadata']['minphi']),
            np.float64(self.geoid_heights['metadata']['stepla']),
            np.float64(self.geoid_heights['metadata']['stepphi'])
        )

    def st70_to_utm(self, e, n, height, utm_e, utm_n, z, zone):
        self._bulk_st70_to_utm(
            np.asarray(e, dtype=np.float64),
            np.asarray(n, dtype=np.float64),
            np.asarray(height, dtype=np.float64),
            np.asarray(utm_e, dtype=np.float64),
            np.asarray(utm_n, dtype=np.float64),
            np.asarray(z, dtype=np.float64),
            np.float64(self.E0), np.float64(self.N0),
            np.float64(self.PHI0), np.float64(self.LAMBDA0),
            np.float64(self.k0), np.float64(self.a), np.float64(self.b),
            np.float64(self.helmert['stereo2etrs']['tE']),
            np.float64(self.helmert['stereo2etrs']['tN']),
            np.float64(self.helmert['stereo2etrs']['dm']),
            np.float64(self.helmert['stereo2etrs']['Rz']),
            np.asarray(self.grid_shifts['grid'], dtype=np.float64),
            np.float64(self.grid_shifts['metadata']['mine']),
            np.float64(self.grid_shifts['metadata']['minn']),
            np.float64(self.grid_shifts['metadata']['stepe']),
            np.float64(self.grid_shifts['metadata']['stepn']),
            np.asarray(self.geoid_heights['grid'], dtype=np.float64),
            np.float64(self.geoid_heights['metadata']['minla']),
            np.float64(self.geoid_heights['metadata']['minphi']),
            np.float64(self.geoid_heights['metadata']['stepla']),
            np.float64(self.geoid_heights['metadata']['stepphi']),
            int(zone)
        )


if __name__ == "__main__":
    pass