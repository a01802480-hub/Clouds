import xarray as xr
import matplotlib.pyplot as plt
import os

# 1. Automatically find the downloaded .nc file in your Clouds folder
folder_path = r"C:\Users\Santiago Arizpe\OneDrive\Desktop\Clouds"
nc_files = [f for f in os.listdir(folder_path) if f.endswith('.nc')]

if not nc_files:
    print("No .nc files found!")
else:
    file_path = os.path.join(folder_path, nc_files[0])
    print(f"Reading from: {nc_files[0]}...")

    # 2. Open the dataset from your local hard drive
    ds = xr.open_dataset(file_path, engine="h5netcdf")

    # 3. Extract Band 13 (Cloud Top Infrared)
    cloud_top_ir = ds["CMI_C13"].values

    # 4. Set up the visual plot
    plt.figure(figsize=(10, 10))
    plt.imshow(cloud_top_ir, cmap='Greys_r', vmin=180, vmax=310)
    plt.colorbar(label='Brightness Temperature (Kelvin)')
    plt.title("GOES-16 Local Data: Band 13 Cloud Top Infrared")
    
    # 5. SAVE THE IMAGE INSTEAD OF SHOWING IT
    output_image_path = os.path.join(folder_path, "GOES16_Band13_Image.png")
    
    # dpi=300 makes it high-res, bbox_inches='tight' removes extra white space around the edges
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
    
    # Close the plot in the background to free up computer memory
    plt.close()
    
    print(f"Success! Image saved to: {output_image_path}")