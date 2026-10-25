import s3fs
import xarray as xr
import os

# Step 1: Connect to the public NOAA GOES S3 bucket anonymously
fs = s3fs.S3FileSystem(anon=True)

# Step 2: List files in the GOES-16 Cloud & Moisture Imager (ABI-L2-MCMIP) bucket
# Path format: noaa-goes16/PRODUCT/YEAR/DAY_OF_YEAR/HOUR/
file_list = fs.ls("noaa-goes16/ABI-L2-MCMIPF/2024/001/12/") # Year 2024, Day 1, 12:00 UTC

print(f"Found {len(file_list)} GOES-16 full-disk imagery files.")

# Step 3: Open NetCDF file directly from AWS S3 into memory
with fs.open(file_list[0]) as f:
    ds = xr.open_dataset(f, engine="h5netcdf")

    # Extract Cloud Top Infrared Brightness Temperature (Band 13)
    cloud_top_ir = ds["CMI_C13"].values
    print("Cloud Top IR Matrix Shape:", cloud_top_ir.shape)
    ds["CMI_C13"].to_netcdf(os.getenv("SAVE_PATH"))
    print("Saved the Band 13 data to goes19_band13.nc")