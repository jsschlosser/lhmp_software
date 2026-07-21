from suncalc import get_position
import polanalyser as pa
import numpy as np 
import shutil
import netCDF4 as nc
from datetime import date
from datetime import time
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import nc_write
import NMEA_decode

def run():
	"""
	Copies an existing NetCDF file to a new location, adds a new dimension 
	and variable, and updates global attributes.

	:param source_path: The absolute or relative path to the original .nc file.
	:type source_path: str
	:param target_path: The destination path where the modified .nc file will be saved.
	:type target_path: str
	:raises IOError: If the source file cannot be found or read.
	:raises OSError: If there is a permissions issue or netCDF modification failure.
	"""
	#data = Dataset(pathto_raw_data_file,'r')
	#data_dictionary = {}		 
	#for key in data.variables.keys():
	#	vals = data.variables[key][:]
	#	print(key)
	#	data_dictionary[key] = vals#np.where(vals == '--', np.nan, vals)	

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
	baselinedate = np.datetime64(f'{desired_data_date}T00:00:00', 's')	
	shutil.copy(pathto_raw_data_file, pathto_L1_data_file)# 1. Copy the original file to the new destination ("Save As" workaround)
	gpsdate = desired_data_date.split("-")
	gpsdate_combined = "".join(gpsdate)	
	gpsfilename = [f for f in os.listdir(f'../gps_data/') if f.startswith(gpsdate_combined)]
	GPS_data = NMEA_decode.Run(filename=gpsfilename[0], path_to_file='../gps_data')
	gpstime_list = [datetime(int(gpsdate[0]), int(gpsdate[1]), int(gpsdate[2]), t.hour, t.minute, t.second, t.microsecond) for t in GPS_data['GGA']['time']]
	gpstime = np.array(gpstime_list, dtype='datetime64[s]')
	gpslon = np.array(GPS_data['GGA']['lon'])
	gpslat = np.array(GPS_data['GGA']['lat'])
	gpsalt = np.array(GPS_data['GGA']['alt'])
	with nc.Dataset(pathto_raw_data_file, 'a') as dataset:# 2. Open the newly copied file in append mode ('a') to modify it in place
		image_data = dataset.variables['Raw_Signal'][:]
		image_time = baselinedate + dataset.variables['time'][:].astype('timedelta64[s]')
		dataset_length = len(image_time)
		h_pixel_length = len(image_data[0,:,0])
		v_pixel_length = len(image_data[0,0,:])
		angles = np.deg2rad([0, 45, 90, 135])
		s0 = np.full((dataset_length, h_pixel_length, v_pixel_length, 3), np.nan)
		s1 = np.full((dataset_length, h_pixel_length, v_pixel_length, 3), np.nan)
		s2 = np.full((dataset_length, h_pixel_length, v_pixel_length, 3), np.nan)
		gps_lon = np.full((dataset_length),np.nan)
		gps_lat = np.full((dataset_length),np.nan)
		gps_alt = np.full((dataset_length),np.nan)
		pan = np.full((dataset_length),np.nan)
		tilt = np.full((dataset_length),np.nan)
		for i1 in range(0,dataset_length):
			# Demosaic the raw image into four polarization channels (0, 45, 90, 135 degrees)
			# The 'pa.COLOR_PolarRGB' option handles the combined RGGB-polarization filter array.
			# The output is a set of 12 full-resolution images (R, G, B for each of the 4 angles).
			img_000_bgr, img_045_bgr, img_090_bgr, img_135_bgr = pa.demosaicing(image_data[i1,:,:], pa.COLOR_PolarRGB) 	
			# Calculate the Stokes vector per-pixel
			image_list_bgr = [img_000_bgr, img_045_bgr, img_090_bgr, img_135_bgr]
			image_list = np.sum(image_list_bgr,axis = 3)
			img_stokes_bgr = pa.calcStokes(image_list_bgr, angles) 	
			s0[i1,...] = np.squeeze(img_stokes_bgr[...,0])
			s1[i1,...] = np.squeeze(img_stokes_bgr[...,1])
			s2[i1,...] = np.squeeze(img_stokes_bgr[...,2])
			gps_index = np.where((gpstime == image_time[i1]))[0]
			gps_lon[i1] = np.mean(gpslon[gps_index])
			gps_lat[i1] = np.mean(gpslat[gps_index])
			gps_alt[i1] = np.mean(gpsalt[gps_index])
			sun_pos = get_position(image_time[i1], gps_lon[i1], gps_lat[i1]) #Set position based on sun location
			pan[i1] = np.degrees(sun_pos['azimuth'])
			tilt[i1] = np.degrees(sun_pos['altitude']) 		
			
		s_bins = np.array(['time', 'H_pixel', 'V_pixel'])
		colors = ['blue', 'green', 'red']
		i_clr = 0
		for clr in colors:
			I = dataset.createVariable(f'I_{clr}', 'f4', s_bins, zlib = True, complevel = 9)# createVariable(name, datatype, dimensions_tuple)			
			I[:] = s0[...,i_clr]
			I.short_name = 'total intensity'
			I.units = 'DN'
			I.long_name = f'{colors[i_clr]} light intensity signal in digital number (DN)'
			I.ACVSNC_standard_name = f'Rad_Radiance_Remote_{colors[i_clr]}'   
			Q = dataset.createVariable(f'Q_{clr}', 'f4', s_bins, zlib = True, complevel = 9)# createVariable(name, datatype, dimensions_tuple)			
			Q[:] = s1[...,i_clr]
			Q.short_name = 'horizontal-vertical intensity'
			Q.units = 'DN'
			Q.long_name = f'{colors[i_clr]} horizontal/vertical linear polarization'
			Q.ACVSNC_standard_name = 'none' 
			U = dataset.createVariable(f'U_{clr}', 'f4', s_bins, zlib = True, complevel = 9)# createVariable(name, datatype, dimensions_tuple)						
			U[:] = s2[...,i_clr]
			U.short_name = 'diagonal intensity'
			U.units = 'DN'
			U.long_name = f'{colors[i_clr]} +/-45 degree linear polarization'
			U.ACVSNC_standard_name = 'none'
			i_clr += 1
		SA = dataset.createVariable('solar_azimuth', 'f4', s_bins, zlib = True, complevel = 9)# createVariable(name, datatype, dimensions_tuple)						
		SA[:] = pan
		SA.short_name = 'solar azimuth angle'
		SA.units = 'degrees'
		SA.long_name = 'Solar azimuth angle associated with sample position and time'
		SA.ACVSNC_standard_name = 'none'
		SA2 = dataset.createVariable('solar_altitude', 'f4', s_bins, zlib = True, complevel = 9)# createVariable(name, datatype, dimensions_tuple)						
		SA2[:] = pan
		SA2.short_name = 'solar altitude'
		SA2.units = 'degrees'
		SA2.long_name = 'Solar azimuth angle associated with sample position and time'
		SA2.ACVSNC_standard_name = 'none'
		lon = dataset.createVariable('GPS_longitude', 'f4', s_bins, zlib = True, complevel = 9)# createVariable(name, datatype, dimensions_tuple)						
		lon[:] = gps_lon
		lon.short_name = 'longitude'
		lon.units = 'degrees'
		lon.long_name = 'sample longitude derived from GPS in degrees W'
		lon.ACVSNC_standard_name = 'none'
		lat = dataset.createVariable('GPS_latitude', 'f4', s_bins, zlib = True, complevel = 9)# createVariable(name, datatype, dimensions_tuple)						
		lat[:] = gps_lat
		lat.short_name = 'latitude'
		lat.units = 'degrees'
		lat.long_name = 'sample latitude derived from GPS in degrees N'
		lat.ACVSNC_standard_name = 'none'
		alt = dataset.createVariable('GPS_altitude', 'f4', s_bins, zlib = True, complevel = 9)# createVariable(name, datatype, dimensions_tuple)						
		alt[:] = gps_alt
		alt.short_name = 'altitude'
		alt.units = 'm'
		alt.long_name = 'sample altitude in MASL'
		alt.ACVSNC_standard_name = 'none'
