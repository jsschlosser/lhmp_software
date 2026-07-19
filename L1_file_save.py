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

    shutil.copy(pathto_raw_data_file, pathto_L1_data_file)# 1. Copy the original file to the new destination ("Save As" workaround)
	gpsdate = desired_data_date.split("-")
	gpsdate = "".join(gpsdate)	
   	gpsfilename = [f for f in os.listdir(f'../gps_data/') if f.startswith(gpsdate)]
    GPS_data = NMEA_decode.Run(filename=gpsfilename, path_to_file='../gps_data')
   	with nc.Dataset(pathto_raw_data_file, 'a') as dataset:# 2. Open the newly copied file in append mode ('a') to modify it in place
   		image_data = data.variables['raw_data'][:]
   		image_time = data.variables['time'][:]
		dataset_length = len(image_time)
		print(dataset_length)
		h_pixel_length = len(image_data[0,:,0])
		v_pixel_length = len(image_data[0,0,:])
		print(h_pixel_length,v_pixel_length)
		angles = np.deg2rad([0, 45, 90, 135])
		for i1 in range(0,dataset_length):
			# Demosaic the raw image into four polarization channels (0, 45, 90, 135 degrees)
			# The 'pa.COLOR_PolarRGB' option handles the combined RGGB-polarization filter array.
			# The output is a set of 12 full-resolution images (R, G, B for each of the 4 angles).
			img_000_bgr, img_045_bgr, img_090_bgr, img_135_bgr = pa.demosaicing(image_data[i1,:,:], pa.COLOR_PolarRGB) 	
			# Calculate the Stokes vector per-pixel
			image_list_bgr = [img_000_bgr, img_045_bgr, img_090_bgr, img_135_bgr]
			image_list = np.sum(image_list_bgr,axis = 3)
			img_stokes_bgr = pa.calcStokes(image_list_bgr, angles) 	
			img_stokes_total = pa.calcStokes(image_list, angles) 	
			# Convert the Stokes vector to Intensity, DoLP and AoLP
			img_intensity_bgr = pa.cvtStokesToIntensity(img_stokes_bgr)
			img_dolp_bgr = pa.cvtStokesToDoLP(img_stokes_bgr)
			img_aolp_bgr = pa.cvtStokesToAoLP(img_stokes_bgr)	
			img_dolp_total = pa.cvtStokesToDoLP(img_stokes_total)
			img_aolp_total = pa.cvtStokesToAoLP(img_stokes_total)
			# The results (s0, dolp, aolp) are full-resolution images. s0 represents the total intensity (a normal color image).
			s0 = img_stokes_total[...,0]
			s1 = img_stokes_total[...,1]
			s2 = img_stokes_total[...,2]
			q = s1 / s0
			u = s2 / s0   

			gps_index = np.where(GPS_data['GGA']['time'] == image_time)
			sun_pos = get_position(image_time[i1], GPS_data['GGA']['longitude'], GPS_data['GGA']['latitude']) #Set position based on sun location
			pan = np.degrees(sun_pos['azimuth'])
			tilt = np.degrees(sun_pos['altitude']) 		




        dataset.setncattr('history', 'Modified on 2026-07-14: Added new_dimension and new_variable.')# 5. Update and add global attributes
        dataset.experiment_version = "v2.1"# You can use the setncattr method or direct assignment

        # 3. Add a new dimension
        # Checking if it exists first prevents errors if the script is run multiple times
        if 'new_dimension' not in dataset.dimensions:
            # createDimension(name, size). Use None for an unlimited dimension.
            dataset.createDimension('new_dimension', 10) 
            
        # 4. Add a new variable using the new dimension
        if 'new_variable' not in dataset.variables:
            # createVariable(name, datatype, dimensions_tuple)
            new_var = dataset.createVariable('new_variable', np.float32, ('new_dimension',))
            
            # Populate the variable with data
            new_var[:] = np.linspace(0, 100, 10, dtype=np.float32)
            
            # Optional: Add metadata (attributes) to the specific variable
            new_var.units = "degrees_celsius"
            new_var.description = "Example variable added via Python script."
            


