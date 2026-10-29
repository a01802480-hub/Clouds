import s3fs
import xarray as xr
import pandas as pd
import pyproj
import numpy as np
import os
from datetime import datetime, timezone

# 1. Connect to AWS
fs = s3fs.S3FileSystem(anon=True)

# 2. DYNAMICALLY FIND THE LATEST LIVE GOES-19 DATA
current_year = datetime.now(timezone.utc).strftime('%Y')
base_path = f"noaa-goes19/ABI-L2-CPSF/{current_year}/"

print("Scanning AWS for the most recent GOES-19 data...")

try:
    # Drill down to find the latest Day and Hour folders
    available_days = fs.ls(base_path)
    latest_day = sorted(available_days)[-1]
    
    available_hours = fs.ls(latest_day)
    latest_hour = sorted(available_hours)[-1]
    
    # Extract the dynamic day and hour strings to use for the products
    day_str = latest_day.split('/')[-1]
    hour_str = latest_hour.split('/')[-1]
    
    # Build exact paths for all four products for this specific hour
    path_cps = f"noaa-goes19/ABI-L2-CPSF/{current_year}/{day_str}/{hour_str}/"
    path_ctt = f"noaa-goes19/ABI-L2-ACHTF/{current_year}/{day_str}/{hour_str}/"
    path_pres = f"noaa-goes19/ABI-L2-CTPF/{current_year}/{day_str}/{hour_str}/"
    path_cod = f"noaa-goes19/ABI-L2-CODF/{current_year}/{day_str}/{hour_str}/" # Added Optical Depth
    path_lwp = f"noaa-goes19/ABI-L2-LWPF/{current_year}/{day_str}/{hour_str}/" # Added Liquid Water Path
    # Grab the absolute latest file from each folder
    latest_cps = sorted(fs.ls(path_cps))[-1]
    latest_ctt = sorted(fs.ls(path_ctt))[-1]
    latest_pres = sorted(fs.ls(path_pres))[-1]
    latest_cod = sorted(fs.ls(path_cod))[-1] # Added Optical Depth
    latest_lwp = sorted(fs.ls(path_lwp))[-1] # Added Liquid Water Path
    print(f"Live files locked in:\n - {latest_cps.split('/')[-1]}")
    
except IndexError:
    raise FileNotFoundError("Connected to AWS, but the folders are currently empty.")

# 3. OPEN THE FILES AND EXTRACT METADATA
with fs.open(latest_cps) as f_cps, fs.open(latest_ctt) as f_ctt, fs.open(latest_pres) as f_pres, fs.open(latest_cod) as f_cod:
    ds_cps = xr.open_dataset(f_cps, engine="h5netcdf")
    ds_ctt_aligned = xr.open_dataset(f_ctt, engine="h5netcdf").interp_like(ds_cps, method="nearest")
    ds_pres_aligned = xr.open_dataset(f_pres, engine="h5netcdf").interp_like(ds_cps, method="nearest")
    ds_cod_aligned = xr.open_dataset(f_cod, engine="h5netcdf").interp_like(ds_cps, method="nearest") # Added Optical Depth
    
    proj_info = ds_cps.goes_imager_projection
    sat_id = ds_cps.attrs.get('platform_ID', 'Unknown')
    sat_height = proj_info.perspective_point_height
    sat_lon = proj_info.longitude_of_projection_origin
    sweep_axis = proj_info.sweep_angle_axis
    obs_time = ds_cps.time_coverage_start
    
    print("\n" + "="*50)
    print("SATELLITE ORBITAL & INSTRUMENT METADATA")
    print("="*50)
    print(f"Platform ID        : {sat_id}")
    print(f"Observation Time   : {obs_time}")
    print(f"Sub-Satellite Lon  : {sat_lon} Degrees")
    print(f"Orbital Altitude   : {sat_height} meters")
    print("="*50 + "\n")

    # 4. SET UP THE GPS PROJECTION MATH
    p = pyproj.Proj(proj='geos', h=sat_height, lon_0=sat_lon, sweep=sweep_axis)
    
    r_t_matrix = ds_cps["CPS"].values
    temp_matrix = ds_ctt_aligned["TEMP"].values
    pres_matrix = ds_pres_aligned["PRES"].values
    cod_matrix = ds_cod_aligned["COD"].values # Extract Optical Depth values
    lwp_matrix = ds_cod_aligned["LWP"].values # Extract Liquid Water Path values
    
    x_angles = ds_cps['x'].values * sat_height
    y_angles = ds_cps['y'].values * sat_height
    
    center_y = r_t_matrix.shape[0] // 2
    center_x = r_t_matrix.shape[1] // 2
    
    subset_x = x_angles[center_x : center_x+10]
    subset_y = y_angles[center_y : center_y+10]
    
    xx, yy = np.meshgrid(subset_x, subset_y)
    lons, lats = p(xx, yy, inverse=True)
    
    # 5. BUILD THE CSV ROWS
    r_t_subset = r_t_matrix[center_y : center_y+10, center_x : center_x+10]
    temp_subset = temp_matrix[center_y : center_y+10, center_x : center_x+10]
    pres_subset = pres_matrix[center_y : center_y+10, center_x : center_x+10]
    cod_subset = cod_matrix[center_y : center_y+10, center_x : center_x+10] # Subset Optical Depth
    
    records = []
    for row in range(10):
        for col in range(10):
            records.append({
                "Date_Time": obs_time,
                "Latitude": lats[row, col],
                "Longitude": lons[row, col],
                "Droplet_Radius_um": r_t_subset[row, col],
                "Cloud_Top_Temp_K": temp_subset[row, col],
                "Cloud_Top_Pressure_hPa": pres_subset[row, col],
                "Cloud_Optical_Depth": cod_subset[row, col], # Added to CSV record
                "liquid_Water_Path": lwp_matrix[row, col] # Added to CSV record
            })
            
    # 6. EXPORT DYNAMIC CSV
    df = pd.DataFrame(records)
    
    # Create a dynamic filename based on the satellite scan time so it never overwrites old data
    time_str = pd.to_datetime(obs_time).strftime("%Y%m%d_%H%M%S")
    dynamic_csv_name = f"live_cloud_data_with_cod_{time_str}.csv"
    
    # Use environment variable if set, otherwise use the dynamic name in the current folder
    csv_path = os.getenv("CSV_PATH2", dynamic_csv_name)
    df.to_csv(csv_path, index=False)
    print(f"Success! GPS coordinates mapped and saved to: {csv_path}")