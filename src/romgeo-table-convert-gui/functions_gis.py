from pathlib import Path

import config
import grid_mgmt

from functions import _is_inside_bounds, _dd2dms

from logutil import log

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import ezdxf




# st70 exports
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
    columns = ["Name", "Lat", "Lon", "Height_Ellipsoidal", "st70_X", "st70_Y", "H_mn"]

    df = pd.DataFrame(points, columns=columns)
    
    df["Lat_t"]  = df["Lat"].apply(lambda x: _dd2dms(x,'DMS'))
    df["Lon_t"]  = df["Lon"].apply(lambda x: _dd2dms(x,'DMS'))

    # Filter out invalid points (using `is_inside_bounds` + H_mn range check)
    df = df[df.apply(lambda row: _is_inside_bounds(row["st70_X"], row["st70_Y"], "st70") and 
                                config.ZBOX_RO_ST70[0] <= row["H_mn"] <= config.ZBOX_RO_ST70[1], axis=1)]

    if df.empty:
        return "No valid points found after filtering. No shapefile was created."

    # Create geometry (full precision for GIS processing)
    if swap_xy:
        df["geometry"] = df.apply(lambda row: Point(row["st70_Y"], row["st70_X"], row["H_mn"]), axis=1)
        print("Swapping st70_X and st70_Y (Using Y as East, X as North).")
    else:
        df["geometry"] = df.apply(lambda row: Point(row["st70_X"], row["st70_Y"], row["H_mn"]), axis=1)
        print("Using standard EPSG:3844 coordinate order (X = East, Y = North).")

    # Convert to GeoDataFrame with EPSG:3844
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:3844")

    # Round st70_X, st70_Y, and H_mn to 3 decimals for table attributes (while keeping geometry at full precision)
    gdf["st70_X"] = gdf["st70_X"].round(3)
    gdf["st70_Y"] = gdf["st70_Y"].round(3)
    gdf["H_mn"] = gdf["H_mn"].round(3)

    # Save Shapefile
    try:
        gdf.to_file(shapefile_path, driver="ESRI Shapefile", engine="fiona")
    except Exception as e:
        log('Got exception while exporting:\n{e}', level='error', also_print=True)
        return "export failed"

    print(f"3D Shapefile saved to: {shapefile_path}")

    # Save .prj file with vertical CRS
    prj_path = dest_dir / f"{shapefile_name}.prj"
    with open(prj_path, "w") as prj_file:
        prj_file.write(config.SHP_PRJ_CONTENT)

    return shapefile_path

def save_st70_as_excel(points, excel_path):
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

    #points = convert_etrs_st70(multiText)

    excel_path = Path(excel_path)
    columns = ["Name", "Latitude", "Longitude", "Height_Ellipsoidal", "st70_X", "st70_Y", "H_mn"]
    df = pd.DataFrame(points, columns=columns)
    
    df["Latitude_DMS"]  = df["Latitude" ].apply(lambda x: _dd2dms(x,'DMS'))
    df["Longitude_DMS"] = df["Longitude"].apply(lambda x: _dd2dms(x,'DMS'))

    # Filter out invalid points (using bounds + height check)
    df = df[df.apply(lambda row: _is_inside_bounds(row["st70_X"], row["st70_Y"], "st70") and 
                                config.ZBOX_RO_ST70[0] <= row["H_mn"] <= config.ZBOX_RO_ST70[1], axis=1)]

    if df.empty:
        return "No valid points found after filtering. No Excel file was created."

    # Round display columns
    df["st70_X"] = df["st70_X"].round(3)
    df["st70_Y"] = df["st70_Y"].round(3)
    df["H_mn"]   = df["H_mn"].round(3)

    # Reorder columns for clarity
    output_columns = ["Name", "Latitude", "Latitude_DMS", "Longitude", "Longitude_DMS", "Height_Ellipsoidal", "st70_X", "st70_Y", "H_mn"]
    df.to_excel(excel_path, index=False, columns=output_columns)

    print(f"Excel file saved to: {excel_path}")

    return excel_path

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

    #points = convert_etrs_st70(multiText)

    dxf_path = Path(dxf_path)
    dest_dir = dxf_path.parent
    dxf_name = dxf_path.stem

    columns = ["Name", "Latitude", "Longitude", "Height_Ellipsoidal", "st70_X", "st70_Y", "H_mn"]

    df = pd.DataFrame(points, columns=columns)

    df = df[df.apply(lambda row: _is_inside_bounds(row["st70_X"], row["st70_Y"], "st70") and 
                                config.ZBOX_RO_ST70[0] <= row["H_mn"] <= config.ZBOX_RO_ST70[1], axis=1)]

    if df.empty:
        return "No valid points found after filtering. No DXF file was created."

    df["Name"] = df["Name"].fillna(df.index.to_series().apply(lambda x: f"Point {x+1}"))

    # Round st70_X, st70_Y, and H_mn to 3 decimals for table attributes (while keeping geometry at full precision)
    df["st70_X"] = df["st70_X"].round(3)
    df["st70_Y"] = df["st70_Y"].round(3)
    df["H_mn"]   = df["H_mn"  ].round(3)

    doc = ezdxf.new()
    msp = doc.modelspace()

    for idx, row in df.iterrows():
        x, y, h = (row["st70_X"], row["st70_Y"], row["H_mn"]) if swap_xy else (row["st70_Y"], row["st70_X"], row["H_mn"])
        label = row["Name"] if row["Name"] else f"Point {idx+1}"
        msp.add_point((x, y, h), dxfattribs={"layer": "Stereo70_EPSG3844"})
        msp.add_text(label, dxfattribs={"insert": (x + 5, y + 5, h), "layer": "Labels"})

    doc.saveas(dxf_path)

    prj_path = dest_dir / f"{dxf_name}.prj"
    with open(prj_path, "w") as prj_file:
        prj_file.write(config.SHP_PRJ_CONTENT)

    info_txt_path = dest_dir / f"{dxf_name}.txt"
    with open(info_txt_path, "w") as info_file:
        info_file.write(config.INFO_TEXT)


    return dxf_path





# etrs exports
def save_etrs_as_shape(points, shapefile_path, swap_xy = config.SWAP_XY_SHP):
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
    #points = convert_st70_etrs89(multiText)

    shapefile_path = Path(shapefile_path)
    dest_dir = shapefile_path.parent
    shapefile_name = shapefile_path.stem

    # Prepare transformed data for GeoDataFrame
    columns = ["Name", "st70_X", "st70_Y", "H_mn", "Lat", "Lon", "Height_Ellipsoidal"]

    df = pd.DataFrame(points, columns=columns)
    
    df["Lat_t"]  = df["Lat"].apply(lambda x: _dd2dms(x,'DMS'))
    df["Lon_t"]  = df["Lon"].apply(lambda x: _dd2dms(x,'DMS'))

    # Filter out invalid points (using `is_inside_bounds` + H_mn range check)
    df = df[df.apply(lambda row: _is_inside_bounds(row["st70_X"], row["st70_Y"], "st70") and 
                                config.ZBOX_RO_ST70[0] <= row["H_mn"] <= config.ZBOX_RO_ST70[1], axis=1)]

    if df.empty:
        return "No valid points found after filtering. No shapefile was created."

    # Create geometry (full precision for GIS processing)
    if swap_xy:
        df["geometry"] = df.apply(lambda row: Point(row["Lon"], row["Lat"], row["Height_Ellipsoidal"]), axis=1)
        print("Swapping st70_X and st70_Y (Using Y as East, X as North).")
    else:
        df["geometry"] = df.apply(lambda row: Point(row["Lat"], row["Lon"], row["Height_Ellipsoidal"]), axis=1)
        print("Using standard EPSG:4258 coordinate order (X = East, Y = North).")

    # Convert to GeoDataFrame with EPSG:4258
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4258")

    # Round st70_X, st70_Y, and H_mn to 3 decimals for table attributes (while keeping geometry at full precision)
    gdf["st70_X"] = gdf["st70_X"].round(3)
    gdf["st70_Y"] = gdf["st70_Y"].round(3)
    gdf["H_mn"] = gdf["H_mn"].round(3)

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

    return shapefile_path

def save_etrs_as_excel(points, excel_path):
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
    
    #points = convert_st70_etrs89(multiText)

    excel_path = Path(excel_path)
    columns = ["Name", "st70_X", "st70_Y", "H_mn","Latitude", "Longitude", "Height_Ellipsoidal"]
    df = pd.DataFrame(points, columns=columns)

    df["Latitude_DMS"]  = df["Latitude" ].apply(lambda x: _dd2dms(x,'DMS'))
    df["Longitude_DMS"] = df["Longitude"].apply(lambda x: _dd2dms(x,'DMS'))

    # Filter out invalid points (using bounds + height check)
    df = df[df.apply(lambda row: _is_inside_bounds(row["st70_X"], row["st70_Y"], "st70") and 
                                config.ZBOX_RO_ST70[0] <= row["H_mn"] <= config.ZBOX_RO_ST70[1], axis=1)]

    if df.empty:
        return "No valid points found after filtering. No Excel file was created."

    # Round display columns
    df["st70_X"] = df["st70_X"].round(3)
    df["st70_Y"] = df["st70_Y"].round(3)
    df["H_mn"]   = df["H_mn"].round(3)

    # Reorder columns for clarity
    output_columns = ["Name", "st70_X", "st70_Y", "H_mn", "Latitude", "Latitude_DMS", "Longitude", "Longitude_DMS", "Height_Ellipsoidal"]
    df.to_excel(excel_path, index=False, columns=output_columns)

    print(f"Excel file saved to: {excel_path}")
    return excel_path

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
    
    #points = convert_st70_etrs89(multiText)

    dxf_path = Path(dxf_path)
    dest_dir = dxf_path.parent
    dxf_name = dxf_path.stem

    columns = ["Name","Latitude", "Longitude", "Height_Ellipsoidal", "st70_X", "st70_Y", "H_mn"]

    df = pd.DataFrame(points, columns=columns)

    df = df[df.apply(lambda row: _is_inside_bounds(row["st70_X"], row["st70_Y"], "st70") and 
                                config.ZBOX_RO_ST70[0] <= row["H_mn"] <= config.ZBOX_RO_ST70[1], axis=1)]

    if df.empty:
        return "No valid points found after filtering. No DXF file was created."

    df["Name"] = df["Name"].fillna(df.index.to_series().apply(lambda x: f"Point {x+1}"))
    
    # Round st70_X, st70_Y, and H_mn to 3 decimals for table attributes (while keeping geometry at full precision)
    df["st70_X"] = df["st70_X"].round(3)
    df["st70_Y"] = df["st70_Y"].round(3)
    df["H_mn"]   = df["H_mn"  ].round(3)

    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 21 #degrees
    msp = doc.modelspace()

    for idx, row in df.iterrows():
        x, y, h = (row["Latitude"], row["Longitude"], row["Height_Ellipsoidal"]) if swap_xy else (row["Longitude"], row["Latitude"], row["Height_Ellipsoidal"])
        label = row["Name"] if row["Name"] else f"Point {idx+1}"
        msp.add_point((x, y, h), dxfattribs={"layer": "ETRS89_EPSG4258"})
        msp.add_text(label, dxfattribs={"insert": (x + 5, y + 5, h), "layer": "Labels"})

    doc.saveas(dxf_path)

    # prj_path = dest_dir / f"{dxf_name}.prj"
    # with open(prj_path, "w") as prj_file:
    #     prj_file.write(config.SHP_PRJ_CONTENT)

    # info_txt_path = dest_dir / f"{dxf_name}.txt"
    # with open(info_txt_path, "w") as info_file:
    #     info_file.write(config.INFO_TEXT)

    return dxf_path


if __name__ == "__main__":
    _, _ = grid_mgmt.select_best_grid()
    #save_st70_as_shape(config.DEF_MULTILIST, 'C:\\ROMGEO\\romgeo-table-convert-gui\\test\\test_out.shp')
    save_st70_as_dxf(config.DEF_MULTILIST, 'C:\\ROMGEO\\romgeo-table-convert-gui\\test\\test_out.dxf')
