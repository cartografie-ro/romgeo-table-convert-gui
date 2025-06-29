import pandas as pd
import os
import re

# Set display options
pd.set_option("display.max_colwidth", None)

# Threshold in seconds to consider an operation slow
SLOW_OPERATION_THRESHOLD = 0.01

def load_procmon_csv(filepath):
    usecols = ["Time of Day", "Process Name", "Operation", "Path", "Duration", "Result"]
    try:
        df = pd.read_csv(filepath, usecols=usecols, on_bad_lines='skip')
        df = df.dropna(subset=["Operation", "Duration"])
        df["Duration"] = pd.to_numeric(df["Duration"], errors='coerce')
        df = df.dropna(subset=["Duration"])
        return df
    except Exception as e:
        print("Failed to load file:", e)
        return None

def analyze_bottlenecks(df):
    print("\n--- Top Slow Operations (Average Duration) ---")
    op_summary = df.groupby("Operation")["Duration"].agg(["count", "mean", "max"]).sort_values(by="mean", ascending=False)
    print(op_summary.head(10))

    print("\n--- Top Slow Paths (Total Duration) ---")
    path_summary = df.groupby("Path")["Duration"].agg(["count", "sum", "max"]).sort_values(by="sum", ascending=False)
    print(path_summary.head(10))

    print("\n--- Slow 'Load Image' DLLs (> 10ms) ---")
    dll_loads = df[(df["Operation"] == "Load Image") & (df["Duration"] > SLOW_OPERATION_THRESHOLD)]
    if not dll_loads.empty:
        print(dll_loads[["Path", "Duration"]].sort_values(by="Duration", ascending=False).head(10))
    else:
        print("No slow DLL loads found.")

    print("\n--- Most Frequently Accessed Paths ---")
    repeated_paths = df["Path"].value_counts().head(10)
    print(repeated_paths)

    print("\n--- Slowest Individual Events ---")
    print(df.sort_values(by="Duration", ascending=False).head(10)[["Time of Day", "Operation", "Path", "Duration"]])

    print("\n--- Operation Frequency Summary ---")
    print(df["Operation"].value_counts().head(10))

    print("\n--- Operation Latency Summary (Mean & Max Duration) ---")
    op_latency = df.groupby("Operation")["Duration"].agg(["count", "mean", "max"]).sort_values(by="mean", ascending=False)
    print(op_latency.head(10))

    print("\n--- DLL Load Times by Folder ---")
    dll_df = df[(df["Operation"] == "Load Image") & df["Path"].notna()]
    dll_df = dll_df.copy()
    dll_df.loc[:, "Folder"] = dll_df["Path"].apply(lambda x: "\\".join(str(x).split("\\")[:3]))
    folder_times = dll_df.groupby("Folder")["Duration"].agg(["count", "mean", "sum"]).sort_values(by="sum", ascending=False)
    print(folder_times.head(10))

    print("\n--- Events Timeline (Per Second) ---")
    try:
        df["Timestamp"] = pd.to_datetime(df["Time of Day"], format="%H:%M:%S.%f", errors='coerce')
        df = df.dropna(subset=["Timestamp"])
        df.set_index("Timestamp", inplace=True)
        events_over_time = df.resample("1s").size()
        print(events_over_time.head(10))
    except Exception as e:
        print("Timeline generation failed:", e)

def get_loaded_dlls(df):
    # Extract all loaded DLLs (paths from 'Load Image' operations ending in .dll)
    dll_df = df[(df["Operation"] == "Load Image") & df["Path"].str.lower().str.endswith(".dll")]
    return sorted(set(dll_df["Path"]))

def get_unused_mei_files_auto(df):
    """
    Auto-detect the _MEI* folder accessed by the process and list unused files.
    
    Returns:
        List of files in the _MEI folder that were NOT accessed.
    """
    # 1. Detect MEI folder path from accessed paths
    mei_candidates = df["Path"].dropna().astype(str)
    mei_folders = set()

    for path in mei_candidates:
        match = re.search(r"(C:\\Users\\[^\\]+\\AppData\\Local\\romgeo\\app\\_MEI[^\\]+)", path, re.IGNORECASE)
        if match:
            mei_folders.add(match.group(1))

    if not mei_folders:
        print("No _MEI folder detected in trace.")
        return []

    # Assume first match is correct if multiple
    mei_folder_path = sorted(mei_folders)[0]
    print(f"Detected _MEI folder: {mei_folder_path}")

    # 2. Gather all files under _MEI folder
    all_mei_files = []
    for root, _, files in os.walk(mei_folder_path):
        for file in files:
            full_path = os.path.abspath(os.path.join(root, file))
            all_mei_files.append(full_path.lower())

    # 3. Get accessed paths from ProcMon logs
    accessed_paths = set(df["Path"].dropna().astype(str).str.lower())

    # 4. Compare and find unused files
    unused_files = [f for f in all_mei_files if f not in accessed_paths]

    print(f"Found {len(unused_files)} unused files in {mei_folder_path}")
    return unused_files


# ---- MAIN ----
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python procmon_analyzer.py path_to_procmon.csv")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"Analyzing: {filepath}")

    df = load_procmon_csv(filepath)
    if df is not None:
        analyze_bottlenecks(df)

        # Example: Get all DLLs loaded
        dlls = get_loaded_dlls(df)
        print(f"\n--- {len(dlls)} DLLs Loaded ---")
        for dll in dlls:
            if "System32" not in dll:
                print(dll)
        
        # unused DLLs
        unused = get_unused_mei_files_auto(df)
        print(f"--- Unused DLLs ---")
        for path in unused:
            print(path)