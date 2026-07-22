import numpy as np
import netCDF4 as nc

def convert_nc_to_grasp(nc_path, output_sdata_path):
    # 1. Load netCDF variables (Update variable keys to match your netCDF schema)
    with nc.Dataset(nc_path, 'r') as ds:
        # Expected dimensions: [wavelength, view_angle/pixel]
        i0 = ds.variables['I0'][:]
        i45 = ds.variables['I45'][:]
        i90 = ds.variables['I90'][:]
        i135 = ds.variables['I135'][:]
        
        wavelengths = ds.variables['wavelength'][:]  # e.g., [450, 550, 650] in nm
        vza = ds.variables['view_zenith_angle'][:]    # Degrees
        vaa = ds.variables['view_azimuth_angle'][:]   # Degrees
        sza = ds.variables['solar_zenith_angle'][:]   # Scalar or matching dimension
        saa = ds.variables['solar_azimuth_angle'][:]   # Scalar or matching dimension
        f0 = ds.variables['solar_irradiance'][:]      # Extraterrestrial solar flux per band
        d_sun_earth = ds.variables['earth_sun_distance_corr'][0] # Scalar adjustment factor

    # 2. Mathematical calculation of Local Stokes Parameters
    I_raw = 0.5 * (i0 + i45 + i90 + i135)
    Q_local = i0 - i90
    U_local = i45 - i135

    # 3. Apply normalization to BRF
    # BRF = (pi * I * d^2) / F0
    norm_factor = (np.pi * (d_sun_earth**2)) / f0[:, np.newaxis]
    I_brf = I_raw * norm_factor
    Q_brf_local = Q_local * norm_factor
    U_brf_local = U_local * norm_factor

    # 4. Reference Frame Rotation Matrix 
    # (Example assumes standard scattering plane transformation angle 'phi')
    # Compute your actual scattering plane rotation angle 'phi' using SZA, SAA, VZA, VAA geometry here.
    phi = np.radians(saa - vaa) 
    
    Q_grasp = Q_brf_local * np.cos(2*phi) + U_brf_local * np.sin(2*phi)
    U_grasp = -Q_brf_local * np.sin(2*phi) + U_brf_local * np.cos(2*phi)

    # 5. Generate GRASP sdata Text File
    with open(output_sdata_path, 'w') as f:
        # Header Metadata Strings
        f.write("GRASP SDS DATA VERSION 1.0\n")
        f.write(f"1 1 1  # 1 Ground Station, 1 Date, 1 Measurement Type\n")
        f.write("# Latitude Longitude Altitude\n")
        f.write("37.7749 -122.4194 0.0\n") # Replace with your deployment coordinates
        
        # Measurement block configuration details
        num_wavelengths = len(wavelengths)
        num_geometry_points = len(vza)
        
        # Record Line: Year Month Day Hour Minute Second ...
        f.write("2026 07 22 12 00 00 0 0.0 0.0\n") 
        
        # Loop through and structure the data row by row
        for w_idx, wl in enumerate(wavelengths):
            f.write(f"  # Wavelength: {wl} nm\n")
            for g_idx in range(num_geometry_points):
                # Format: Measurement_Type, WL_index, SZA, VZA, Relative_Azimuth, I, Q, U
                # (GRASP code maps: 1=I, 2=Q, 3=U or combinations based on your specific YAML config)
                rel_azimuth = abs(saa[g_idx] - vaa[g_idx])
                
                f.write(f"  1 {w_idx+1} {sza[g_idx]:.4f} {vza[g_idx]:.4f} {rel_azimuth:.4f} "
                        f"{I_brf[w_idx, g_idx]:.6e} {Q_grasp[w_idx, g_idx]:.6e} {U_grasp[w_idx, g_idx]:.6e}\n")

    print(f"Success: GRASP file exported to {output_sdata_path}")
