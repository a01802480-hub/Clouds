import numpy as np

# Convert the entire matrix from Kelvin to Celsius
temp_celsius = cloud_top_ir - 273.15

# Find the coldest and warmest spots
coldest_pixel = np.nanmin(temp_celsius)
warmest_pixel = np.nanmax(temp_celsius)

print(f"Coldest cloud top (Severe Weather): {coldest_pixel:.2f} °C")
print(f"Warmest surface (Clear Skies): {warmest_pixel:.2f} °C")