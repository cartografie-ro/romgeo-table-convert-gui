from typing import Literal
import re
import pandas as pd
import numpy as np
import logging

# LATEST

PREGEX_DMS   = r"([NEne]?)(\d+)(\D+)(\d+)(\D+)([\d.]+)(\D)*"
PREGEX_DMS4a = r"((?P<name>([\w\-\_\s\S])*)(?P<s0>[\s,;\t]))*(?P<lat>([NEne]?)(?P<lat_d>[4][345678]+)(\D+)(?P<lat_m>\d+)(\D+)(?P<lat_s>[\d]{2}([.][\d]+)*)(\D)*)(?P<s1>[\s,;\t])(?P<lon>([NEne]?)(?P<lon_d>[23][\d]+)(\D+)(?P<lon_m>\d+)(\D+)(?P<lon_s>[\d]{2}([.][\d]+)*)(\D)*)(?P<s2>[\s,;\t])(?P<height>[\d.]+)"
# v1 PREGEX_DMS4  = r"((?P<name>([\w\-\S])*)(?P<s0>[\s,;\t])*)(?P<lat>(([NEne]?)(?P<lat_d>[4][345678]+)(\D+)(?P<lat_m>\d+)(\D+)(?P<lat_s>[\d]{2}([.][\d]+)*)|(?P<lat_dd>[4][345678]\.[\d]*))(\D)*)(?P<s1>[\s,;\t])(?P<lon>(([NEne]?)(?P<lon_d>[23][\d]+)(\D+)(?P<lon_m>\d+)(\D+)(?P<lon_s>[\d]{2}([.][\d]+)*)|(?P<lon_dd>[23][\d]\.[\d]*))(\D)*)(?P<s2>[\s,;\t])(?P<height>[\d.]+)"
# v2 PREGEX_DMS4  = r"((?P<name>([\w\-\_\s\S])*)(?P<s0>[\s,;\t]))*(?P<lat>(([NEne]?)(?P<lat_d>[4][345678]+)(\D+)(?P<lat_m>\d+)(\D+)(?P<lat_s>[\d]{2}([.][\d]+)*)|(?P<lat_dd>[4][345678]\.[\d]*))(\D)*)(?P<s1>[\s,;\t])(?P<lon>(([NEne]?)(?P<lon_d>[23][\d]+)(\D+)(?P<lon_m>\d+)(\D+)(?P<lon_s>[\d]{2}([.][\d]+)*)|(?P<lon_dd>[23][\d]\.[\d]*))(\D)*)(?P<s2>[\s,;\t])(?P<height>[\d.]+)"
PREGEX_DMS4  = r"((?P<name>([\w\-\_\s\S])*)(?P<s0>[\s,;\t]))*(?P<lat>(([NEne]?)(?P<lat_d>[4][345678]+)(\D+)(?P<lat_m>\d+)(\D+)(?P<lat_s>[\d]{1,2}([.][\d]+)*)|(?P<lat_dd>[4][345678]\.[\d]*))(\D)*)(?P<s1>[\s,;\t])(?P<lon>(([NEne]?)(?P<lon_d>[23][\d]+)(\D+)(?P<lon_m>\d+)(\D+)(?P<lon_s>[\d]{1,2}([.][\d]+)*)|(?P<lon_dd>[23][\d]\.[\d]*))(\D)*)(?P<s2>[\s,;\t])(?P<height>[\d.]+)"

BBOX_RO_ST70 = [116424.61, 215561.44, 1018946.51, 771863.53] 
BBOX_RO_ETRS = [    20.26,     43.44,      31.41,     48.27]

def is_DMS(val):
        return False

def is_DMS3(val):
        return False

def is_inside_bounds(a:float, b:float, type:str = "etrs")->bool:
    """
    Determines whether the given coordinates (a, b) are within the bounds 
    of the specified coordinate system type.

    Parameters:
    a (float): The latitude or x-coordinate to check.
    b (float): The longitude or y-coordinate to check.
    type (str): The coordinate system type to use for bounds checking. 
                Default is "etrs". Other valid value is "st70".

    Returns:
    bool: True if the coordinates are within the bounds of the specified 
          coordinate system type, False otherwise.
    """
    if type == "etrs":
        BBOX = BBOX_RO_ETRS
    elif type == "st70":
        BBOX = BBOX_RO_ST70
    
    return (BBOX[1] <= a <= BBOX[3]) and (BBOX[0] <= b <= BBOX[2])

def dd_or_dms(x):
    """Converts parameter to decimal dgrees

    Args:
        x (string, float, whatever): value to be converted

    Raises:
        Exception: "Bad Value" conversion cannot be done

    Returns:
        float: Decimal degrees
    """
    import re
    try:
        return float(x)
    except:
        try:
            x = re.search(PREGEX_DMS,x).groups()
            return float(x[1]) + float(x[3])/60 + float(x[5])/3600
        except:
            return np.nan
            #raise Exception("Bad Value") 

def dd4_or_dms4(x) -> tuple[float, float, float, str]:
    """Converts parameter to decimal dgrees
    Args:
        x (string, float, whatever): value to be converted
    Raises:
        Exception: "Bad Value" conversion cannot be done
    Returns:
        float: Decimal degrees
    """
    import re
    try:
        x = re.search(PREGEX_DMS4,x).groupdict()

        if None != x['name']:
            pointName = x['name']
        else:
            pointName = ''

        if None not in [ x['lat_d'], x['lat_m'], x['lat_s'] ]:
            la = float(x['lat_d'] ) + float(x['lat_m']) /60 + float(x['lat_s']) /3600
        elif ['lat_dd'] != None:
            la = float(x['lat_dd'])
        else:
            la = np.nan

        if None not in [ x['lon_d'],x['lon_m'], x['lon_s'] ]:
            lo = float(x['lon_d'] ) + float(x['lon_m']) /60 + float(x['lon_s']) /3600
        elif ['lon_dd'] != None:
            lo = float(x['lon_dd'])
        else:
            lo = np.nan

        if ['height'] != None:
            he = float(x['height'])
        else:
            he = np.nan
        
        return la, lo, he, pointName
    except:
        #print(f"Bad value {x}")
        return np.nan, np.nan, np.nan, pointName
        #raise Exception("Bad Value") 

def val_to_float(x):
    """Converts parameter to decimal dgrees

    Args:
        x (string, float, whatever): value to be converted

    Raises:
        Exception: "Bad Value" conversion cannot be done

    Returns:
        float: Decimal degrees
    """
    try:
        return float(x)
    except:
        return np.nan

def islat(v) -> bool:
    v = dd_or_dms(v)
    if v:
        return (BBOX_RO_ETRS[1] <= v <= BBOX_RO_ETRS[3])
    else:
        return False

def islon(v) -> bool:
    v = dd_or_dms(v)
    if v:
        return (BBOX_RO_ETRS[0] <= v <= BBOX_RO_ETRS[2])
    else:
        return False

def is_float(element: any) -> bool:
    #If you expect None to be passed:
    if element is None: 
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False

def dd2dms(dd:float, format:str="tuple"):
    """Converts Decimal degrees to DD*MM'SS.ss", or to tuple (d,m,s) format

    Args:
        dd (float): Value to be converted
        format (str, optional): format type to convert to. Defaults to "tuple".

    Returns:
        string or tuple (d,m,s)
    """

    is_positive = dd >= 0
    dd = abs(dd)
    m,s = divmod(dd*3600,60)
    d,m = divmod(m,60)
    d = d if is_positive else -d
    if 'tuple' == format :
        return (d,m,s) 
    else:
        return f"{d:.0f}\N{DEGREE SIGN}{m:.0f}\N{Apostrophe}{s:.5f}\N{Quotation mark}"