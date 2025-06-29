#!/usr/bin/env python
# coding: utf-8
# crs class - Get CRS parameters

import pyproj as prj
import warnings
import math

warnings.filterwarnings('ignore')

class crs:
    
    def __init__(self, crs_code, ellipsoid_code=None):    # intialise constants

        if str(crs_code) not in prj.database.get_codes(auth_name='EPSG',pj_type='CRS'):
            raise NotImplementedError(f'CRS code {crs_code} unsupported')
        
        self.crs_code = crs_code
        self.crs = prj.CRS.from_epsg(crs_code)
        self.projection = self.crs.to_dict()
        
        if ellipsoid_code is None:
            self.ellipsoid = self.crs.ellipsoid
            
        elif str(ellipsoid_code) in prj.database.get_codes(auth_name='EPSG',pj_type='ELLIPSOID'):
            self.ellipsoid = prj.crs.Ellipsoid.from_epsg(ellipsoid_code)
            self._update_ellps()
                
        elif str(ellipsoid_code) in prj.database.get_codes(auth_name='EPSG',pj_type='CRS'):
            self.ellipsoid = prj.CRS.from_epsg(ellipsoid_code).ellipsoid
            self._update_ellps()
            
        else:
            raise NotImplementedError(f'Ellipsoid code {ellipsoid_code} unsupported')
            
        self.ellipsoid_code = self.ellipsoid.to_json_dict()['id']['code']
        self.axes = self.crs.axis_info

        self.projection['a'] = self.ellipsoid.semi_major_metre
        self.projection['b'] = self.ellipsoid.semi_minor_metre
        self.projection['f'] = self.ellipsoid.inverse_flattening
        
    def _update_ellps(self):
        ellipsoid_map = prj.list.get_ellps_map()
        
        ellps = None
        
        for e in ellipsoid_map:
            ellipsoid_name = ellipsoid_map[e]['description'].lower()
            
            if '(' in ellipsoid_name:
                ellipsoid_name = ellipsoid_name[:ellipsoid_name.find('(')]

            if ellipsoid_name == self.ellipsoid.name.lower():
                self.projection['ellps'] = e
                return

class ellipsoid:
    
    def __init__(self, crs):    # intialise constants
        
        self.a = crs.projection['a']
        self.b = crs.projection['b']
        self.f = crs.projection['f']
        self.k0 = crs.projection['k']
        
        for axis in crs.axes:
            axis_direction = axis.abbrev[0].lower()
            
            if axis_direction in ('x', 'y'):
                
                if axis.name[0].lower() == 'e':
                    self.E0 = crs.projection[f'{axis_direction}_0']
                elif axis.name[0].lower() == 'n':
                    self.N0 = crs.projection[f'{axis_direction}_0']
                    
        self.PHI0 = math.radians(crs.projection['lat_0'])
        self.LAMBDA0 = math.radians(crs.projection['lon_0'])
