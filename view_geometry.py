import numpy as np

def calculate_view_geometry(roll_deg, pitch_deg, yaw_deg, pixel_vector=None):
    """
    Calculates View Zenith Angle (VZA) and View Azimuth Angle (VAA) 
    from system Roll, Pitch, and Yaw.
    
    Convention:
    - Global: X=East, Y=North, Z=Up
    - Yaw (y): 0 is North, clockwise rotation
    - VAA: 0 to 360 degrees clockwise from North
    """
    # 1. Convert orientation angles to radians
    r = np.radians(roll_deg)
    p = np.radians(pitch_deg)
    y = np.radians(yaw_deg)
    
    # 2. Define Local Look Vector (Default to center optical axis/boresight)
    if pixel_vector is None:
        v_local = np.array([0.0, 1.0, 0.0])
    else:
        v_local = np.array(pixel_vector)
        
    # 3. Structural Aerospace Rotation Matrices
    R_y = np.array([
        [np.cos(y), -np.sin(y), 0],
        [np.sin(y),  np.cos(y), 0],
        [0,         0,          1]
    ])
    
    R_p = np.array([,
        [0, np.cos(p), -np.sin(p)],
        [0, np.sin(p),  np.cos(p)]
    ])
    
    # Note: Roll rotation relative to the Y-axis alignment
    R_r = np.array([
        [ np.cos(r), 0, np.sin(r)],
        [ 0,         1, 0        ],
        [-np.sin(r), 0, np.cos(r)]
    ])
    
    # 4. Transform Local Vector to Global Frame (Yaw * Pitch * Roll)
    R_total = R_y @ R_p @ R_r
    v_global = R_total @ v_local
    
    X_g, Y_g, Z_g = v_global[0], v_global[1], v_global[2]
    magnitude = np.linalg.norm(v_global)
    
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
    vza, vaa = calculate_view_geometry(s["r"], s["p"], s["y"])
    print(f"{s['name']:<30} | {vza:<10.2f} | {vaa:<10.2f}")
