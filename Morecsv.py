import s3fs
import xarray as xr
import pandas as pd
import os

# 1. Connect to AWS
fs = s3fs.S3FileSystem(anon=True)

print("Searching for Particle Size, Temperature, and Pressure data...")
cps_files = fs.ls("noaa-goes16/ABI-L2-CPSF/2024/001/12/") 
ctt_files = fs.ls("noaa-goes16/ABI-L2-ACHTF/2024/001/12/") 
pres_files = fs.ls("noaa-goes16/ABI-L2-CTPF/2024/001/12/") 

with fs.open(cps_files[0]) as f_cps, fs.open(ctt_files[0]) as f_ctt, fs.open(pres_files[0]) as f_pres:
    ds_cps = xr.open_dataset(f_cps, engine="h5netcdf")
    ds_ctt = xr.open_dataset(f_ctt, engine="h5netcdf")
    ds_pres = xr.open_dataset(f_pres, engine="h5netcdf")
    
    scan_time = ds_cps.time_coverage_start
    print(f"Data captured on: {scan_time}")
    
    # Extract matrices
    r_t_matrix = ds_cps["CPS"].values
    temp_matrix = ds_ctt["TEMP"].values
    pres_matrix = ds_pres["PRES"].values
    
    # FIX: Dynamically calculate the center of each matrix based on its specific shape
    def get_center_subset(matrix, size=10):
        center_y = matrix.shape[0] // 2
        center_x = matrix.shape[1] // 2
        return matrix[center_y : center_y + size, center_x : center_x + size]
    
    # Grab the center 10x10 subset for each variable safely
    r_t_subset = get_center_subset(r_t_matrix)
    temp_subset = get_center_subset(temp_matrix)
    pres_subset = get_center_subset(pres_matrix)
    
    # 4. Loop and format for your fractional modeling dataset
    records = []
    for row in range(10):
        for col in range(10):
            records.append({
                "Date_Time": scan_time,
                "Relative_Row": row,
                "Relative_Col": col,
                "Droplet_Radius_um": r_t_subset[row, col],
                "Cloud_Top_Temp_K": temp_subset[row, col],
                "Cloud_Top_Pressure_hPa": pres_subset[row, col]
            })
            
    # 5. Export to CSV 
    df = pd.DataFrame(records)
    cv_path = os.getenv("CSV_PATH")
    df.to_csv(cv_path, index=False)
    
    print(f"Success! Generated kinematic data at: {cv_path}")