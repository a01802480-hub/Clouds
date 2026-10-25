import s3fs
import xarray as xr
import pandas as pd
import pyproj
import numpy as np
import os
# 1. Connect to AWS and open the files (same as before)
fs = s3fs.S3FileSystem(anon=True)

cps_files = fs.ls("noaa-goes16/ABI-L2-CPSF/2024/001/12/") 
ctt_files = fs.ls("noaa-goes16/ABI-L2-ACHTF/2024/001/12/") 
pres_files = fs.ls("noaa-goes16/ABI-L2-CTPF/2024/001/12/") 

with fs.open(cps_files[0]) as f_cps, fs.open(ctt_files[0]) as f_ctt, fs.open(pres_files[0]) as f_pres:
    ds_cps = xr.open_dataset(f_cps, engine="h5netcdf")
    ds_ctt_aligned = xr.open_dataset(f_ctt, engine="h5netcdf").interp_like(ds_cps, method="nearest")
    ds_pres_aligned = xr.open_dataset(f_pres, engine="h5netcdf").interp_like(ds_cps, method="nearest")
    
    # 2. SET UP THE GPS PROJECTION MATH
    # GOES files contain the satellite's exact orbital math inside the 'goes_imager_projection' variable
    proj_info = ds_cps.goes_imager_projection
    
    # Create a pyproj conversion object using the satellite's altitude and center longitude
    sat_height = proj_info.perspective_point_height
    p = pyproj.Proj(proj='geos', h=sat_height, lon_0=proj_info.longitude_of_projection_origin, sweep=proj_info.sweep_angle_axis)
    
    # Extract matrices
    r_t_matrix = ds_cps["CPS"].values
    temp_matrix = ds_ctt_aligned["TEMP"].values
    pres_matrix = ds_pres_aligned["PRES"].values
    
    # Get the 1D arrays of the raw x/y angles from the file and multiply by satellite height
    x_angles = ds_cps['x'].values * sat_height
    y_angles = ds_cps['y'].values * sat_height
    
    # Calculate center coordinates for the subset
    center_y = r_t_matrix.shape[0] // 2
    center_x = r_t_matrix.shape[1] // 2
    
    # Extract the exact 10x10 grid of X and Y coordinates
    subset_x = x_angles[center_x : center_x+10]
    subset_y = y_angles[center_y : center_y+10]
    
    # Create a meshgrid and convert to Latitude and Longitude
    xx, yy = np.meshgrid(subset_x, subset_y)
    lons, lats = p(xx, yy, inverse=True)
    
    # 3. Build the CSV rows with the new GPS data
    r_t_subset = r_t_matrix[center_y : center_y+10, center_x : center_x+10]
    temp_subset = temp_matrix[center_y : center_y+10, center_x : center_x+10]
    pres_subset = pres_matrix[center_y : center_y+10, center_x : center_x+10]
    
    records = []
    for row in range(10):
        for col in range(10):
            records.append({
                "Date_Time": ds_cps.time_coverage_start,
                "Latitude": lats[row, col],
                "Longitude": lons[row, col],
                "Droplet_Radius_um": r_t_subset[row, col],
                "Cloud_Top_Temp_K": temp_subset[row, col],
                "Cloud_Top_Pressure_hPa": pres_subset[row, col]
            })
            
    # 4. Export to CSV 
    df = pd.DataFrame(records)
    csv_path = os.getenv("CSV_PATH2")
    df.to_csv(csv_path, index=False)
    print(f"Success! GPS coordinates mapped and saved to: {csv_path}")