import data_capture
import cv2
import numpy as np 
from datetime import date

def dark_current():
	"""
	Function for capturing a set of dark current measurements by running this on starup with the instrument with the lense cap on.

	
	"""  
	formatted_date = date.today().isoformat()
	camera_settings = {}
	camera_settings['acquisition_duration'] = 600
	camera_settings['GainAuto'] = 'Off' #'Continuous' #'Off'
	camera_settings['ExposureAuto'] = 'Off'#'Off'
	camera_settings['GainSetting'] = 0
	camera_settings['ExposureTimeSetting'] = 150000#5147373
	camera_settings['sleep_time'] = 0.25
	camera_settings['PixelFormat'] = 'BayerRG8'
	camera_settings['save_rate'] = 30 # seconds
	print(f"Camera Settings: {camera_settings}")
	camera_settings['output_filename'] = f'../lhmp_data/dark_current_cal_data_{formatted_date}.nc'
	output_dictionary = data_capture.run(camera_settings)


def dark_read():
	"""
	Function for capturing a set of dark read measurements by varying expsure time after running the dark_current routine. 
	
	"""  
	formatted_date = date.today().isoformat()
	output_dictionary = {}   
	output_dictionary['image_data_list'] = None
	output_dictionary['image_info_list'] = None
	camera_settings = {}
	camera_settings['acquisition_duration'] = 1000
	camera_settings['sleep_time'] = 0.5
	camera_settings['GainAuto'] = 'Off' #'Continuous' #'Off'
	camera_settings['ExposureAuto'] = 'Off'#'Off'
	camera_settings['GainSetting'] = 0
	camera_settings['PixelFormat'] = 'BayerRG8'
	camera_settings['save_rate'] = 30 # seconds
	for i1 in np.logspace(np.log10(10000),np.log10(150000),25):
		camera_settings['ExposureTimeSetting'] = int(i1)#5147373
		#print(f"Camera Settings: {camera_settings}")
		camera_settings['output_filename'] = f'../lhmp_data/dark_read_cal_data_{int(i1/1000)}ms_{formatted_date}.nc'
		OP_dict = data_capture.run(camera_settings)

