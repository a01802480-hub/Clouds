import s3fs
import xarray as xr
import os
from datetime import datetime, timezone

# Step 1: Connect to the public NOAA GOES S3 bucket anonymously
fs = s3fs.S3FileSystem(anon=True)

# Step 2: Navigate the AWS folder tree dynamically to guarantee the latest file
current_year = datetime.now(timezone.utc).strftime('%Y')

# UPDATE: Point to the new GOES-19 bucket instead of GOES-16
base_path = f"noaa-goes19/ABI-L2-MCMIPF/{current_year}/"

print("Scanning AWS for the most recent GOES-19 data...")

try:
    # 1. Find the most recent Day folder
    available_days = fs.ls(base_path)
    latest_day = sorted(available_days)[-1]
    
    # 2. Find the most recent Hour folder inside that Day
    available_hours = fs.ls(latest_day)
    latest_hour = sorted(available_hours)[-1]
    
    # 3. Find the most recent File inside that Hour
    available_files = fs.ls(latest_hour)
    latest_file = sorted(available_files)[-1]
    
    print(f"Success! Latest live file found: {latest_file}")

except IndexError:
    raise FileNotFoundError(f"Connected to AWS, but no files found in {base_path}")
except FileNotFoundError:
    raise FileNotFoundError(f"Could not reach AWS or the folder {base_path} does not exist.")

# Step 3: Open NetCDF file directly from AWS S3 into memory
with fs.open(latest_file) as f:
    ds = xr.open_dataset(f, engine="h5netcdf")

    # Extract Cloud Top Infrared Brightness Temperature (Band 13)
    cloud_top_ir = ds["CMI_C13"].values
    print("Cloud Top IR Matrix Shape:", cloud_top_ir.shape)
    
    # Save locally (Updated file name for GOES-19)
    save_path = os.getenv("SAVE_PATH", "latest_goes19_band13.nc")
    ds["CMI_C13"].to_netcdf(save_path)
    print(f"Successfully saved the live Band 13 data to {save_path}")