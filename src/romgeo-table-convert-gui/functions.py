import romgeo_lite as romgeo
import numpy as np
import re

import config
from logutil import log_function

import grid_mgmt

def _fmt(val: float, width: int, precision: str) -> str:
    """Formats a floating-point number to a specified width and precision.
    
    Args:
        val (float): The floating-point number to format.
        width (int): The total width of the formatted string.
        precision (str): The precision format (e.g., '.2f' for two decimal places).
    
    Returns:
        str: The formatted string representation of the number, or "NaN" right-justified 
        to the specified width if the input value is NaN.
    """
    return format(val, f"{width}{precision}") if not np.isnan(val) else "NaN".rjust(width)

def _dd2dms(dd:float, format:str="tuple"):
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
        return f"{int(d):02d}\N{DEGREE SIGN}{int(m):02d}\N{Apostrophe}{int(s * 1e5) / 1e5:08.5f}\N{Quotation mark}"

def _parse_line_etrs(x) -> tuple[float, float, float, str, list[str]]:
    """Converts parameter to decimal dgrees.
        Also flips Lat/lon if needed
    Args:
        x (string, float, whatever): value to be converted
    Raises:
        Exception: "Bad Value" conversion cannot be done
    Returns:
        float: Decimal degrees
    """
    import re    

    pointName = ''
    comment = []

    match = re.search(config.PREGEX_DMS4, x)
    if not match:
        # Try flipped version
        match = re.search(config.PREGEX_DMS4_FLIPPED, x)
        if not match:
            return np.nan, np.nan, np.nan, pointName if pointName else 'invalid_format', ['invalid format'] 
        flipped = True
    else:
        flipped = False

    x = match.groupdict()
    pointName = x['name'] if x['name'] else ''

    def parse_coord(dd_key, d_key, m_key, s_key):
        if x.get(d_key) and x.get(m_key) and x.get(s_key):
            return float(x[d_key]) + float(x[m_key]) / 60 + float(x[s_key]) / 3600
        elif x.get(dd_key):
            return float(x[dd_key])
        return np.nan

    lat = parse_coord('lat_dd', 'lat_d', 'lat_m', 'lat_s')
    lon = parse_coord('lon_dd', 'lon_d', 'lon_m', 'lon_s')
    he = float(x['height']) if x['height'] else np.nan



    if flipped:
        lat, lon = lon, lat
        comment.append('flipped lat/lon')

    if not _is_inside_bounds(lat, lon, "etrs"):
        lat, lon, he = np.nan, np.nan, np.nan
        comment.append('out of bounds')

    return lat, lon, he, pointName, comment

def _split_floats_from_text(line: str) -> tuple[float, float, float, str]:
    """
    Extracts a name (optional) followed by exactly three floats from a line using named regex groups.
    Supports any separator: spaces, commas, tabs.

    Returns NaN for float values if not exactly 3 are found.

    Args:
        line (str): Input line with optional name and three float values.

    Returns:
        Tuple[float, float, float, str]: Parsed values.
    """
    # Match pattern: optional name + 3 floats (with flexible separators)
    pattern = re.compile(
        r"""^(?P<name>.*?)
            [,\s\t]*  (?P<val1>[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)
            [,\s\t]+  (?P<val2>[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)
            [,\s\t]+  (?P<val3>[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)
            [,\s\t]*$""",
        re.VERBOSE
    )

    match = pattern.match(line.strip())
    if not match:
        return np.nan, np.nan, np.nan, ""

    try:
        x = float(match.group("val1"))
        y = float(match.group("val2"))
        z = float(match.group("val3"))
        name = match.group("name").strip(" ,\t")
        return x, y, z, name
    except Exception:
        return np.nan, np.nan, np.nan, ""

def _is_inside_bounds(a:float, b:float, type:str = "etrs")->bool:
    """Determines if the given coordinates are within specified bounds.
    
    Args:
        a (float): The x-coordinate to check.
        b (float): The y-coordinate to check.
        type (str, optional): The type of coordinate system to use for bounds. 
            Defaults to "etrs". Can be "etrs" or "st70".
    
    Returns:
        bool: True if the coordinates (a, b) are within the defined bounds, 
        False otherwise.
    """
    if type == "etrs":
        BBOX = config.BBOX_RO_ETRS
    elif type == "st70":
        BBOX = config.BBOX_RO_ST70
    
    return (BBOX[1] <= a <= BBOX[3]) and (BBOX[0] <= b <= BBOX[2])

def _val_to_float(x):
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

def _dd_or_dms(x):
    """Converts a given input into a decimal degree (DD) or degrees, minutes, seconds (DMS) format.
    
    This function attempts to convert the input `x` into a float. If the conversion fails, it tries to parse the input as a DMS string using a regular expression. If successful, it converts the DMS values into decimal degrees. If both conversions fail, it returns NaN.
    
    Args:
        x (str or float): The input value to be converted. It can be a numeric value or a string representing DMS.
    
    Returns:
        float: The decimal degree representation of the input if successful, otherwise NaN.
    """
    import re
    try:
        return float(x)
    except:
        try:
            x = re.search(config.PREGEX_DMS,x).groups()
            return float(x[1]) + float(x[3])/60 + float(x[5])/3600
        except:
            return np.nan
            #raise Exception("Bad Value") 

def _islat(v) -> bool:
    """Determines if a given value is a valid latitude.
    
    This function checks if the provided value falls within the defined 
    latitude bounds specified in the configuration.
    
    Args:
        v: The value to be checked, which can be in decimal degrees or 
           degrees-minutes-seconds format.
    
    Returns:
        bool: True if the value is a valid latitude within the specified 
              bounds, False otherwise.
    """
    v = _dd_or_dms(v)
    if v:
        return (config.BBOX_RO_ETRS[1] <= v <= config.BBOX_RO_ETRS[3])
    else:
        return False

def _islon(v) -> bool:
    """Determines if a given value is a valid longitude within a specified bounding box.
    
    Args:
        v: The value to be checked, which can be in decimal degrees or DMS format.
    
    Returns:
        bool: True if the value is a valid longitude within the bounding box defined by
        config.BBOX_RO_ETRS, False otherwise.
    """
    v = _dd_or_dms(v)
    if v:
        return (config.BBOX_RO_ETRS[0] <= v <= config.BBOX_RO_ETRS[2])
    else:
        return False

def _latlon_maybe_flipped(lat: float, lon: float) -> bool:
    """Determines if the latitude and longitude values may be flipped.
    
    This function checks the validity of the provided latitude and longitude values,
    as well as their flipped counterparts. It returns True if the original values
    are invalid but the flipped values are valid, indicating a potential mix-up.
    
    Args:
        lat (float): The latitude value to check.
        lon (float): The longitude value to check.
    
    Returns:
        bool: True if the latitude and longitude values may be flipped, False otherwise.
    """
    lat_valid = _islat(lat)
    lon_valid = _islon(lon)
    flipped_lat_valid = _islat(lon)
    flipped_lon_valid = _islon(lat)

    return not (lat_valid and lon_valid) and (flipped_lat_valid and flipped_lon_valid)

def _is_ascii_file(filepath: str, max_bytes: int = 4096) -> bool:
    """Determines if a file is likely an ASCII text file.
    
    This function reads a specified number of bytes from the given file and checks for the presence of NULL bytes and the ratio of non-text bytes to total bytes. If the file contains a NULL byte or if more than 30% of the bytes are non-text, it is considered a binary file.
    
    Args:
        filepath (str): The path to the file to be checked.
        max_bytes (int, optional): The maximum number of bytes to read from the file. Defaults to 4096.
    
    Returns:
        bool: True if the file is likely an ASCII text file, False otherwise.
    """
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(max_bytes)
            if b'\0' in chunk:
                return False  # contains NULL byte → binary

            # Count non-printable characters (allow tab, newline, carriage return)
            nontext = sum(1 for b in chunk if b < 9 or (13 < b < 32) or b > 126)
            ratio = nontext / len(chunk) if chunk else 1

            return ratio < 0.30  # heuristic: <30% non-text = likely text
    except Exception:
        return False







@log_function(level='debug')
def convert_etrs_st70(multiText: list[str]) -> list[tuple[str, float, float, float, float, float, float]]:
    """Converts coordinates from ETRS89 to the ST70 system.
    
    Args:
        multiText (list[str]): A list of strings, each containing coordinates in ETRS89 format.
    
    Returns:
        list[tuple[str, float, float, float, float, float, float]]: A list of tuples, where each tuple contains:
            - name (str): The name associated with the coordinates.
            - n (float): The northing coordinate in ETRS89.
            - e (float): The easting coordinate in ETRS89.
            - h (float): The height coordinate in ETRS89.
            - st_x (float): The converted easting coordinate in ST70.
            - st_y (float): The converted northing coordinate in ST70.
            - st_h (float): The converted height coordinate in ST70.
            
    If the input coordinates cannot be parsed or converted, NaN values will be returned for those fields.
    """
    results = []
    # Preallocate transformer
    t = romgeo.transformations.Transform(grid_mgmt.ROMGEO_GRID_FILE)

    for line in multiText:
        name = ""
        try:
            n, e, h, name, comment = _parse_line_etrs(line)
        except Exception:
            n = e = h = np.nan

        if not np.isnan(n) and not np.isnan(e) and not np.isnan(h):
            st_y = st_x = st_h = np.nan
            try:
                # Prepare 1-element arrays
                n_arr = np.array([n], dtype=float)
                e_arr = np.array([e], dtype=float)
                h_arr = np.array([h], dtype=float)
                st_y_arr = np.full_like(e_arr, 0.0)
                st_x_arr = np.full_like(n_arr, 0.0)
                st_h_arr = np.full_like(h_arr, 0.0)

                t.etrs_to_st70(n_arr, e_arr, h_arr, st_y_arr, st_x_arr, st_h_arr)

                st_x, st_y, st_h = st_x_arr[0], st_y_arr[0], st_h_arr[0]
            except Exception:
                pass  # leave output as NaN
        else:
            st_x = st_y = st_h = np.nan

        results.append((name, n, e, h, st_x, st_y, st_h))

    return results

@log_function(level='debug')
def convert_st70_etrs89(multiText: list[str]) -> list[tuple[str, float, float, float, float, float, float]]:
    """Converts coordinates from ST70 to ETRS89 for a list of input strings.
    
    Args:
        multiText (list[str]): A list of strings, each containing coordinates in the format 
                               suitable for conversion. Each string should include easting, 
                               northing, height, and a name.
    
    Returns:
        list[tuple[str, float, float, float, float, float, float]]: A list of tuples, 
        where each tuple contains the name, original easting, original northing, original 
        height, converted latitude, converted longitude, and converted height (altitude) 
        in ETRS89. If conversion fails or input values are NaN, the corresponding latitude, 
        longitude, and height will be NaN.
    """
    results = []
    t = romgeo.transformations.Transform(grid_mgmt.ROMGEO_GRID_FILE)

    for line in multiText:
        e, n, h, name = _split_floats_from_text(line)

        if not np.isnan(n) and not np.isnan(e) and not np.isnan(h):
            lat = lon = z = np.nan
            try:
                n_arr = np.array([n], dtype=float)
                e_arr = np.array([e], dtype=float)
                h_arr = np.array([h], dtype=float)
                lat_arr = np.full(1, 0.0)
                lon_arr = np.full(1, 0.0)
                z_arr   = np.full(1, 0.0)

                t.st70_to_etrs(n_arr, e_arr, h_arr, lat_arr, lon_arr, z_arr)

                lat, lon, z = lat_arr[0], lon_arr[0], z_arr[0]
            except Exception:
                pass
        else:
            lat = lon = z = np.nan

        results.append((name, e, n, h, lat, lon, z))

    return results







def test_1():
    import numpy
    TEST_MULTILIST = [
        "DEMO1 44°34\'31.54821\" 22°39\'02.48758\" 198.848",
        "DEMO2 N44g34m31.54821s 22 39 02.48758 E 198.848",
        "DEMO3 44.84821 22.48758 198.848m",
        "DEMO4 22.48758 44.84821 198.848",
        "ERR1 test 22 39 02.48758",
        "ERR2 44.84821 22.48758 nan",
        "ERR3 nan 0 nan",
        "ERR4 44.84821 22.48758"
    ]

    print("Test 1")
    print (convert_etrs_st70(TEST_MULTILIST))
    print("=" * 10)
def test_2():
    import numpy
    TEST_MULTILIST = [
        "DEMO1 344458.3829365224 313553.8380337978 157.25357634622287",
        "DEMO2 344458.3829365224 313553.8380337978 157.25357634622287",
        "DEMO3 375150.60522646806 301547.983126504 155.99730706694916",
        "ERR1 test 22 39 02.48758",
        "ERR2 44.84821 22.48758 nan",
        "ERR3 nan 0 nan",
        "ERR4 44.84821 22.48758"
    ]

    print("Test 2")
    print (convert_st70_etrs89(TEST_MULTILIST))
    print("=" * 10)
def test_3():
    import numpy
    TEST_MULTILIST = [
        "MAYBE_FLIPPED 25.48758 45.84821 198.848",
        "a 45.500000   25.500000   123.10"
    ]

    print("Test 3")
    print (convert_etrs_st70(TEST_MULTILIST))
    print("=" * 10)

if __name__ == "__main__":

    _,_ = grid_mgmt.select_best_grid()
    test_1()    
    test_2()
    test_3()
    #grid_mgmt.ROMGEO_GRID_FILE = "C:/Users/mihail.cretu/AppData/Local/romgeo/grids/rom_grid3d_408_api.spg"
    #print(convert_etrs_st70(["SULI	45°09'26.39240 N	29°40'20.24480 E	32.915"]))
