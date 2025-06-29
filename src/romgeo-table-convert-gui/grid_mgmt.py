import os, sys
from pathlib import Path

from logutil import log_function, log

import config

import spg_management as spg


ROMGEO_APPDATA  = Path(os.getenv('LOCALAPPDATA', os.path.expanduser("~\\AppData\\Local")))
ROMGEO_APPDATA  = ROMGEO_APPDATA / "romgeo"
ROMGEO_GRID_DIR = ROMGEO_APPDATA / "grids"
ROMGEO_GRID_DIR.mkdir(parents=True, exist_ok=True)

ROMGEO_GRID_FILE = 'internal'
ROMGEO_GRID_VER  = 'internal'

from pathlib import Path
from typing import Union

# import urllib.request
# import ssl

# Use the system certificate store (safe)
# _ssl_context = ssl.create_default_context()
# def _url_get_data(url: str) -> str:
#     """Downloads text data from a URL and returns it as a string."""
#     with urllib.request.urlopen(url, context=_ssl_context) as response:
#         return response.read().decode('utf-8')
# def _url_download_data(url: str, dest: Union[str, Path]) -> Path:
#     """Downloads file from URL and saves to `dest`. Returns the Path."""
#     dest_path = Path(dest)
#     dest_path.mkdir(parents=True,exist_ok=True)
#     with urllib.request.urlopen(url, context=_ssl_context) as response:
#         with open(dest_path, 'wb') as f:
#             f.write(response.read())
#     return dest_path

@log_function(level='debug')
def _compact_release_text(release):
    rev = f"-{release['revision']}" if release['revision'] > 0 else ''
    legacy = '-legacy' if release['legacy'] == 'yes' else ""

    return f"{release['major']:02}.{release['minor']:02}{rev}{legacy}"

@log_function(level='debug')
def _get_exe_dir() -> str:
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        return os.path.dirname(sys.executable)
    else:
        # Running in a normal Python environment
        return os.path.dirname(os.path.abspath(__file__))

@log_function(level='debug')
def _get_temp_dir() -> str:
    if getattr(sys, 'frozen', False):
        # This is the temp directory where onefile unpacks its contents
        print(f"{sys._MEIPASS=}")
        return sys._MEIPASS
    else:
        # When not frozen, fallback to script directory
        print(f"{os.path.dirname(os.path.abspath(__file__))}")
        return os.path.dirname(os.path.abspath(__file__))

@log_function(level='info')
def _latest_grid(ROMGEO_GRID_DIR):
    """
    Returns the Path to the .spg file:
    - Preferentially the one ending with 'latest.spg'
    - Otherwise the one with the highest (major, minor, revision) version
    """
    grid_files = list(Path(ROMGEO_GRID_DIR).glob("*.spg"))
    if not grid_files:
        return None

    # Priority: file ending in 'latest.spg'
    for f in grid_files:
        if f.name.endswith("latest.spg"):
            return f

    # Fallback: return file with highest version
    def version_key(file: Path) -> tuple:
        ver = spg.SPGFile(file).get_spg_version()
        return (
            int(ver.get('major') or 0),
            int(ver.get('minor') or 0),
            int(ver.get('revision') or 0),
        )

    return max(grid_files, key=version_key)

@log_function(level='info')
def git_get_prerelease() :
    """
    Check GitHub for the latest prerelease ROMGEO grid and return its metadata.

    Returns:
        dict or None: Metadata of the latest prerelease grid, or None if not found.
    """
    metadata_url = "https://raw.githubusercontent.com/cartografie-ro/romgeo-grid/main/grids/pre-release/metadata.json"

    log(f"Github Check for Pre-Release GRID", also_print=True)

    import requests

    try:
        response = requests.get(metadata_url)
        response.raise_for_status()
        metadata = response.json()

        # import json
        # metadata =  json.loads(_url_get_data(metadata_url))

        return  metadata.get('release', None), metadata.get('valid_from', None)

    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return None, None

@log_function(level='debug')
def git_get_exe_version(CURRENT_VERSION:str = 'v0.0.0') :
    import requests
    
    GITHUB_REPO = "cartografie-ro/romgeo-table-convert-gui"

    log(f"Github Check for new EXE", also_print=True)

    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        log(f"Failed to check for updates: {e}")
        return None

    data = response.json()
    latest_version = data.get("tag_name")

    if not latest_version:
        log("No tag name found in latest release.")
        return None

    if latest_version == CURRENT_VERSION:
        log(f"update_available: False, version: {CURRENT_VERSION}")
        return None

    # Get release info
    release_info = {
        "update_available": True,
        "latest_version": latest_version,
        "release_name": data.get("name"),
        "published_at": data.get("published_at"),
        "body": data.get("body"),
        "assets": [
            {
                "name": asset["name"],
                "size": asset["size"],
                "download_url": asset["browser_download_url"]
            }
            for asset in data.get("assets", [])
        ]
    }
    return release_info

@log_function(level='info')
def git_update_grid_files(local_version: str, download_dir: str) -> str:
    """
    Check for a new ROMGEO grid version on GitHub and download if it's newer.
    
    Args:
        local_version ({'major': 4, 'minor': 0, 'revision': 8, 'legacy': 'yes'}): Current installed grid version (e.g., "408" or "25.03").
        download_dir (str): Path where new files should be saved.
    
    Returns:
        bool: True if an update was performed, False otherwise.
    """
    base_url = "https://raw.githubusercontent.com/cartografie-ro/romgeo-grid/main/grids/latest/"
    metadata_url = base_url + "metadata.json"
    grid_file_url = base_url + "rom_grid3d_latest.spg"

    log(f"Github Check for New GRID", also_print=True)

    import requests

    try:
        # Fetch metadata
        response = requests.get(metadata_url)
        response.raise_for_status()
        metadata = response.json()

        latest_version = metadata.get("release", {'major': None, 'minor': None, 'revision': 0, 'legacy': None})
        latest_version = _compact_release_text(latest_version)

        # import json
        # metadata = json.loads(_url_get_data(metadata_url))

        if not latest_version:
            print("No 'release' key in metadata.")
            return None

        if latest_version != local_version:
            print(f"New release available: {latest_version} (current: {local_version})")

            # Download metadata
            # metadata_path = os.path.join(download_dir, "metadata.json")
            # with open(metadata_path, 'w') as f:
            #     json.dump(metadata, f, indent=2)
            # _url_download_data(grid_file_url, grid_path)

            # Download grid file
            grid_response = requests.get(grid_file_url)
            grid_response.raise_for_status()
            grid_path = os.path.join(download_dir, "rom_grid3d_latest.spg")
            with open(grid_path, 'wb') as f:
                f.write(grid_response.content)

            print(f"Downloaded new grid to {grid_path}")
            return grid_path
        else:
            print("Grid is up to date.")
            return None

    except Exception as e:
        print(f"Error checking or downloading grid: {e}")
        return None

@log_function(level='info')
def set_active_grid_file(file:str, ROMGEO_GRID_DIR:str = ROMGEO_GRID_DIR):

    GRID_FILE = Path(ROMGEO_GRID_DIR) / file
    GRID_VER = {'major': None, 'minor': None, 'revision': 0, 'legacy': None}

    if os.path.isfile(GRID_FILE):
        grid = spg.SPGFile(GRID_FILE)
        
        GRID_VER = _compact_release_text(grid.get_spg_version())
    else:
        raise Exception('Grid Invalid.')
    
    global ROMGEO_GRID_FILE
    global ROMGEO_GRID_VER
    ROMGEO_GRID_FILE, ROMGEO_GRID_VER = GRID_FILE, GRID_VER

    print(f"{ROMGEO_GRID_FILE=}, {ROMGEO_GRID_VER=}")

@log_function(level='info')
def select_best_grid(ROMGEO_GRID_DIR:str = ROMGEO_GRID_DIR):
    GRID_FILE = ''
    GRID_VER = {'major': None, 'minor': None, 'revision': 0, 'legacy': None}

    GRID_FILE = _latest_grid(ROMGEO_GRID_DIR)
    print(f"{GRID_FILE=}")

    if not GRID_FILE:

        # get internal
        GRID_FILE = _latest_grid(Path(_get_temp_dir()) / 'grids' )
        print(f"{GRID_FILE=}")

        if not GRID_FILE:
            # download online
            GRID_FILE = git_update_grid_files(GRID_VER, ROMGEO_GRID_DIR)

        if not GRID_FILE:
            # last change, no grid
            raise Exception('Nu a fost gasit niciun grid disponibil.')
        else:
            # do local copy
            import shutil
            shutil.copy2(GRID_FILE, Path(ROMGEO_GRID_DIR) / 'rom_grid3d_latest.spg' )

    if os.path.isfile(GRID_FILE):
        grid = spg.SPGFile(GRID_FILE)
        
        GRID_VER = _compact_release_text(grid.get_spg_version())
    else:
        raise Exception('Grid Invalid.')

    global ROMGEO_GRID_FILE
    global ROMGEO_GRID_VER
    ROMGEO_GRID_FILE, ROMGEO_GRID_VER = GRID_FILE, GRID_VER

    return GRID_FILE, GRID_VER

@log_function(level='info')
def do_online_grid_update():
    try:
        # atempt update new grid
        global ROMGEO_GRID_FILE
        global ROMGEO_GRID_VER

        ROMGEO_GRID_FILE, ROMGEO_GRID_VER = select_best_grid(ROMGEO_GRID_DIR)
        git_update_grid_files(ROMGEO_GRID_VER, ROMGEO_GRID_DIR)
    except:
        # update failed, defaulting to internal
        pass


if __name__ == "__main__":

    print(f"Pre-release:\n{git_get_prerelease()}")

    do_online_grid_update()

    ROMGEO_GRID_FILE, ROMGEO_GRID_VER = select_best_grid()

    print(f"\n\n {ROMGEO_GRID_FILE=} {ROMGEO_GRID_VER=}" )