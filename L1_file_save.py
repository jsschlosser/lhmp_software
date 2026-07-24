import numpy as np 
import shutil
import netCDF4 as nc
import os
from datetime import date
from datetime import time
from datetime import datetime
from zoneinfo import ZoneInfo
from tqdm import tqdm
from suncalc import get_position
import polanalyser as pa
import nc_write
import NMEA_decode
import look_vectors
import view_geometry
def run():
	"""
	Copies an existing NetCDF file to a new location, processes polarization data
	in memory-efficient chunks, and writes directly to disk to prevent OOM errors.
	"""
	desired_data_date = input("Enter the date of the desired raw data in iso format (YYYY-MM-DD) or leave blank to default to today's date: ")
	if desired_data_date == "":
		desired_data_date = date.today().isoformat()
	file_suffix = input("Enter filename suffix or leave empty to default to 'test': ")
	if file_suffix=="":
		pathto_raw_data_file = f'../L0_data/BayerRG8_{desired_data_date}_test.nc'
		pathto_L1_data_file = f'../L1_data/BayerRG8_{desired_data_date}_test.nc'
	else:
		pathto_raw_data_file = f'../L0_data/BayerRG8_{desired_data_date}_{file_suffix}.nc'		
		pathto_L1_data_file = f'../L1_data/BayerRG8_{desired_data_date}_{file_suffix}.nc'

	physical_focal_length_mm = 6.0 # default, will update with method for getting exact values later.
	pixel_size_mm = 0.00345

	baselinedate = np.datetime64(f'{desired_data_date}T00:00:00', 's')	
	shutil.copy(pathto_raw_data_file, pathto_L1_data_file)
	
	gpsdate = desired_data_date.split("-")
	gpsdate_combined = "".join(gpsdate)	
	gpsfilename = [f for f in os.listdir(f'../gps_data/') if f.startswith(gpsdate_combined)]
	GPS_data = NMEA_decode.Run(filename=gpsfilename[0], path_to_file='../gps_data')
	gpstime_list = [datetime(int(gpsdate[0]), int(gpsdate[1]), int(gpsdate[2]), t.hour, t.minute, t.second, t.microsecond) for t in GPS_data['GGA']['time']]
	gpstime = np.array(gpstime_list, dtype='datetime64[s]')
	gpslon = np.array(GPS_data['GGA']['lon'])
	gpslat = np.array(GPS_data['GGA']['lat'])
	gpsalt = np.array(GPS_data['GGA']['alt'])

	with nc.Dataset(pathto_L1_data_file, 'a') as dataset:# Access variable references WITHOUT using [:] to avoid memory loading
		raw_signal_var = dataset.variables['Raw_Signal']
		time_var = dataset.variables['time']
		roll = dataset.variables['roll']
		pitch = dataset.variables['pitch']
		yaw	 = dataset.variables['yaw']
		dataset_length = raw_signal_var.shape[0]# Get dimensions dynamically from variable shapes
		h_pixel_length = raw_signal_var.shape[1]
		v_pixel_length = raw_signal_var.shape[2]
		
		angles = np.deg2rad([0, 45, 90, 135])
		new_dims = ('time', 'H_pixel', 'V_pixel')
		colors = ['blue', 'green', 'red']
		
		fx = physical_focal_length_mm / pixel_size_mm
		fy = physical_focal_length_mm / pixel_size_mm
		u0, v0 = v_pixel_length/2, h_pixel_length/2   # Center pixel coordinate defaults
		# Generate the full sensor array grid mapping
		pixel_look_vectors = look_vectors.run(fx, fy, u0, v0, v_pixel_length, h_pixel_length, 
												physical_focal_length_mm, pixel_size_mm)
		# Check a pixel near the top-left corner
		#print("Top-Left Pixel Vector:", all_look_vectors[10, 10])
		## Check the absolute center pixel (should point straight out along Y axis)
		#print("Center Pixel Vector:", all_look_vectors[1028, 1232])

		nc_vars = {}
		for clr in colors:# --- Step 1: Pre-create NetCDF variables on disk before processing ---
			for prefix, s_short, s_long in [('I', 'total intensity', 'light intensity signal in digital number (DN)'),
											('Q', 'horizontal-vertical intensity', 'I_(90)-I_(0) linear polarization'),
											('U', 'diagonal intensity', 'I_(+45)-I_(-45) degree linear polarization')]:
				var_name = f'{prefix}_{clr}'
				v = dataset.createVariable(var_name, 'f4', new_dims, zlib=True, complevel=5) # Lowered complevel to 5 for speed
				v.short_name = s_short
				v.units = 'DN'
				v.long_name = f'{clr} {s_long}'
				v.ACVSNC_standard_name = f'Rad_Radiance_Remote_{clr}' if prefix == 'I' else 'none'
				nc_vars[var_name] = v

		meta_vars_config = {# Pre-create 1D tracking variables
			'solar_azimuth': ('solar azimuth angle', 'degrees', 'Solar azimuth angle associated with sample location, altitude, and time'),
			'solar_altitude': ('solar altitude', 'degrees', 'Solar altitude angle associated with sample location, altitude, and time'), # Keeping original metadata long_name copy
			'view_azimuth': ('viwing azimuth angle', 'degrees', 'viewing azimuth angle associated with sample location, altitude, and time, and pixel position'),
			'view_zenith': ('viwing zenith angle', 'degrees', 'viewing zenith angle associated with sample location, altitude, and time, and pixel position'),			
			'GPS_longitude': ('longitude', 'degrees', 'sample longitude derived from GPS in degrees W'),
			'GPS_latitude': ('latitude', 'degrees', 'sample latitude derived from GPS in degrees N'),
			'GPS_altitude': ('altitude', 'm', 'sample altitude in MASL')}
		
		meta_vars = {}
		for name, config in meta_vars_config.items():
			if name.__contains__('view_'):
				dims = new_dims
			else:
				dims = 'time'
			v = dataset.createVariable(name, 'f4', dims, zlib=True, complevel=5)
			v.short_name = config[0]
			v.units = config[1]
			v.long_name = config[2]
			v.ACVSNC_standard_name = 'none'
			meta_vars[name] = v

		# --- Step 2: Chunked processing loop (One time-step/chunk at a time) ---
		# Adjust the step size if you want to process in small batches (e.g., step=10)
		chunk_step = 240 
		
		for i1 in range(0, dataset_length, chunk_step):
			end_chunk = min(i1 + chunk_step, dataset_length)
			
			# Slice only the required time window into memory
			image_data_chunk = raw_signal_var[i1:end_chunk, :, :]
			image_time_chunk = baselinedate + time_var[i1:end_chunk].astype('timedelta64[s]')
			roll_deg = roll[i1:end_chunk]
			pitch_deg = pitch[i1:end_chunk]
			yaw_deg = yaw[i1:end_chunk]

			# Mini arrays to hold the chunk calculations transiently
			actual_chunk_len = end_chunk - i1
			chunk_s0 = np.full((actual_chunk_len, h_pixel_length, v_pixel_length, 3), np.nan, dtype='f4')
			chunk_s1 = np.full((actual_chunk_len, h_pixel_length, v_pixel_length, 3), np.nan, dtype='f4')
			chunk_s2 = np.full((actual_chunk_len, h_pixel_length, v_pixel_length, 3), np.nan, dtype='f4')
			chunk_vaa = np.full((actual_chunk_len, h_pixel_length, v_pixel_length), np.nan, dtype='f4')
			chunk_vza = np.full((actual_chunk_len, h_pixel_length, v_pixel_length), np.nan, dtype='f4') 	

			chunk_lon = np.full((actual_chunk_len), np.nan, dtype='f4')
			chunk_lat = np.full((actual_chunk_len), np.nan, dtype='f4')
			chunk_alt = np.full((actual_chunk_len), np.nan, dtype='f4')
			chunk_pan = np.full((actual_chunk_len), np.nan, dtype='f4')
			chunk_tilt = np.full((actual_chunk_len), np.nan, dtype='f4')
			for i2, t_i2 in tqdm(enumerate(range(i1, end_chunk))):
				# Demosaic and calculate Stokes per index
				img_000_bgr, img_045_bgr, img_090_bgr, img_135_bgr = pa.demosaicing(image_data_chunk[i2, :, :], pa.COLOR_PolarRGB) 	
				img_stokes_bgr = pa.calcStokes([img_000_bgr, img_045_bgr, img_090_bgr, img_135_bgr], angles) 	
				
				chunk_s0[i2, ...] = np.squeeze(img_stokes_bgr[..., 0])
				chunk_s1[i2, ...] = np.squeeze(img_stokes_bgr[..., 1])
				chunk_s2[i2, ...] = np.squeeze(img_stokes_bgr[..., 2])
				
				# GPS & Sun Position calculations
				gps_index = np.where((gpstime == image_time_chunk[i2]))[0]
				if len(gps_index) > 0:
					chunk_lon[i2] = np.mean(gpslon[gps_index])
					chunk_lat[i2] = np.mean(gpslat[gps_index])
					chunk_alt[i2] = np.mean(gpsalt[gps_index])
				
				sun_pos = get_position(image_time_chunk[i2], chunk_lon[i2], chunk_lat[i2])
				chunk_pan[i2] = np.degrees(sun_pos['azimuth'])
				chunk_tilt[i2] = np.degrees(sun_pos['altitude'])

				chunk_vaa[i2,...],chunk_vza[i2,...] = view_geometry.run(roll_deg[i2], pitch_deg[i2], yaw_deg[i2], pixel_look_vectors)			 

			# --- Step 3: Stream and write current computed chunk directly to disk ---
			for i_clr, clr in enumerate(colors):
				nc_vars[f'I_{clr}'][i1:end_chunk, :, :] = chunk_s0[..., i_clr]
				nc_vars[f'Q_{clr}'][i1:end_chunk, :, :] = chunk_s1[..., i_clr]
				nc_vars[f'U_{clr}'][i1:end_chunk, :, :] = chunk_s2[..., i_clr]
				
			meta_vars['solar_azimuth'][i1:end_chunk] = chunk_pan
			meta_vars['solar_altitude'][i1:end_chunk] = chunk_tilt
			meta_vars['view_azimuth'][i1:end_chunk, :, :] = chunk_vaa
			meta_vars['view_zenith'][i1:end_chunk, :, :] = chunk_vza			
			meta_vars['GPS_longitude'][i1:end_chunk] = chunk_lon
			meta_vars['GPS_latitude'][i1:end_chunk] = chunk_lat
			meta_vars['GPS_altitude'][i1:end_chunk] = chunk_alt
			
			# Force disk synchronization and flush temporary RAM structures
			dataset.sync()
