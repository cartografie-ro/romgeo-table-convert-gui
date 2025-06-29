#!/usr/bin/env python
# coding: utf-8
# RomGEO Python Library
# projections module - Perform CRS projections

import numpy as np
import math

from romgeo_lite import crs
from romgeo_lite import projections

# Numba JIT function to compute geocentric primary curve radius

def _primary_curve_radius(phi, a, b):
    """
    Compute primary curve radius for geocentric coordinate projection. Do not call directly.
    References: Heikkinen (1982), Hofmann-Wellenhof & Lichtenegger (1997)    
    """
    e_sqr = (a**2 - b**2) / a**2
    return a / math.sqrt(1 - e_sqr * (math.sin(phi)**2))
    
# Numba JIT function to compute coordinate projection from spherical to cartesian.

def _geodetic_to_geocentric(lat, lon, h, a, b):
    """
    Compute geocentric coordinate geocentric projection from spherical to cartesian. Do not call directly.
    References: Heikkinen (1982), Hofmann-Wellenhof & Lichtenegger (1997)    
    """
    phi = math.radians(lat)
    lda = math.radians(lon)
    X = (_primary_curve_radius(phi, a, b) + h) * math.cos(phi) * math.cos(lda)
    Y = (_primary_curve_radius(phi, a, b) + h) * math.cos(phi) * math.sin(lda)
    Z = (b**2 / a**2 * _primary_curve_radius(phi, a, b) + h) * math.sin(phi)
    return X, Y, Z

# Numba JIT function to compute geocentric coordinate projection from cartesian to spherical using Ferrari's solution.

def _geocentric_to_geodetic(x, y, z, a, b):
    """
    Compute geocentric coordinate projection from cartesian to spherical using Ferrari's solution. Do not call directly.
    References: Heikkinen (1982), Hofmann-Wellenhof & Lichtenegger (1997)
    """
    e_sqr = (a**2 - b**2) / a**2
    e1_sqr = (a**2 - b**2) / b**2
    p = math.sqrt(x**2 + y**2)
    F = 54 * b**2 * z **2
    G = p**2 + (1 - e_sqr) * z**2 - e_sqr * (a**2 - b**2)
    c = (e_sqr**2 * F * p**2) / G**3
    s = (1 + c + math.sqrt(c**2 + 2*c))**(1.0/3.0)
    k = s + 1 + (1 / s)
    P = F / (3 * k**2 * G**2)
    Q = math.sqrt(1 + 2 * (e_sqr**2) * P)
    r0 = (-P * e_sqr * p) / (1 + Q) + math.sqrt(1/2 * a**2 * (1 + (1 / Q)) - (P * (1 - e_sqr) * z**2) / (Q * (1 + Q)) - 1 / 2 * P * p**2)
    U = math.sqrt((p - e_sqr * r0)**2 + z**2)
    V = math.sqrt((p - e_sqr * r0)**2 + (1 - e_sqr) * z**2)
    z0 = (b**2 * z) / (a * V)
    h = U * (1 - b**2 / (a * V))
    phi = math.atan((z + e1_sqr * z0) / p)
    lda = math.atan2(y, x)
    return math.degrees(phi), math.degrees(lda), h


def _geodetic_to_stereographic(lat, lon, E0, N0, PHI0, LAMBDA0, k0, a, b):
    fi = math.radians(lat)
    la = math.radians(lon)
    ep = math.sqrt((a**2 - b**2) / a**2)
    w = math.sqrt(1 - ep**2 * math.sin(PHI0)**2)
    raza = (a * (1 - ep**2)) / (w**3)
    raza = math.sqrt(raza * a / w)
    n = math.sqrt(1 + (ep**2 * math.cos(PHI0)**4) / (1 - ep**2))
    s1 = (1 + math.sin(PHI0)) / (1 - math.sin(PHI0))
    s2 = (1 - ep * math.sin(PHI0)) / (1 + ep * math.sin(PHI0))
    w1 = math.exp(n * math.log(s1 * math.exp(ep * math.log(s2))))
    c = ((n + math.sin(PHI0)) * (1 - (w1 - 1) / (w1 + 1))) / ((n - math.sin(PHI0)) * (1 + (w1 - 1) / (w1 + 1)))
    w2 = c * w1
    hi0 = (w2 - 1) / (w2 + 1)
    hi0 = math.atan(hi0 / math.sqrt(1 - hi0**2))
    sa = (1 + math.sin(fi)) / (1 - math.sin(fi))
    sb = (1 - ep * math.sin(fi)) / (1 + ep * math.sin(fi))
    w = c * math.exp(n * math.log(sa * math.exp(ep * math.log(sb))))
    hi = (w - 1) / (w + 1)
    hi = math.atan(hi / math.sqrt(1 - hi**2))
    lam = n * (la - LAMBDA0) + LAMBDA0
    beta = 1 + math.sin(hi) * math.sin(hi0) + math.cos(hi) * math.cos(hi0) * math.cos(lam - LAMBDA0)
    east = 2 * raza * k0 * math.cos(hi) * math.sin(lam - LAMBDA0) / beta
    north = 2 * raza * k0 * (math.cos(hi0) * math.sin(hi) - math.sin(hi0) * math.cos(hi) * math.cos(lam-LAMBDA0)) / beta
    north = north + N0
    east = east + E0

    return east, north


def _stereographic_to_geodetic(east, north, E0, N0, PHI0, LAMBDA0, k0, a, b):
    fi = 0
    la = 0
    ep = math.sqrt((a**2 - b**2) / a**2)
    w = math.sqrt(1 - ep**2 * math.sin(PHI0)**2)
    raza = (a * (1 - ep**2)) / (w**3)
    raza = math.sqrt(raza * a / w)
    n = (ep**2 * math.cos(PHI0)**4) / (1 - ep**2)
    n = math.sqrt(1 + n)
    s1 = (1 + math.sin(PHI0)) / (1 - math.sin(PHI0))
    s2 = (1 - ep * math.sin(PHI0)) / (1 + ep * math.sin(PHI0))
    w1 = math.exp(n * math.log(s1 * math.exp(ep * math.log(s2))))
    c = ((n + math.sin(PHI0)) * (1 - (w1 - 1) / (w1 + 1))) / ((n - math.sin(PHI0)) * (1 + (w1 - 1) / (w1 + 1)))
    w2 = c * w1
    hi0 = (w2 - 1) / (w2 + 1)
    hi0 = math.atan(hi0 / math.sqrt(1 - hi0**2))
    g = 2 * raza * k0 * math.tan(math.pi / 4 - hi0 / 2)
    h = 4 * raza * k0 * math.tan(hi0) + g
    ii = math.atan((east - E0) / (h + (north - N0)))
    j = math.atan((east - E0) / (g - (north - N0))) - ii
    lam = j + 2 * ii + LAMBDA0
    la = LAMBDA0 + (lam - LAMBDA0) / n
    hi = hi0 +2 * math.atan((north - N0 - (east - E0) * math.tan(j / 2)) / (2 * raza * k0))
    North = north
    East = east
    fn = N0
    fe = E0
    csi = (0.5 * math.log((1 + math.sin(hi)) / (c * (1 - math.sin(hi))))) / n
    fi = 2 * math.atan(math.exp(csi)) - math.pi / 2
    i = 0
    tol = 1e-9
    dif = 100
    max_iter = 100

    while ((dif > tol) and (i < max_iter)):
        i = i + 1
        fic = fi
        csii = math.log(math.tan(fi / 2 + math.pi / 4) * math.exp((ep / 2) *
               math.log((1 - ep * math.sin(fi)) / (1 + ep * math.sin(fi)))))
        fi = fi - (csii - csi) * math.cos(fi) * (1 - ep**2 * math.sin(fi)**2) / (1-ep**2)
        dif = abs(math.degrees(fi) - math.degrees(fic)) * 3600

    return math.degrees(fi), math.degrees(la)
    
# Numba JIT function to compute meridional arc

def _tm_meridarc(bF0, n, PHI0, phi):
    """ Compute TM meridional arc. Do not call directly.
    """
    m1 = (1.0 + n + ((5.0 / 4.0) * (pow(n,2))) + ((5.0 / 4.0) * (pow(n,3)))) * (phi - PHI0)
    m2 = ((3.0 * n) + (3.0 * (pow(n,2))) + ((21.0 / 8.0) * (pow(n,3)))) * (math.sin(phi - PHI0)) * (math.cos(phi + PHI0))
    m3 = (((15.0 / 8.0) * (pow(n,2))) + ((15.0 / 8.0) * (pow(n,3)))) * (math.sin(2 * (phi - PHI0))) * (math.cos(2 * (phi + PHI0)))
    m4 = ((35.0 / 24.0) * (pow(n,3))) * (math.sin(3 * (phi - PHI0))) * (math.cos(3 * (phi + PHI0)))
    m = bF0 * (m1 - m2 + m3 - m4)
    return m
    
# Numba JIT function to project E/N coordindates to Latitude and longitude coordinates using given projection parameters for Tranverse Mercator coordinates

def _tm_en2latlon(E ,N, E0, N0, PHI0, LAMBDA0, F0, a, b):
    """ Convert Tranverse Mercator easting/northing to Geodetic Lat/Lon. Do not call directly.
    """
    # Calculate constants
    aF0 = a * F0
    bF0 = b * F0
    e_sqr = (a**2 - b**2) / a**2
    n = (a - b) / (a + b) 
    # Compute initial value of phi1
    phi1 = (float(N - N0) / aF0) + PHI0
    # Compute intitial separation in metres
    m = _tm_meridarc(bF0, n, PHI0, phi1)
    phi2 = (float(N - N0 - m) / aF0) + phi1
    # Iterate until separation is less than 0.01 mm
    while (abs(float(N) - N0 - m) > 0.00001):
        phi2 = (float(N - N0 - m) / aF0) + phi1
        # file.write("next phi = %14.10E\n" % phi2)
        m = projections._tm_meridarc(bF0, n, PHI0, phi2)
        phi1 = phi2
    nu = a * F0 * pow(1 - (e_sqr * pow(math.sin(phi2),2)),-0.5)
    rho = a * F0 * (1 - e_sqr) * pow(1 - (e_sqr * pow(math.sin(phi2),2)),-1.5)
    eta_sqr = (nu / rho) - 1
    tanphi = math.tan(phi2)
    secphi = 1 / math.cos(phi2)
    VII = tanphi / (2 * rho * nu)
    VIII = (tanphi / (24 * rho * pow(nu,3))) * (5 + ((3 * pow(tanphi,2)) + eta_sqr - (9 * pow(tanphi,2) * eta_sqr)))
    IX = (tanphi / (720 * rho * pow(nu,5))) * (61 + ((90 * pow(tanphi,2)) + (45 * pow(tanphi,4))))
    X = secphi / nu
    XI = (secphi / (6 * pow(nu,3))) * ((nu / rho) + (2 * pow(tanphi,2)))
    XII = (secphi / (120 * pow(nu,5))) * (5 + (28 * pow(tanphi,2)) + (24 * pow(tanphi,4)))
    XIIA = (secphi / (5040 * pow(nu,7))) * (61 + (662 * pow(tanphi,2)) + (1320 * pow(tanphi,4)) + (720 * pow(tanphi,6)))
    LAT = math.degrees(phi2 - (VII * pow(E - E0,2)) + (VIII * pow(E - E0,4)) - (IX * pow(E - E0,6)))
    LON = math.degrees(LAMBDA0 + (X * (E - E0)) - (XI * pow(E - E0,3)) + (XII * pow(E - E0,5)) - (XIIA * pow(E - E0,7)))

    return LAT, LON

# Numba JIT function to project Latitude and longitude coordindates to E/N coordindates using given projection parameters for Tranverse Mercator coordinates

def _tm_latlon2en(LAT, LON, E0, N0, PHI0, LAMBDA0, F0, a, b):
    """ Convert Geodetic Lat/Lon to Tranverse Mercator easting/northing. Do not call directly.
    """
    # Calculate constants
    aF0 = a * F0
    bF0 = b * F0
    e_sqr = (a**2 - b**2) / a**2
    n = (a - b) / (a + b) 
    lambda1 = math.radians(LON)
    phi1 = math.radians(LAT)
    nu = a * F0 * pow(1 - (e_sqr * pow(math.sin(phi1),2)),-0.5)
    rho = a * F0 * (1 - e_sqr) * pow(1 - (e_sqr * pow(math.sin(phi1),2)),-1.5)
    eta_sqr = (nu / rho) - 1
    m = projections._tm_meridarc(bF0, n, PHI0, phi1)
    I = m + N0
    II = (nu / 2.0) * math.sin(phi1) * math.cos(phi1)
    III = (nu / 24.0) * (math.sin(phi1) * pow(math.cos(phi1),3)) * (5 - pow(math.tan(phi1),2) + (9 * eta_sqr))
    IIIA = (nu / 720.0) * math.sin(phi1) * pow(math.cos(phi1),5) * (61 - (58 * pow(math.tan(phi1),2)) + pow(math.tan(phi1),4))
    IV = nu * math.cos(phi1)
    V = (nu / 6) * pow(math.cos(phi1),3) * ((nu / rho) - pow(math.tan(phi1),2))
    VI = (nu / 120) * pow(math.cos(phi1),5) * (5 - (18 * pow(math.tan(phi1),2)) + pow(math.tan(phi1),4) + (14 * eta_sqr) - (58 * pow(math.tan(phi1),2)*eta_sqr))
    lambda2 = lambda1 - LAMBDA0
    N = I + (II * pow(lambda2,2)) + (III * pow(lambda2,4)) + (IIIA * pow(lambda2,6))
    E = E0 + (IV * lambda2) + (V * pow(lambda2,3)) + (VI * pow(lambda2,5))

    return E, N

class geocentric:

    def __init__(self, crs_code, ellipsoid_code=None):    # intialise constants

        self.crs = crs.crs(crs_code, ellipsoid_code)
        self.projection = self.crs.projection
        self.a = self.crs.projection['a']
        self.b = self.crs.projection['b']
        self.f = self.crs.projection['f']

    @staticmethod

    def _bulk_geodetic_to_geocentric(lat, lon, h, x, y, z, a, b):
        for i in range(lat.shape[0]):
            x[i], y[i], z[i] = projections._geodetic_to_geocentric(lat[i], lon[i], h[i], a, b)

    @staticmethod

    def _bulk_geocentric_to_geodetic(x, y, z, lat, lon, h, a, b):
        for i in range(lat.shape[0]):
            lat[i], lon[i], h[i] = projections._geocentric_to_geodetic(x[i], y[i], z[i], a, b)

    def geodetic_to_geocentric(self, lat, lon, h, x, y, z):
        self._bulk_geodetic_to_geocentric(lat, lon, h, x, y, z, self.a, self.b)

    def geocentric_to_geodetic(self, x, y, z, lat, lon, h):
        self._bulk_geocentric_to_geodetic(x, y, z, lat, lon, h, self.a, self.b)

class stereographic:
    """
    Hristow Oblique Stereographic (Romania) coordinate projection class using the EPSG method.
    params
    crs_code: int 
        EPSG code of the CRS to be used in conversion
    ellipsoid_code: int, default crs_code
        (optional) EPSG code of the ellipsoid to be used in conversion if different to CRS default
        
    Parameters
    ----------
    {params}
    
    Attributes
    ----------
    crs_code: int
        EPSG code of the CRS to be used in conversion
    ellipsoid_code: int, default None
        (optional) EPSG code of the ellipsoid to be used in conversion. If not provided (None) then crs_code is used.
    
    Notes
    -----
    Initiates a Hristow Oblique Stereographic (Romania) coordinate projection class for a given CRS.
    """

    def __init__(self, crs_code, ellipsoid_code=None):    # intialise constants

        self.crs = crs.crs(crs_code, ellipsoid_code)
        self.projection = self.crs.projection
        
        self._set_ellipsoid_param()
        
    def _set_ellipsoid_param(self):
        """ Set ellipsoid parameters. Do not call directly.
        """

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
        
    @staticmethod

    def _bulk_geodetic_to_stereographic(lat, lon, e, n, E0, N0, PHI0, LAMBDA0, k0, a, b):
        """ Numba CPU Kernel to perform bulk stereographic projections from ETRS89 to Stereo70. Do not call directly.
        """
        for i in range(lat.shape[0]):
            e[i], n[i] = projections._geodetic_to_stereographic(lat[i], lon[i], E0, N0, PHI0, LAMBDA0, k0, a, b)
            
    @staticmethod
    def _bulk_stereographic_to_geodetic(e, n, lat, lon, E0, N0, PHI0, LAMBDA0, k0, a, b):
        """ Numba CPU Kernel to perform bulk sprojections from Stereo70 to ETRS89. Do not call directly.
        """
        for i in range(e.shape[0]):
            lat[i], lon[i] = projections._stereographic_to_geodetic(e[i], n[i], E0, N0, PHI0, LAMBDA0, k0, a, b)  
        
    def geodetic_to_stereographic(self, lat, lon, e, n):
        self._bulk_geodetic_to_stereographic(lat, lon, e, n, self.E0, self.N0, self.PHI0, self.LAMBDA0, self.k0, self.a, self.b)
        
    def stereographic_to_geodetic(self, e, n, lat, lon):
        self._bulk_stereographic_to_geodetic(e, n, lat, lon, self.E0, self.N0, self.PHI0, self.LAMBDA0, self.k0, self.a, self.b)
        
class mercator:
    """
    Transverse Mercator coordinate projection class using the EPSG method.
    params
    crs_code: int 
        EPSG code of the CRS to be used in conversion
    ellipsoid_code: int, default None
        (optional) EPSG code of the ellipsoid to be used in conversion. If not provided (None) then crs_code is used.
        
    Parameters
    ----------
    {params}
    
    Attributes
    ----------
    crs_code: int
        EPSG code of the CRS to be used in conversion
    ellipsoid_code: int, default crs_code
        EPSG code of the ellipsoid to be used in conversion. Set to crs_code if not provided.
    
    
    Notes
    -----
    Initiates a Transverse Mercator conversions for a given CRS.
    """

    @staticmethod
    
    def bulk_en2latlon(x, y, lat, lon, E0, N0, PHI0, LAMBDA0, F0, a, b, aF0, bF0, e_sqr, n):
        """ Bulk convert TM easting/northing to WGS84 Lat/Lon. Do not call directly.
        """
        for i in range(x.shape[0]):
            lat[i], lon[i] = _tm_en2latlon(x[i], y[i], E0, N0, PHI0, LAMBDA0, F0, a, b, aF0, bF0, e_sqr, n)

    @staticmethod
    
    def bulk_latlon2en(lat, lon, x, y, E0, N0, PHI0, LAMBDA0, F0, a, b, aF0, bF0, e_sqr, n):
        """ Bulk convert WGS84 Lat/Lon to TM easting/northing. Do not call directly.
        """
        for i in range(x.shape[0]):
            x[i], y[i] = _tm_latlon2en(lat[i], lon[i], E0, N0, PHI0, LAMBDA0, F0, a, b, aF0, bF0, e_sqr, n)

    def en2latlon(self, x, y, lat, lon):
        """ Fast parallel CPU conversion of Tranverse Mercator easting/northing coordinates to WGS84 Latitude/Longitude using the EPSG formula.
        params
        east: Source Numpy compatible array of TM Easting Coordinates (float64)
        north: Source Numpy compatible array of TM Northing Coordinate (float64)
        lat: Destination Numpy compatible array of WGS84 latitude coordinates in decimal degrees (float64)
        lon: Destination Numpy compatible array of WGS84 longitude coordinates in decimal degrees (float64)
        
        Parameters
        ----------
        {params}
        
        Returns
        -------
        Nothing.
        
        Notes
        -----
        Requires Numpy compatible arrays supported by the Python array interface.
        """
        self.bulk_en2latlon(x, y, lat, lon,
                         self.projection['E0'],
                         self.projection['N0'],
                         self.projection['PHI0'],
                         self.projection['LAMBDA0'],
                         self.projection['F0'],
                         self.projection['a'],
                         self.projection['b'],
                         self.projection['aF0'],
                         self.projection['bF0'],
                         self.projection['e_sqr'],
                         self.projection['n'])

    def latlon2en(self, lat, lon, x, y):
        """ Fast parallel CPU conversion of WGS84 Latitude/Longitude to Tranverse Mercator easting/northing coordinates using the EPSG formula.
        params
        lat: Destination Numpy compatible array of WGS84 latitude coordinates in decimal degrees (float64)
        lon: Destination Numpy compatible array of WGS84 longitude coordinates in decimal degrees (float64)
        east: Source Numpy compatible array of TM Easting Coordinates (float64)
        north: Source Numpy compatible array of TM Northing Coordinate (float64)
            
        Parameters
        ----------
        {params}
        
        Returns
        -------
        Nothing.
        
        Notes
        -----
        Requires Numpy compatible arrays supported by the Python array interface.
        """
        self.bulk_latlon2en(lat, lon, x, y,
                         self.projection['E0'],
                         self.projection['N0'],
                         self.projection['PHI0'],
                         self.projection['LAMBDA0'],
                         self.projection['F0'],
                         self.projection['a'],
                         self.projection['b'],
                         self.projection['aF0'],
                         self.projection['bF0'],
                         self.projection['e_sqr'],
                         self.projection['n'])

    def __init__(self, crs_code, ellipsoid_code=None):
        self.crs_code = crs_code
        self.ellipsoid_code = ellipsoid_code or crs_code

        # p = spatia.epsg.projection(crs_code, ellipsoid_code)

        # if p.crs['method_name'] != 'TRANSVERSE MERCATOR':
        #     raise NotImplementedError("Unsupported projection method: " + p.crs['method_name'])

        # self.projection = p.projection
        # self.crs_parameters = p.crs
