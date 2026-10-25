import xarray as xr
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import mark_inset
import os

# 1. Point to your exact folder location
folder_path = os.getenv("FOLDER_PATH")  

# Find the .nc file you downloaded
nc_files = [f for f in os.listdir(folder_path) if f.endswith('.nc')]

if not nc_files:
    print("No .nc files found! Make sure you downloaded the file first.")
else:
    file_path = os.path.join(folder_path, nc_files[0])
    print(f"Reading from: {nc_files[0]}...")

    # 2. Open the dataset from your local hard drive
    ds = xr.open_dataset(file_path, engine="h5netcdf")

    # 3. Extract the full Cloud Top IR matrix
    cloud_top_ir = ds["CMI_C13"].values

    # Calculate center coordinates for the 10x10 subset
    center_y = cloud_top_ir.shape[0] // 2
    center_x = cloud_top_ir.shape[1] // 2

    # 4. Set up the main figure
    fig, ax = plt.subplots(figsize=(12, 12))

    # Plot the full disk on the main axis
    im = ax.imshow(cloud_top_ir, cmap='Greys_r', vmin=180, vmax=310)
    plt.colorbar(im, ax=ax, label='Brightness Temperature (Kelvin)', shrink=0.7)
    ax.set_title("GOES-19 Full Disk with 10x10 Center Zoom Inset")

    # 5. Create the zoomed inset box
    # [x, y, width, height] as fractions of the main plot (placed in the top right here)
    axins = ax.inset_axes([0.6, 0.6, 0.35, 0.35])

    # Plot the exact same full image inside the inset, but with 'none' interpolation for sharp pixels
    axins.imshow(cloud_top_ir, cmap='Greys_r', vmin=180, vmax=310, interpolation='none')

    # Zoom the inset strictly to your 10x10 pixel grid
    axins.set_xlim(center_x, center_x + 10)
    axins.set_ylim(center_y + 10, center_y) # Y-axis is inverted in image arrays (top is 0)

    # Add red gridlines to the zoomed inset to see individual pixels
    axins.set_xticks(range(center_x, center_x + 11))
    axins.set_yticks(range(center_y, center_y + 11))
    axins.grid(which='major', color='red', linestyle='-', linewidth=1.5)
    
    # Hide the tick labels on the inset so it looks clean
    axins.set_xticklabels([])
    axins.set_yticklabels([])

    # 6. Draw the connecting lines from the main map to the zoomed box
    # loc1 and loc2 are the corners of the box to connect (1=upper right, 2=upper left, 3=lower left, 4=lower right)
    mark_inset(ax, axins, loc1=2, loc2=4, fc="none", ec="red", lw=2)

    # 7. Save the image
    output_image_path = os.path.join(folder_path, "GOES_Inset_Zoom_Image.png")
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Success! Map with zoomed inset saved to: {output_image_path}")