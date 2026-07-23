import numpy as np

def run(fx, fy, u0, v0, width_p, height_p, physical_focal_length_mm, pixel_size_mm):
    """
    Generates a 3D array [Width, Height, 3] containing the local 
    normalized look vector for every individual pixel on the sensor.

    :param fx: Focal length in the x-direction, expressed in pixels.
    :type fx: float
    :param fy: Focal length in the y-direction, expressed in pixels.
    :type fy: float
    :param u0: X-coordinate of the principal point in pixels.
    :type u0: float
    :param v0: Y-coordinate of the principal point in pixels.
    :type v0: float
    :param width_p: Width of the sensor in pixels.
    :type width_p: int
    :param height_p: Height of the sensor in pixels.
    :type height_p: int
    :param physical_focal_length_mm: Physical focal length of the lens in millimeters.
    :type physical_focal_length_mm: float
    :param pixel_size_mm: Physical size of a single pixel in millimeters.
    :type pixel_size_mm: float
    :return: A 3D numpy array of shape (height, width, 3) representing unit look vectors for each pixel.
    :rtype: numpy.ndarray
    """
    
    u_grid, v_grid = np.meshgrid(np.arange(width_p), np.arange(height_p)) # 1. Create a coordinate grid grid for columns (u) and rows (v)
    x_local = (u_grid - u0) / fx # 2. Map coordinates using the intrinsic matrix formulation
    y_local = np.ones_like(u_grid, dtype=np.float64) # Boresight direction
    z_local = (v0 - v_grid) / fy                     # Invert row axis
    v_local_stack = np.stack([x_local, y_local, z_local], axis=-1) # 3. Stack components into an un-normalized 3D array matrix
    magnitudes = np.linalg.norm(v_local_stack, axis=-1, keepdims=True)  # 4. Normalize each vector to unit length
    v_local_normalized = v_local_stack / magnitudes
    
    return v_local_normalized

if __name__ == "__main__":
    # Added dummy parameters so the script can execute properly
    run(fx=1500.0, fy=1500.0, u0=1232.0, v0=1028.0, width_p=2464, height_p=2056, physical_focal_length_mm=6.0, pixel_size_mm=0.00345)