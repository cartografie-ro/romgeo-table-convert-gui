import pickle
import numpy as np
# import matplotlib.pyplot as plt
import json
from types import SimpleNamespace

from typing import Optional, Literal

class SPGFile:
    """SPGFile class for handling and processing SPG (Spatial Pickle Grid) files.
    
    This class provides methods to load, save, visualize, and compare geodetic shifts and geoid heights from SPG files. It supports various formats for saving data, including JSON and CSV, and allows for the generation of metadata files.
    
    Attributes:
        data (dict): The loaded data from the SPG pickle file.
        datans (SimpleNamespace): A recursive namespace representation of the data.
        geodetic_shifts (np.ndarray): The grid data for geodetic shifts.
        geodetic_metadata (dict): Metadata associated with the geodetic shifts grid.
        geoid_heights (np.ndarray): The grid data for geoid heights.
        geoid_metadata (dict): Metadata associated with the geoid heights grid.
    
    Methods:
        _load_pickle() -> dict:
            Load the SPG pickle file and return its contents as a dictionary.
    
        get_metadata() -> dict:
            Return metadata for both geodetic shifts and geoid heights grids.
    
        get_spg_version() -> dict:
            Retrieve the version information from the metadata.
    
        generate_tree_structure(obj=None, indent=0) -> str:
            Recursively generate a tree-like structure of the SPG file, displaying parameter values compactly.
    
        save_spg(output_path: str):
            Save the current data back into a .spg (pickle) file.
    
        save_json(output_path: str):
            Save the SPG file content as JSON.
    
        generate_metadata_json(output_path: str = None):
            Generate a metadata.json file for the SPG grid based on class metadata.
    
        save_csv(grid_name: str, output_path: str):
            Save a specified grid (geodetic_shifts or geoid_heights) as a CSV file.
    
        visualize_geodetic_shifts_e(saveas: Optional[str] = None):
            Visualize geodetic shifts as a grid.
    
        visualize_geodetic_shifts_real(saveas: Optional[str] = None):
            Visualize geodetic shifts using real-world coordinates.
    
        visualize_geoid_heights_e(saveas: Optional[str] = None):
            Visualize geoid heights as a grid.
    
        visualize_geoid_heights_real(saveas: Optional[str] = None):
            Visualize geoid heights using real-world coordinates.
    
        compare_geoid_heights(other_file: str, saveas: Optional[str] = None):
            Compare geoid heights with another SPG file and visualize the differences.
    
        compare_geodetic_shifts(other_file: str, mode: Literal['x', 'y', 'both'] = 'both', saveas: Optional[str] = None):
            Compare geodetic shifts with another SPG file and visualize the differences.
    
        compare_geoid_heights_interpolated(other_file: str, saveas: Optional[str] = None):
            Compare interpolated geoid heights with another SPG file and visualize the differences.
    """

    def __init__(self, file_path: Optional[str] = None):
        """Initialize the SPG file by loading data and structuring it."""
        if file_path:
            self.file_path = file_path
            self.data = self._load_pickle()
        else:
            self.data = self.generate_empty_spg_structure()

        self.datans = self._recursive_namespace(self.data)

        # Separate grids
        self.geodetic_shifts = self.data["grids"]["geodetic_shifts"]["grid"]
        self.geodetic_metadata = self.data["grids"]["geodetic_shifts"]["metadata"]
        
        self.geoid_heights = self.data["grids"]["geoid_heights"]["grid"]
        self.geoid_metadata = self.data["grids"]["geoid_heights"]["metadata"]

    def _load_pickle(self) -> dict:
        """Load the SPG pickle file."""
        with open(self.file_path, "rb") as file:
            return pickle.load(file)
    
    def generate_empty_spg_structure():
        return {
            "params": {
                "input_file": "",
                "output_file": "grid.spg",
                "description": "Empty template grid",
            },
            "grids": {
                "geoid_heights": {
                    "grid": np.zeros((1, 160, 320), dtype=np.float32),  # placeholder shape
                    "metadata": {
                        "ndim": 1,
                        "minla": 19.930622,
                        "maxla": 30.5639447,
                        "minphi": 43.3923573,
                        "maxphi": 48.692352,
                        "stepla": 0.0333333,
                        "stepphi": 0.0333333,
                        "crs_type": "geodetic",
                        "ncols": 320,
                        "nrows": 160
                    }
                },
                "geodetic_shifts": {
                    "grid": np.zeros((2, 53, 72), dtype=np.float32),  # placeholder shape
                    "metadata": {
                        "ndim": 2,
                        "mine": 300000,
                        "maxe": 900000,
                        "minn": 420000,
                        "maxn": 620000,
                        "stepe": 8400 / 71,
                        "stepn": 2000 / 52,
                        "crs_type": "projected",
                        "ncols": 72,
                        "nrows": 53
                    }
                }
            },
            "metadata": {
                "release": {
                    "major": None,
                    "minor": None,
                    "revision": 0,
                    "legacy": None
                },
                "created_by": "CNC",
                "release_date": None,
                "valid_from": None,
                "valid_to": None
            }
        }


    def get_metadata(self) -> dict:
        """Return metadata for both grids."""
        return {
            "geodetic_shifts": self.geodetic_metadata,
            "geoid_heights": self.geoid_metadata
        }

    def get_spg_version(self) -> dict:
        try:
            m = self.data.get('metadata', {})
            vers = m.get('release',  {'major': None, 'minor': None, 'revision': 0, 'legacy': None})
            return vers
        
        except:
            return {'major': None, 'minor': None, 'revision': 0, 'legacy': None}

    def generate_tree_structure(self, obj=None, indent=0) -> str:
        """Recursively generate a tree-like structure of the SPG file, displaying parameter values compactly."""
        if obj is None:
            obj = self.data  # Start with the root of the pickle data
    
        tree_str = ""
        indent_str = " " * (indent * 2)
    
        if isinstance(obj, dict):
            for key, value in obj.items():
                tree_str += f"{indent_str}- {key}: {self._format_value(value)}\n"
                tree_str += self.generate_tree_structure(value, indent + 1)
        elif isinstance(obj, list):
            tree_str += f"{indent_str}- List[{len(obj)}]\n"
            if len(obj) > 0:
                tree_str += self.generate_tree_structure(obj[0], indent + 1)
        elif isinstance(obj, np.ndarray):
            tree_str += f"{indent_str}- NumPy Array (shape={obj.shape}, dtype={obj.dtype})\n"
    
        return tree_str
    
    def _format_value(self, value):
        """Format values for display in the tree structure."""
        if isinstance(value, str):
            return f"\"{value}\""
        elif isinstance(value, (float, np.float32, np.float64)):
            return f"{value} (dtype={np.dtype(type(value)).name})"
        elif isinstance(value, (int, np.int32, np.int64)):
            return f"{value} (dtype={np.dtype(type(value)).name})"
        return type(value).__name__

    def save_spg(self, output_path: str):
        """Save the current data back into a .spg (pickle) file."""
        with open(output_path, "wb") as file:
            pickle.dump(self.data, file, protocol=pickle.HIGHEST_PROTOCOL)
    
    def save_json(self, output_path: str):
        """Save the SPG file content as JSON."""
        with open(output_path, "w") as file:
            json.dump(self.data, file, indent=4)

    def generate_metadata_json(self, output_path: str = None):
        """Generate a metadata.json file for the SPG grid based on class metadata."""
        metadata = self.data.get("metadata", {})
        output_file = self.data.get("params", {}).get("output_file", "grid.spg")

        if metadata:
            metadata_json = metadata
        else:
        
            metadata_json = {
                output_file: {
                    "file": output_file,
                    "license": "CC by-nd 4.0",
                    "created_by": "CNC",
                    "attribution": (
                        '<p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/">'
                        '<a property="dct:title" rel="cc:attributionURL" href="https://romgeo.ro/grids">'
                        'RomGEO Densified transformation Grid</a> by '
                        '<a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://cartografie.ro">'
                        'Centrul National de Cartografie</a> is licensed under '
                        '<a href="https://creativecommons.org/licenses/by-sa/4.0/?ref=chooser-v1" target="_blank" '
                        'rel="license noopener noreferrer" style="display:inline-block;">'
                        'Creative Commons Attribution-NoDerivatives 4.0 International'
                        '<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" '
                        'src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1" alt="">'
                        '<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" '
                        'src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1" alt="">'
                        '<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" '
                        'src="https://mirrors.creativecommons.org/presskit/icons/nd.svg?ref=chooser-v1" alt="">'
                        '</a></p>'
                    ),
                    "abstract": "(C) CNC 2025",
                    "notes": "exact replica of previous version grid (4.0.8)",
                    "release": {
                        "major": metadata.get("major_release", '25'),
                        "minor": metadata.get("minor_release", '04'),
                        "revision": metadata.get("revision", 0),
                        "legacy": metadata.get("legacy", "no"),
                    },
                    "release_date": metadata.get("release_date", "2025-04-30T00:00:00+00:00"),
                    "valid_from": metadata.get("valid_from", "2025-04-30T00:00:00+00:00"),
                    "valid_to": metadata.get("valid_to", "None"),
                }
            }
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(metadata_json, f, indent=4, ensure_ascii=False)
        else:
            return metadata_json
    
    
    def save_csv(self, grid_name: str, output_path: str):
        """Save a grid as CSV (geodetic_shifts or geoid_heights)."""
        import pandas as pd
        grid = self.geodetic_shifts if grid_name == "geodetic_shifts" else self.geoid_heights
        pd.DataFrame(grid[0]).to_csv(output_path, index=False)  # Save first layer if 3D

    def _recursive_namespace(self, obj):
        if isinstance(obj, dict):
            return SimpleNamespace(**{k: self._recursive_namespace(v) for k, v in obj.items()})
        elif isinstance(obj, list):
            return [self._recursive_namespace(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._recursive_namespace(item) for item in obj)
        else:
            return obj  # Includes NumPy arrays, primitives, etc.
    
    # def _visualize_heatmap_e(self, grid: np.ndarray, title: str, saveas: Optional[str] = None):
    #     """Plot a heatmap for grid-like structured data."""
    #     flipped_grid = np.flipud(grid)
    #     plt.figure(figsize=(10, 6))
    #     plt.imshow(flipped_grid, cmap="viridis", aspect="auto", interpolation="nearest")
    #     plt.colorbar(label="Value")
    #     plt.title(title)
    #     plt.xlabel("X index")
    #     plt.ylabel("Y index")
        
    #     if saveas:
    #         plt.savefig(saveas)
    #         plt.close()
    #     else:
    #         plt.show()
    
    # def _visualize_heatmap_real_geodetic(self, grid: np.ndarray, saveas: Optional[str] = None):
    #     """Plot a heatmap for the Geodetic Shifts Grid using real-world coordinates."""
    #     min_lon, max_lon = self.geodetic_metadata["mine"], self.geodetic_metadata["maxe"]  # X-axis (Longitude)
    #     min_lat, max_lat = self.geodetic_metadata["minn"], self.geodetic_metadata["maxn"]  # Y-axis (Latitude)
        
    #     lon_values = np.linspace(min_lon, max_lon, grid.shape[1])  # Longitude points
    #     lat_values = np.linspace(min_lat, max_lat, grid.shape[0])  # Latitude points
        
    #     flipped_grid = np.flipud(grid)  # Ensure correct vertical alignment
        
    #     plt.figure(figsize=(10, 6))
    #     plt.imshow(flipped_grid, cmap="viridis", aspect="auto", interpolation="nearest",
    #                extent=[min_lon, max_lon, min_lat, max_lat])
    #     plt.colorbar(label="Value")
    #     plt.title("Geodetic Shifts Grid (Real Coordinates)")
    #     plt.xlabel("Longitude (°)")
    #     plt.ylabel("Latitude (°)")

    #     if saveas:
    #         plt.savefig(saveas)
    #         plt.close()
    #     else:
    #         plt.show()
    
    # def _visualize_heatmap_real_geoid(self, grid: np.ndarray, saveas: Optional[str] = None):
    #     """Plot a heatmap for the Geoid Heights Grid using real-world coordinates."""
    #     min_lon, max_lon = self.geoid_metadata["minla"], self.geoid_metadata["maxla"]  # X-axis (Longitude)
    #     min_lat, max_lat = self.geoid_metadata["minphi"], self.geoid_metadata["maxphi"]  # Y-axis (Latitude)
        
    #     lon_values = np.linspace(min_lon, max_lon, grid.shape[1])  # Longitude points
    #     lat_values = np.linspace(min_lat, max_lat, grid.shape[0])  # Latitude points
        
    #     flipped_grid = np.flipud(grid)  # Ensure correct vertical alignment
        
    #     plt.figure(figsize=(10, 6))
    #     plt.imshow(flipped_grid, cmap="viridis", aspect="auto", interpolation="nearest",
    #                extent=[min_lon, max_lon, min_lat, max_lat])
    #     plt.colorbar(label="Value")
    #     plt.title("Geoid Heights Grid (Real Coordinates)")
    #     plt.xlabel("Longitude (°)")
    #     plt.ylabel("Latitude (°)")

    #     if saveas:
    #         plt.savefig(saveas)
    #         plt.close()
    #     else:
    #         plt.show()
    
    # def visualize_geodetic_shifts_e(self, saveas: Optional[str] = None):
    #     """Visualize geodetic shifts as a grid."""
    #     self._visualize_heatmap_e(self.geodetic_shifts[0], "Geodetic Shifts Grid (Grid Index)", saveas)
    
    # def visualize_geodetic_shifts_real(self, saveas: Optional[str] = None):
    #     """Visualize geodetic shifts using real-world coordinates."""
    #     self._visualize_heatmap_real_geodetic(self.geodetic_shifts[0], saveas)
    
    # def visualize_geoid_heights_e(self, saveas: Optional[str] = None):
    #     """Visualize geoid heights as a grid."""
    #     self._visualize_heatmap_e(self.geoid_heights[0], "Geoid Heights Grid (Grid Index)", saveas)
    
    # def visualize_geoid_heights_real(self, saveas: Optional[str] = None):
    #     """Visualize geoid heights using real-world coordinates."""
    #     self._visualize_heatmap_real_geoid(self.geoid_heights[0], saveas)


    # def compare_geoid_heights(self, other_file: str, saveas: Optional[str] = None):
    #     other = SPGFile(other_file)

    #     lat1 = np.linspace(self.geoid_metadata['minphi'], self.geoid_metadata['maxphi'], self.geoid_metadata['nrows'])
    #     lon1 = np.linspace(self.geoid_metadata['minla'], self.geoid_metadata['maxla'], self.geoid_metadata['ncols'])

    #     lat2 = np.linspace(other.geoid_metadata['minphi'], other.geoid_metadata['maxphi'], other.geoid_metadata['nrows'])
    #     lon2 = np.linspace(other.geoid_metadata['minla'], other.geoid_metadata['maxla'], other.geoid_metadata['ncols'])

    #     min_lat, max_lat = max(lat1[0], lat2[0]), min(lat1[-1], lat2[-1])
    #     min_lon, max_lon = max(lon1[0], lon2[0]), min(lon1[-1], lon2[-1])

    #     def get_idx(axis, minv, maxv):
    #         return np.where((axis >= minv) & (axis <= maxv))[0]

    #     idx_lat1 = get_idx(lat1, min_lat, max_lat)
    #     idx_lon1 = get_idx(lon1, min_lon, max_lon)
    #     idx_lat2 = get_idx(lat2, min_lat, max_lat)
    #     idx_lon2 = get_idx(lon2, min_lon, max_lon)

    #     n = min(len(idx_lat1), len(idx_lat2))
    #     e = min(len(idx_lon1), len(idx_lon2))
    #     idx_lat1, idx_lon1 = idx_lat1[:n], idx_lon1[:e]
    #     idx_lat2, idx_lon2 = idx_lat2[:n], idx_lon2[:e]

    #     sub1 = np.squeeze(self.geoid_heights)[np.ix_(idx_lat1, idx_lon1)]
    #     sub2 = np.squeeze(other.geoid_heights)[np.ix_(idx_lat2, idx_lon2)]

    #     diff = sub1 - sub2
    #     rmse = np.sqrt(np.nanmean(diff ** 2))
    #     mean = np.nanmean(diff)

    #     lon_grid, lat_grid = np.meshgrid(lon1[idx_lon1], lat1[idx_lat1])

    #     plt.figure(figsize=(10, 6))
    #     plt.pcolormesh(lon_grid, lat_grid, diff, shading='auto', cmap='bwr')
    #     plt.colorbar(label='Geoid Height Difference (m)')
    #     plt.title(f'Geoid Height Difference\nRMSE: {rmse:.4f} m | Mean: {mean:.4f} m')
    #     plt.xlabel('Longitude')
    #     plt.ylabel('Latitude')
    #     plt.tight_layout()

    #     if saveas:
    #         plt.savefig(saveas)
    #         plt.close()
    #     else:
    #         plt.show()

    #     return rmse, mean

    # def compare_geodetic_shifts(self, other_file: str, mode: Literal['x', 'y', 'both'] = 'both', saveas: Optional[str] = None):
    #     other = SPGFile(other_file)

    #     n1 = np.linspace(self.geodetic_metadata['minn'], self.geodetic_metadata['maxn'], self.geodetic_metadata['nrows'])
    #     e1 = np.linspace(self.geodetic_metadata['mine'], self.geodetic_metadata['maxe'], self.geodetic_metadata['ncols'])
    #     n2 = np.linspace(other.geodetic_metadata['minn'], other.geodetic_metadata['maxn'], other.geodetic_metadata['nrows'])
    #     e2 = np.linspace(other.geodetic_metadata['mine'], other.geodetic_metadata['maxe'], other.geodetic_metadata['ncols'])

    #     min_n, max_n = max(n1[0], n2[0]), min(n1[-1], n2[-1])
    #     min_e, max_e = max(e1[0], e2[0]), min(e1[-1], e2[-1])

    #     def get_idx(axis, minv, maxv):
    #         return np.where((axis >= minv) & (axis <= maxv))[0]

    #     idx_n1 = get_idx(n1, min_n, max_n)
    #     idx_e1 = get_idx(e1, min_e, max_e)
    #     idx_n2 = get_idx(n2, min_n, max_n)
    #     idx_e2 = get_idx(e2, min_e, max_e)

    #     n = min(len(idx_n1), len(idx_n2))
    #     e = min(len(idx_e1), len(idx_e2))
    #     idx_n1, idx_e1 = idx_n1[:n], idx_e1[:e]
    #     idx_n2, idx_e2 = idx_n2[:n], idx_e2[:e]

    #     sub1 = self.geodetic_shifts[:, idx_n1[:, None], idx_e1]
    #     sub2 = other.geodetic_shifts[:, idx_n2[:, None], idx_e2]

    #     if mode == 'x':
    #         diff = sub1[0] - sub2[0]
    #         rmse = np.sqrt(np.nanmean(diff**2))
    #         title = f'X Shift Difference (RMSE: {rmse:.4f} m)'
    #     elif mode == 'y':
    #         diff = sub1[1] - sub2[1]
    #         rmse = np.sqrt(np.nanmean(diff**2))
    #         title = f'Y Shift Difference (RMSE: {rmse:.4f} m)'
    #     elif mode == 'both':
    #         dx = sub1[0] - sub2[0]
    #         dy = sub1[1] - sub2[1]
    #         diff = np.sqrt(dx**2 + dy**2)
    #         rmse = np.sqrt(np.nanmean(diff**2))
    #         title = f'Total Shift Difference Magnitude (Vector RMSE: {rmse:.4f} m)'
    #     else:
    #         raise ValueError("Mode must be 'x', 'y', or 'both'")

    #     sub_n = n1[idx_n1]
    #     sub_e = e1[idx_e1]
    #     lon_grid, lat_grid = np.meshgrid(sub_e, sub_n)

    #     plt.figure(figsize=(10, 6))
    #     plt.pcolormesh(lon_grid, lat_grid, diff, shading='auto', cmap='coolwarm')
    #     plt.colorbar(label='Shift Difference (m)')
    #     plt.title(title)
    #     plt.xlabel('Easting')
    #     plt.ylabel('Northing')
    #     plt.tight_layout()

    #     if saveas:
    #         plt.savefig(saveas)
    #         plt.close()
    #     else:
    #         plt.show()
   
    # def compare_geoid_heights_interpolated(self, other_file: str, saveas: Optional[str] = None):
    #     from scipy.interpolate import RegularGridInterpolator
    #     other = SPGFile(other_file)
    
    #     # Target grid (self)
    #     lat1 = np.linspace(self.geoid_metadata['minphi'], self.geoid_metadata['maxphi'], self.geoid_metadata['nrows'])
    #     lon1 = np.linspace(self.geoid_metadata['minla'], self.geoid_metadata['maxla'], self.geoid_metadata['ncols'])
    
    #     # Source grid (other)
    #     lat2 = np.linspace(other.geoid_metadata['minphi'], other.geoid_metadata['maxphi'], other.geoid_metadata['nrows'])
    #     lon2 = np.linspace(other.geoid_metadata['minla'], other.geoid_metadata['maxla'], other.geoid_metadata['ncols'])
    
    #     grid2 = np.squeeze(other.geoid_heights)
    #     interpolator = RegularGridInterpolator((lat2, lon2), grid2, bounds_error=False, fill_value=np.nan)
    
    #     # Generate coordinate pairs for interpolation
    #     lon_grid, lat_grid = np.meshgrid(lon1, lat1)
    #     points = np.stack([lat_grid.ravel(), lon_grid.ravel()], axis=-1)
    #     interp_grid2 = interpolator(points).reshape(len(lat1), len(lon1))
    
    #     # Compute difference
    #     grid1 = np.squeeze(self.geoid_heights)
    #     diff = grid1 - interp_grid2
    #     rmse = np.sqrt(np.nanmean(diff ** 2))
    #     mean = np.nanmean(diff)
    
    #     # Plot
    #     plt.figure(figsize=(10, 6))
    #     plt.pcolormesh(lon_grid, lat_grid, diff, shading='auto', cmap='bwr')
    #     plt.colorbar(label='Geoid Height Difference (m)')
    #     plt.title(f'Interpolated Geoid Height Difference\nRMSE: {rmse:.4f} m | Mean: {mean:.4f} m')
    #     plt.xlabel('Longitude')
    #     plt.ylabel('Latitude')
    #     plt.tight_layout()
    
    #     if saveas:
    #         plt.savefig(saveas)
    #         plt.close()
    #     else:
    #         plt.show()
    
    #     return rmse, mean
