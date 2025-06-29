from pathlib import Path

import config
import grid_mgmt

from functions import _is_inside_bounds, _dd2dms, _filter_inside_bounds, _round_columns, _dd_to_dms_vec, _fill_missing_names

from logutil import log

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import ezdxf
from csv import QUOTE_NONNUMERIC

# region ...for the future
# def _save_as_xlsb(df: pd.DataFrame, path: Path, sheet_name="Sheet1"):
#     try:
#         import xlwings as xw
#         import win32com.client
#         try:
#             excel = win32com.client.Dispatch("Excel.Application")
#             print("✅ Excel is installed.")
#         except Exception as e:
#             print("Excel is NOT installed or not registered for COM.")
#             print(f"Error: {e}")
#         # Ensure the file ends with .xlsb
#         path = path.with_suffix('.xlsb')
#         # Launch Excel and write data
#         app = xw.App(visible=False)
#         try:
#             wb = app.books.add()
#             sht = wb.sheets[0]
#             sht.name = sheet_name
#             sht.range("A1").value = [df.columns.tolist()] + df.values.tolist()
#             wb.save(str(path))
#             wb.close()
#         finally:
#             app.quit()
#     except ImportError:
#         print("xlwings is not installed. Please install it to save as XLSB.")
#         return "xlwings not installed", -1
#     return path
# endregion

def df_to_geodataframe(df, x_field: str = "st70_X", y_field: str = "st70_Y", z_field: str = "H_mn", geometry_col: str = "geometry", crs: str = "EPSG:3844", swap_xy: bool = False) -> gpd.GeoDataFrame:
    """
    Creates a GeoDataFrame with 3D Point geometry using specified columns.

    Args:
        df (pd.DataFrame): Input DataFrame with coordinate columns.
        x_field (str): Name of the X (Easting) column.
        y_field (str): Name of the Y (Northing) column.
        z_field (str): Name of the Z (height) column.
        geometry_col (str): Name of the geometry column to create.
        crs (str): Coordinate Reference System (e.g., "EPSG:3844").
        swap_xy (bool): If True, swaps X and Y values.

    Returns:
        GeoDataFrame with specified CRS and geometry.
    """
    east = df[y_field] if swap_xy else df[x_field]
    north = df[x_field] if swap_xy else df[y_field]
    elev = df[z_field]

    df[geometry_col] = [Point(e, n, z) for e, n, z in zip(east, north, elev)]

    print(
        f"{'Swapping' if swap_xy else 'Using'} {x_field} and {y_field} "
        f"({'Y as East' if swap_xy else 'X = East'}) with CRS {crs}."
    )

    return gpd.GeoDataFrame(df, geometry=geometry_col, crs=crs)


# region st70 exports

# OK
def save_st70_as_shape(points, shapefile_path, swap_xy = config.SWAP_XY_SHP):
    """Save ST70 points as a shapefile.
    
    This function takes a list of points and saves them as a shapefile in the specified path. 
    It filters the points based on predefined bounds and optionally swaps the X and Y coordinates 
    before saving.
    
    Args:
        points (list): A list of points where each point is expected to be a list or tuple 
                       containing the necessary attributes.
        shapefile_path (str or Path): The file path where the shapefile will be saved.
        swap_xy (bool, optional): If True, swaps the X and Y coordinates. Defaults to True.
    
    Returns:
        str: The path to the saved shapefile, or a message indicating that no valid points 
             were found after filtering.
    
    Raises:
        ValueError: If the input points do not contain the required fields.
    """

    #points = convert_etrs_st70(multiText)

    shapefile_path = Path(shapefile_path)
    dest_dir = shapefile_path.parent
    shapefile_name = shapefile_path.stem

    # Prepare transformed data for GeoDataFrame
    columns = ["Name", "Lat", "Lon", "H_Ell", "st70_X", "st70_Y", "H_mn"]

    df = pd.DataFrame(points, columns=columns)

    # Filter out rows with NaN in any of the required columns
    df = df.dropna(subset=["Lat", "Lon", "H_Ell", "st70_X", "st70_Y", "H_mn"])
    
    # Filter out invalid points (using `is_inside_bounds` + H_mn range check)
    df = _filter_inside_bounds(df,"st70", "st70_X", "st70_Y", "H_mn")

    if df.empty:
        return "No valid points found after filtering. No shapefile was created.",-1
    
    # Fill DMS columns
    df["Lat_t"] = _dd_to_dms_vec(df["Lat"].values, safe=True)
    df["Lon_t"] = _dd_to_dms_vec(df["Lon"].values, safe=True)

    # Round st70_X, st70_Y, and H_mn to 3 decimals for table attributes (while keeping geometry at full precision)
    df = _round_columns(df, ["st70_X", "st70_Y", "H_mn"])

    # Create geometry (full precision for GIS processing)
    gdf = df_to_geodataframe(df,
                             x_field="st70_X", y_field="st70_Y", z_field="H_mn",
                             swap_xy=swap_xy,
                             crs = "EPSG:3844")

    # Save Shapefile
    try:
        gdf.to_file(shapefile_path, driver="ESRI Shapefile", engine="fiona")
    except Exception as e:
        log('Got exception while exporting:\n{e}', level='error', also_print=True)
        return "export failed",-1

    print(f"3D Shapefile saved to: {shapefile_path}")

    # Save .prj file with vertical CRS
    prj_path = dest_dir / f"{shapefile_name}.prj"
    with open(prj_path, "w") as prj_file:
        prj_file.write(config.SHP_PRJ_CONTENT)

    return shapefile_path, df.shape[0],  # Return the path and number of valid points saved

# OK
def save_st70_as_excel(points, excel_path, force_csv=False, engine=None):
    """Save a filtered set of points to an Excel file.
    
    This function takes a list of points, filters them based on specific criteria, and saves the resulting DataFrame to an Excel file at the specified path. The filtering criteria include checking if the points are within certain bounds and if their height values fall within a defined range.
    
    Args:
        points (list of dict): A list of dictionaries where each dictionary represents a point with keys corresponding to the columns.
        excel_path (str or Path): The file path where the Excel file will be saved.
    
    Returns:
        str: The path to the saved Excel file, or a message indicating that no valid points were found and no file was created.
    
    Raises:
        ValueError: If the provided points do not contain the required keys or if the excel_path is invalid.
    """

    excel_path = Path(excel_path)
    columns = ["Name", "Latitude", "Longitude", "Height_Ellipsoidal", "st70_X", "st70_Y", "H_mn"]
    df = pd.DataFrame(points, columns=columns)

    # Filter out rows with NaN in any of the required columns
    df = df.dropna(subset=["Latitude", "Longitude", "Height_Ellipsoidal", "st70_X", "st70_Y", "H_mn"])

    # Filter out invalid points (using bounds + height check)
    df = _filter_inside_bounds(df, "st70", "st70_X", "st70_Y", "H_mn")

    if df.empty:
        return "No valid points found after filtering. No Excel file was created.", -1

    # Fill DMS columns
    df["Latitude_DMS"]  = _dd_to_dms_vec(df["Latitude"].values)
    df["Longitude_DMS"] = _dd_to_dms_vec(df["Longitude"].values)

    # Round display columns
    df = _round_columns(df, ["st70_X", "st70_Y", "H_mn"])

    # Reorder columns for clarity
    output_columns = ["Name", "Latitude", "Latitude_DMS", "Longitude", "Longitude_DMS", "Height_Ellipsoidal", "st70_X", "st70_Y", "H_mn"]
    
    if force_csv:
        # Save as CSV if force_csv is True
        excel_path = excel_path.with_suffix('.csv')
        df.to_csv(excel_path, index=False, quoting=QUOTE_NONNUMERIC, escapechar='\\', doublequote=True, quotechar='"')
        print(f"CSV file saved to: {excel_path}")
    # elif excel_path.suffix.lower() == ".xlsb":
    #     excel_path = _save_as_xlsb(df[output_columns], excel_path)
    #     print(f"XLSB file saved to: {excel_path}")
    # else:
        # Save as Excel file
        df.to_excel(excel_path, index=False, columns=output_columns, engine=engine)
        print(f"Excel file saved to: {excel_path}")

    df.to_excel(excel_path, index=False, columns=output_columns)

    print(f"Excel file saved to: {excel_path}")

    return excel_path, df.shape[0]  # Return the path and number of valid points saved

# OK
def save_st70_as_dxf(points, dxf_path, swap_xy = config.SWAP_XY_DXF):
    """Save a collection of points as a DXF file.
    
    This function takes a list of points and saves them in a DXF format, optionally swapping the X and Y coordinates. It filters the points based on specified bounds and generates associated project and information files.
    
    Args:
        points (list): A list of points where each point is expected to be a dictionary containing keys such as "Name", "Latitude", "Longitude", "Height_Ellipsoidal", "st70_X", "st70_Y", and "H_mn".
        dxf_path (str or Path): The file path where the DXF file will be saved.
        swap_xy (bool, optional): If True, swaps the X and Y coordinates when saving. Defaults to True.
    
    Returns:
        str: The path to the created DXF file, or a message indicating that no valid points were found and no DXF file was created.
    """

    dxf_path = Path(dxf_path)
    dest_dir = dxf_path.parent
    dxf_name = dxf_path.stem

    columns = ["Name", "Latitude", "Longitude", "Height_Ellipsoidal", "st70_X", "st70_Y", "H_mn"]

    df = pd.DataFrame(points, columns=columns)

    is_large = df.shape[0] > config.MAX_POINTS_FOR_DXF

    # Filter out rows with NaN in any of the required columns
    df = df.dropna(subset=["Latitude", "Longitude", "Height_Ellipsoidal", "st70_X", "st70_Y", "H_mn"])
    
    df = _filter_inside_bounds(df, "st70", "st70_X", "st70_Y", "H_mn")

    if df.empty:
        return "No valid points found after filtering. No DXF file was created.", -1
    
    # Fill missing names with default values
    df = _fill_missing_names(df, "Name", prefix="Point ")

    # Round st70_X, st70_Y, and H_mn to 3 decimals for table attributes (while keeping geometry at full precision)
    df = _round_columns(df, ["st70_X", "st70_Y", "H_mn"])
    df = df.astype({"st70_X": "float32", "st70_Y": "float32", "H_mn": "float32"})

    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 6 #meters
    msp = doc.modelspace()

    # Prepare coordinates and labels efficiently
    if swap_xy:
        xs = df["st70_X"].values
        ys = df["st70_Y"].values
        hs = df["H_mn"].values
    else:
        xs = df["st70_Y"].values
        ys = df["st70_X"].values
        hs = df["H_mn"].values

    labels = df["Name"].values

    # Fast loop to add points (skip add_text for performance)
    for x, y, h, label in zip(xs, ys, hs, labels):
        msp.add_point((x, y, h), dxfattribs={"layer": "Stereo70_EPSG3844"})

        # Optional: enable only if needed, slows down massively
        if not is_large:
            msp.add_text(label, dxfattribs={"insert": (x + 5, y + 5, h), "layer": "Labels"})

    doc.saveas(dxf_path,fmt='bin')

    prj_path = dest_dir / f"{dxf_name}.prj"
    with open(prj_path, "w") as prj_file:
        prj_file.write(config.SHP_PRJ_CONTENT)

    info_txt_path = dest_dir / f"{dxf_name}.txt"
    with open(info_txt_path, "w") as info_file:
        info_file.write(config.INFO_TEXT)


    return dxf_path, df.shape[0]  # Return the path and number of valid points saved

#endregion



# region etrs exports

# OK
def save_etrs_as_shape(points, shapefile_path, swap_xy = config.SWAP_LATLON_SHP):
    """Save a set of points as a shapefile.
    
    This function takes a list of points and saves them as a shapefile at the specified path. 
    It filters the points based on predefined bounds and can swap the X and Y coordinates if specified.
    
    Args:
        points (list): A list of points where each point is expected to be a dictionary containing 
                       keys corresponding to the columns: "Name", "st70_X", "st70_Y", "H_mn", 
                       "Latitude", "Longitude", and "Height_Ellipsoidal".
        shapefile_path (str or Path): The file path where the shapefile will be saved.
        swap_xy (bool, optional): If True, swaps the X and Y coordinates in the output shapefile. 
                                   Defaults to False.
    
    Returns:
        str: The path to the saved shapefile, or a message indicating that no valid points were found 
             after filtering.
    """
    
    shapefile_path = Path(shapefile_path)
    dest_dir = shapefile_path.parent
    shapefile_name = shapefile_path.stem

    # Prepare transformed data for GeoDataFrame
    columns = ["Name", "st70_X", "st70_Y", "H_mn", "Lat", "Lon", "H_Ell"]

    df = pd.DataFrame(points, columns=columns)

    # Filter out rows with NaN in any of the required columns
    df = df.dropna(subset=["Lat", "Lon", "H_Ell", "st70_X", "st70_Y", "H_mn"])
    
    # Filter out invalid points (using `is_inside_bounds` + H_mn range check)
    df = _filter_inside_bounds(df,"st70", "st70_X", "st70_Y", "H_mn")

    if df.empty:
        return "No valid points found after filtering. No shapefile was created.",-1
    
    # Fill DMS columns
    df["Lat_t"] = _dd_to_dms_vec(df["Lat"].values, safe=True)
    df["Lon_t"] = _dd_to_dms_vec(df["Lon"].values, safe=True)

    # Round st70_X, st70_Y, and H_mn to 3 decimals for table attributes (while keeping geometry at full precision)
    df = _round_columns(df, ["st70_X", "st70_Y", "H_mn"])

    # Create geometry (full precision for GIS processing)
    gdf = df_to_geodataframe(df, 
                             x_field="Lon", y_field="Lat", z_field="H_Ell",
                             swap_xy=swap_xy,
                             crs = "EPSG:4258")

    # Save Shapefile
    try:
        gdf.to_file(shapefile_path, driver="ESRI Shapefile", engine="fiona")
    except Exception as e:
        log('Got exception while exporting:\n{e}', level='error', also_print=True)
        return "export failed"

    print(f"3D Shapefile saved to: {shapefile_path}")

    # # Save .prj file with vertical CRS
    # prj_path = dest_dir / f"{shapefile_name}.prj"
    # with open(prj_path, "w") as prj_file:
    #     prj_file.write(config.SHP_PRJ_CONTENT)

    return shapefile_path, df.shape[0]  # Return the path and number of valid points saved

# OK
def save_etrs_as_excel(points, excel_path, force_csv=False, engine=None):
    """Saves a DataFrame of points to an Excel file after filtering based on specified criteria.
    
    Args:
        points (list of dict): A list of dictionaries containing point data with keys corresponding to the columns.
        excel_path (str or Path): The file path where the Excel file will be saved.
    
    Returns:
        str: The path to the saved Excel file, or a message indicating that no valid points were found.
    
    Raises:
        ValueError: If the provided points do not contain the required data or if the excel_path is invalid.
    
    Notes:
        The function filters points based on their coordinates and height, rounding the values before saving.
        The output Excel file will contain the following columns: 
        "Name", "st70_X", "st70_Y", "H_mn", "Latitude", "Longitude", "Height_Ellipsoidal".
    """
    
    excel_path = Path(excel_path)
    columns = ["Name", "st70_X", "st70_Y", "H_mn","Latitude", "Longitude", "Height_Ellipsoidal"]
    df = pd.DataFrame(points, columns=columns)

    # Filter out rows with NaN in any of the required columns
    df = df.dropna(subset=["st70_X", "st70_Y", "H_mn","Latitude", "Longitude", "Height_Ellipsoidal"])    

    # Filter out invalid points (using bounds + height check)
    df = _filter_inside_bounds(df, "etrs", "Latitude", "Longitude", "Height_Ellipsoidal")

    if df.empty:
        return "No valid points found after filtering. No Excel file was created.", -1

    # Fill DMS columns
    df["Latitude_DMS"]  = _dd_to_dms_vec(df["Latitude"].values)
    df["Longitude_DMS"] = _dd_to_dms_vec(df["Longitude"].values)

    # Round display columns
    df = _round_columns(df, ["st70_X", "st70_Y", "H_mn"])

    # Reorder columns for clarity
    output_columns = ["Name", "st70_X", "st70_Y", "H_mn", "Latitude", "Latitude_DMS", "Longitude", "Longitude_DMS", "Height_Ellipsoidal"]

    if force_csv:
        # Save as CSV if force_csv is True
        excel_path = excel_path.with_suffix('.csv')
        df.to_csv(excel_path, index=False, quoting=QUOTE_NONNUMERIC, escapechar='\\', doublequote=True, quotechar='"')
        print(f"CSV file saved to: {excel_path}")
    # elif excel_path.suffix.lower() == ".xlsb":
    #     excel_path = _save_as_xlsb(df[output_columns], excel_path)
    #     print(f"XLSB file saved to: {excel_path}")
    else:
        # Save as Excel file
        df.to_excel(excel_path, index=False, columns=output_columns, engine=engine)
        print(f"Excel file saved to: {excel_path}")
    
    return excel_path, df.shape[0]  # Return the path and number of valid points saved

# OK
def save_etrs_as_dxf(points, dxf_path, swap_xy = config.SWAP_XY_DXF):
    """Save a collection of points as a DXF file.
    
    This function takes a list of points and saves them in a DXF format. The points are filtered based on specified bounds and conditions before being written to the DXF file. The function also allows for the swapping of the X and Y coordinates.
    
    Args:
        points (list of dict): A list of dictionaries where each dictionary represents a point with keys corresponding to the columns: 
            "Name", "st70_X", "st70_Y", "H_mn", "Latitude", "Longitude", "Height_Ellipsoidal".
        dxf_path (str or Path): The file path where the DXF file will be saved.
        swap_xy (bool, optional): If True, swaps the Latitude and Longitude values when saving. Defaults to True.
    
    Returns:
        str: The path to the saved DXF file, or a message indicating that no valid points were found and no file was created.
    """
    
    dxf_path = Path(dxf_path)
    dest_dir = dxf_path.parent
    dxf_name = dxf_path.stem

    columns = ["Name", "st70_X", "st70_Y", "H_mn", "Latitude", "Longitude", "Height_Ellipsoidal"]

    df = pd.DataFrame(points, columns=columns)

    is_large = df.shape[0] > config.MAX_POINTS_FOR_DXF

    # Filter out rows with NaN in any of the required columns
    df = df.dropna(subset=["st70_X", "st70_Y", "H_mn", "Latitude", "Longitude", "Height_Ellipsoidal"])    

    df = _filter_inside_bounds(df, "etrs", "Latitude", "Longitude", "Height_Ellipsoidal")
    
    if df.empty:
        return "No valid points found after filtering. No DXF file was created.", -1

    df = _fill_missing_names(df, "Name", prefix="Point ")
    
    # Round st70_X, st70_Y, and H_mn to 3 decimals for table attributes (while keeping geometry at full precision)
    df = _round_columns(df, ["st70_X", "st70_Y", "H_mn"])
    df = df.astype({"st70_X": "float32", "st70_Y": "float32", "H_mn": "float32"})

    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 21 #degrees
    msp = doc.modelspace()

    # Prepare coordinates and labels efficiently
    if swap_xy:
        xs = df["Latitude"].values
        ys = df["Longitude"].values
        hs = df["Height_Ellipsoidal"].values
    else:
        xs = df["Longitude"].values
        ys = df["Latitude"].values
        hs = df["Height_Ellipsoidal"].values

    labels = df["Name"].values

    # Fast loop to add points (skip add_text for performance)
    for x, y, h, label in zip(xs, ys, hs, labels):
        msp.add_point((x, y, h), dxfattribs={"layer": "ETRS89_EPSG4258"})

        # Optional: enable only if needed, slows down massively
        if not is_large:
            msp.add_text(label, dxfattribs={"insert": (x + 5, y + 5, h), "layer": "Labels"})

    doc.saveas(dxf_path, fmt='bin')

    return dxf_path, df.shape[0]  # Return the path and number of valid points saved

# endregion

if __name__ == "__main__":
    _, _ = grid_mgmt.select_best_grid()

    def generate_random_data(n=1_000_000):
        import numpy as np
        names = np.random.choice(['P1', 'P2', 'P3', 'P4', 'P5'], size=n)
        st70_X = np.random.uniform(300000.0, 900000.0, size=n)            # Example ST70 X range
        st70_Y = np.random.uniform(200000.0, 800000.0, size=n)            # Example ST70 Y range
        H_mn = np.random.uniform(0.0, 500.0, size=n)                      # Black Sea normal height
        lat = np.random.uniform(43.5, 48.5, size=n)                   # Romania approx lat
        lon = np.random.uniform(20.0, 29.5, size=n)                   # Romania approx lon
        ell_h = H_mn + np.random.uniform(30.0, 60.0, size=n)              # Just an offset example

        #data = np.column_stack([names, st70_X, st70_Y, H_mn, lat, lon, ell_h])
        data = np.rec.fromarrays(
            [names, st70_X, st70_Y, H_mn, lat, lon, ell_h],
            names=['Name', 'st70_X', 'st70_Y', 'H_mn', 'Latitude', 'Longitude', 'Height_Ellipsoidal']
        )
        return data.tolist()

    #save_st70_as_shape(config.DEF_MULTILIST, 'C:\\ROMGEO\\romgeo-table-convert-gui\\test\\test_out.shp')
    #save_st70_as_dxf(config.DEF_MULTILIST, 'C:\\ROMGEO\\romgeo-table-convert-gui\\test\\test_out.dxf')