import data_capture
import cv2
import numpy as np 
from datetime import date

def run():
	"""
	Function for inputting camera settings and acquiring images from the LHMP. Writes output level 0 data to netCDF file for processing.	

	"""  
	camera_settings = {}
	camera_settings['acquisition_duration'] = 30 # seconds
	camera_settings['GainAuto'] = 'Off' #'Continuous' 'Off'
	camera_settings['ExposureAuto'] = 'Continuous'#'Continuous' 'Off'
	camera_settings['GainSetting'] = 0
	camera_settings['ExposureTimeSetting'] = 140000#5147373 # us
	camera_settings['sleep_time'] = 0.1 # seconds
	camera_settings['save_rate'] = 30 # seconds
	pxl_format_list = ['BayerRG8','PolarizedDolp_BayerRG8','PolarizedAolp_BayerRG8']
	formatted_date = date.today().isoformat()
	file_suffix = input("Enter filename suffix or leave empty to default to test: ")
	for pxl_frmt in pxl_format_list:
		camera_settings['PixelFormat'] = pxl_frmt
		print(f"Camera Settings: {camera_settings}")
		if file_suffix=="":
			camera_settings['output_filename'] = f'../lhmp_data/{camera_settings["PixelFormat"]}_{formatted_date}_test.nc'
		else:
			camera_settings['output_filename'] = f'../lhmp_data/{camera_settings["PixelFormat"]}_{formatted_date}_{file_suffix}.nc'
		data_capture.run(camera_settings)
