import xarray as xr
import matplotlib.pyplot as plt
import os

# 1. Point to your exact folder location
folder_path = os.getenv("FOLDER_PATH")  # Use the environment variable for folder path

# Find the .nc file you downloaded
nc_files = [f for f in os.listdir(folder_path) if f.endswith('.nc')]

if not nc_files:
    print("No .nc files found! Make sure you downloaded the file first.")
else:
    file_path = os.path.join(folder_path, nc_files[0])
    print(f"Reading from: {nc_files[0]}...")

    # 2. Open the dataset from your local hard drive
    ds = xr.open_dataset(file_path, engine="h5netcdf")

    # 3. DEFINE cloud_top_ir (This step was missing in your snippet)
    cloud_top_ir = ds["CMI_C13"].values

    # 4. Set up the visual plot
    plt.figure(figsize=(10, 10))
    plt.imshow(cloud_top_ir, cmap='Greys_r', vmin=180, vmax=310)
    plt.colorbar(label='Brightness Temperature (Kelvin)')
    plt.title("GOES-16 Local Data: Band 13 Cloud Top Infrared")
    
    # 5. Save the image to your Clouds folder
    output_image_path = os.path.join(folder_path, "GOES16_Band13_Image.png")
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Success! Image saved to: {output_image_path}")