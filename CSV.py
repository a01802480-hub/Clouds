import s3fs
import xarray as xr
import pandas as pd

# 1. Connect to AWS
fs = s3fs.S3FileSystem(anon=True)

# 2. Locate the specific products needed for the FOIT equation
print("Searching for Particle Size and Temperature data...")
cps_files = fs.ls("noaa-goes16/ABI-L2-CPSF/2024/001/12/") # Cloud Particle Size for r(t)

# FIX: Changed CTTF to ACHTF to match the AWS directory structure
ctt_files = fs.ls("noaa-goes16/ABI-L2-ACHTF/2024/001/12/") 

# 3. Open both files directly from AWS
with fs.open(cps_files[0]) as f_cps, fs.open(ctt_files[0]) as f_ctt:
    ds_cps = xr.open_dataset(f_cps, engine="h5netcdf")
    ds_ctt = xr.open_dataset(f_ctt, engine="h5netcdf")
    
    scan_time = ds_cps.time_coverage_start
    print(f"Data captured on: {scan_time}")
    
    # Extract matrices
    r_t_matrix = ds_cps["CPS"].values
    
    # FIX: The variable name inside the ACHTF file is also "TEMP"
    temp_matrix = ds_ctt["TEMP"].values
    
    # Grab a subset for your spatial domain
    r_t_subset = r_t_matrix[2700:2710, 2700:2710]
    temp_subset = temp_matrix[2700:2710, 2700:2710]
    
    # 4. Loop and format for your fractional modeling dataset
    records = []
    for row in range(10):
        for col in range(10):
            records.append({
                "Date_Time": scan_time,
                "Local_Row": row,
                "Local_Col": col,
                "Droplet_Radius_um": r_t_subset[row, col],
                "Cloud_Top_Temp_K": temp_subset[row, col]
            })
            
    # 5. Export to CSV 
    df = pd.DataFrame(records)
    csv_path = r"C:\Users\Santiago Arizpe\OneDrive\Desktop\Clouds\foit_model_data.csv"
    df.to_csv(csv_path, index=False)
    
    print(f"Success! Generated kinematic data at: {csv_path}")