import numpy as np

def generate_pixel_look_vectors(width, height, fx, fy, u0, v0):
    """
    Generates a 3D array [Height, Width, 3] containing the local 
    normalized look vector for every individual pixel on the sensor.
    """
    # 1. Create a coordinate grid grid for columns (u) and rows (v)
    u_grid, v_grid = np.meshgrid(np.arange(width), np.arange(height))
    
    # 2. Map coordinates using the intrinsic matrix formulation
    x_local = (u_grid - u0) / fx
    y_local = np.ones_like(u_grid, dtype=np.float64) # Boresight direction
    z_local = (v0 - v_grid) / fy                     # Invert row axis
    
    # 3. Stack components into an un-normalized 3D array matrix
    v_local_stack = np.stack([x_local, y_local, z_local], axis=-1)
    
    # 4. Normalize each vector to unit length
    magnitudes = np.linalg.norm(v_local_stack, axis=-1, keepdims=True)
    v_local_normalized = v_local_stack / magnitudes
    
    return v_local_normalized

# Example Configuration: Sony IMX250MZR Matrix Profile
width, height = 2464, 2056
# Compute estimated focal lengths in pixels
physical_focal_length_mm = 6.0  # Check your actual lens barrel
pixel_size_mm = 0.00345          # Sony IMX250MZR pixel pitch (3.45 microns)

fx = physical_focal_length_mm / pixel_size_mm
fy = physical_focal_length_mm / pixel_size_mm

print(f"Estimated fx: {fx_est:.2f}, fy: {fy_est:.2f}")
#fx, fy = 1500.0, 1500.0   # Example calibrated focal lengths in pixels
u0, v0 = 1232.0, 1028.0   # Center pixel coordinate defaults

# Generate the full sensor array grid mapping
all_look_vectors = generate_pixel_look_vectors(width, height, fx, fy, u0, v0)

# Check a pixel near the top-left corner
print("Top-Left Pixel Vector:", all_look_vectors[10, 10])
# Check the absolute center pixel (should point straight out along Y axis)
print("Center Pixel Vector:", all_look_vectors[1028, 1232])
