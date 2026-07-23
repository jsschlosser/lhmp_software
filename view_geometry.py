import numpy as np

def run(roll_deg, pitch_deg, yaw_deg, pixel_look_vectors=None):
    """
    Calculates View Zenith Angle (VZA) and View Azimuth Angle (VAA) 
    from system Roll, Pitch, and Yaw. Supports both single coordinate vectors 
    and multi-dimensional arrays of vectors (e.g., full sensor grids).
    
    Convention:
    - Global: X=East, Y=North, Z=Up
    - Yaw (y): 0 is North, clockwise rotation
    - VAA: 0 to 360 degrees clockwise from North

    :param roll_deg: Roll angle of the system in degrees.
    :type roll_deg: float
    :param pitch_deg: Pitch angle of the system in degrees.
    :type pitch_deg: float
    :param yaw_deg: Yaw angle of the system in degrees.
    :type yaw_deg: float
    :param pixel_look_vectors: Optional local look vector(s). Can be a 1D array of shape (3,) 
                         or an ND array where the last dimension is 3, such as 
                         (width, height, 3). Defaults to [0.0, 1.0, 0.0] (center optical axis).
    :type pixel_look_vectors: list or numpy.ndarray, optional
    :return: A tuple containing the View Zenith Angle (VZA) and View Azimuth Angle (VAA) in degrees.
             Returns scalar floats if pixel_look_vectors is 1D, or numpy arrays if pixel_look_vectors is ND.
    :rtype: tuple
    """
    # 1. Convert orientation angles to radians
    r = np.radians(roll_deg)
    p = np.radians(pitch_deg)
    y = np.radians(yaw_deg)
    
    # 2. Define Local Look Vector(s)
    if pixel_look_vectors is None:
        v_local = np.array([0.0, 1.0, 0.0])
    else:
        v_local = np.asarray(pixel_look_vectors)
        
    # 3. Structural Aerospace Rotation Matrices
    R_y = np.array([
        [np.cos(y), -np.sin(y), 0],
        [np.sin(y),  np.cos(y), 0],
        [0,         0,          1]
    ])
    
    R_p = np.array([
        [1, 0,          0         ],
        [0, np.cos(p), -np.sin(p) ],
        [0, np.sin(p),  np.cos(p) ]
    ])
    
    # Note: Roll rotation relative to the Y-axis alignment
    R_r = np.array([
        [ np.cos(r), 0, np.sin(r)],
        [ 0,         1, 0        ],
        [-np.sin(r), 0, np.cos(r)]
    ])
    
    # 4. Transform Local Vector(s) to Global Frame (Yaw * Pitch * Roll)
    R_total = R_y @ R_p @ R_r
    
    # Vectorized matrix multiplication: applies the 3x3 rotation matrix to 
    # the last dimension of v_local, whether it's shape (3,) or (W, H, 3)
    v_global = np.dot(v_local, R_total.T)
    
    # Extract components using ellipsis to support arbitrary dimensions
    X_g = v_global[..., 0]
    Y_g = v_global[..., 1]
    Z_g = v_global[..., 2]
    
    # Calculate magnitude along the last axis
    magnitude = np.linalg.norm(v_global, axis=-1)
    
    # 5. Calculate View Zenith Angle (VZA)
    vza_rad = np.arccos(Z_g / magnitude)
    vza_deg = np.degrees(vza_rad)
    
    # 6. Calculate View Azimuth Angle (VAA)
    # atan2(East, North) maps 0 to North, growing towards East
    vaa_rad = np.arctan2(X_g, Y_g)
    vaa_deg = np.degrees(vaa_rad)
    
    # Normalize azimuth angle strictly to standard 0-360 range
    vaa_deg = (vaa_deg + 360) % 360
    
    return vza_deg, vaa_deg

if __name__ == "__main__":
    # --- Multi-scenario Verification Matrix ---
    scenarios = [
        {"name": "Level pointing North", "r": 0, "p": 0, "y": 0},
        {"name": "Level pointing East", "r": 0, "p": 0, "y": 90},
        {"name": "Pitch up 30° facing North", "r": 0, "p": 30, "y": 0},
        {"name": "Pitch up 30° facing East", "r": 0, "p": 30, "y": 90},
    ]   

    print(f"{'Scenario':<30} | {'VZA (Deg)':<10} | {'VAA (Deg)':<10}")
    print("-" * 58)
    for s in scenarios:
        vza, vaa = run(s["r"], s["p"], s["y"])
        print(f"{s['name']:<30} | {vza:<10.2f} | {vaa:<10.2f}")
        
    print("\n" + "=" * 58)
    print("Testing 3D Sensor Array Input (W=2, H=2, 3)")
    
    # Mocking a tiny 2x2 sensor grid of vectors
    mock_sensor_vectors = np.array([
        [[ 0.1,  0.9, 0.0], [-0.1,  0.9, 0.0]],
        [[ 0.1,  0.9, 0.1], [-0.1,  0.9, 0.1]]
    ])
    
    vza_grid, vaa_grid = run(roll_deg=0, pitch_deg=30, yaw_deg=0, pixel_look_vectors=mock_sensor_vectors)
    
    print("\nVZA Grid Result Shape:", vza_grid.shape)
    print(vza_grid)
    print("\nVAA Grid Result Shape:", vaa_grid.shape)
    print(vaa_grid)