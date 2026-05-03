import numpy as np 
from datetime import date
from datetime import time
from datetime import datetime
from zoneinfo import ZoneInfo
import nc_write_v2
ncwrite = nc_write_v2

def gen_file(raw_data_dict,output_filename):
	"""
	Function for capturing samples with the LHMP.

	:param raw_data_dict: raw image dictionary with ancillary data.
	:type raw_data_dict: numpy dictionary	 
	:param output_filename: user set output path/filename.
	:type output_filename: string   
	"""  

	OP_Dictionary = {}
	OP_Dictionary['VariableAttributes'] = {}
	OP_Dictionary['Dims'] = {}
	dims = {}
	GlobParams = {}

	raw_data = raw_data_dict['image_data_list']
	raw_info = raw_data_dict['image_info_list']
	DATE= raw_info[0,2].strftime("%Y-%m-%d") 
	print(DATE)
	GlobParams['conventions']='CF-1.9'
	GlobParams['data_product_group'] = 'derived'
	GlobParams['data_use_guideline'] = 'N/A'
	GlobParams['file_originator'] = 'Joseph Schlosser'
	GlobParams['file_originator_contact'] = 'joseph.schlosser@hamptonu.edu'
	GlobParams['flight_start_date'] = DATE
	GlobParams['format'] = 'NETCDF4'
	GlobParams['history'] = f'Raw (level 0) LHMP data'
	GlobParams['IdentifierProductDOI'] = 'TBD'
	GlobParams['institution'] = 'Hampton University'
	GlobParams['last_modified_date'] = datetime.today().strftime('%Y-%m-%d')
	GlobParams['ACVSNC_standard_name_URL'] = 'https://www-air.larc.nasa.gov/missions/etc/AtmosphericCompositionVariableStandardNames.pdf'
	GlobParams['ACVSNC_standard_name_version'] = '1.0'
	GlobParams['measurement_platform'] = 'LHMP'
	GlobParams['PI_contact'] = 'joseph.schlosser@hamptonu.edu'
	GlobParams['PI_name'] = 'Joseph Schlosser'
	GlobParams['platform_identifier'] = 'LHMP'
	GlobParams['ProcessingLevel'] = '0'
	GlobParams['project'] = 'Langley-Hampton Multispectral Polarimeter (LHMP)'
	GlobParams['references'] = 'TBD'
	GlobParams['source'] = 'Raw output data from LHMP'
	GlobParams['time_coverage_end'] =f' {raw_info[-1,2].strftime("%Y%m%dT%H%M%S-%f")} (UTC)'
	GlobParams['time_coverage_resolution'] = '1 second'
	GlobParams['time_coverage_start'] = f'{raw_info[0,2].strftime("%Y%m%dT%H%M%S-%f")} (UTC)'
	GlobParams['title'] = 'Level 0 LHMP output data'
	GlobParams['VersionID'] = f'R0'

	
	dims['time'] = None #len(raw_data[:,0,0])
	OP_Dictionary["time"] = raw_info[:,3].astype(int)
	OP_Dictionary['Dims']["time"] = 'time'
	OP_Dictionary['VariableAttributes']["time"] = {}
	OP_Dictionary['VariableAttributes']["time"]['short_name'] = 'time'
	OP_Dictionary['VariableAttributes']["time"]['units'] = f'seconds after {DATE} 00:00:00 UTC.'

	dims['H_pixel'] = len(raw_data[0,:,0])
	OP_Dictionary["H_pixel"] = np.arange(0,dims['H_pixel'])
	OP_Dictionary['VariableAttributes']["H_pixel"] = {}
	OP_Dictionary['Dims']["H_pixel"] = 'H_pixel'
	OP_Dictionary['VariableAttributes']["H_pixel"]['short_name'] = 'H_pixel'
	OP_Dictionary['VariableAttributes']["H_pixel"]['units'] = '1'
	OP_Dictionary['VariableAttributes']["H_pixel"]['long_name'] = f'Value corresponding to the physical horizontal pixel position with 0 being the left most column on the detector.'

	dims['V_pixel'] = len(raw_data[0,0,:])
	OP_Dictionary["V_pixel"] = np.arange(0,dims['V_pixel'])
	OP_Dictionary['VariableAttributes']["V_pixel"] = {}
	OP_Dictionary['Dims']["V_pixel"] = 'V_pixel'
	OP_Dictionary['VariableAttributes']["V_pixel"]['short_name'] = 'V_pixel'
	OP_Dictionary['VariableAttributes']["V_pixel"]['units'] = '1'
	OP_Dictionary['VariableAttributes']["V_pixel"]['long_name'] = f'Value corresponding to the physical vertical pixel position with 0 being the top most row on the detector.'

	OP_Dictionary["Detector_Exposure_Time"] = raw_info[:,0].astype(int)
	OP_Dictionary['Dims']['Detector_Exposure_Time'] = 'time'
	OP_Dictionary['VariableAttributes']["Detector_Exposure_Time"] = {}
	OP_Dictionary['VariableAttributes']["Detector_Exposure_Time"]['_FillValue'] = -1
	OP_Dictionary['VariableAttributes']["Detector_Exposure_Time"]['short_name'] = 'et'
	OP_Dictionary['VariableAttributes']["Detector_Exposure_Time"]['units'] = 'us'
	OP_Dictionary['VariableAttributes']["Detector_Exposure_Time"]['long_name'] = f'Exposure time associated with the LHPM data.'
	OP_Dictionary['VariableAttributes']["Detector_Exposure_Time"]['ACVSNC_standard_name'] = 'none'  

	OP_Dictionary["Detector_Gain"] = raw_info[:,1].astype(float)
	OP_Dictionary['Dims']['Detector_Gain'] = 'time'
	OP_Dictionary['VariableAttributes']["Detector_Gain"] = {}
	OP_Dictionary['VariableAttributes']["Detector_Gain"]['_FillValue'] = np.nan
	OP_Dictionary['VariableAttributes']["Detector_Gain"]['short_name'] = 'gain'
	OP_Dictionary['VariableAttributes']["Detector_Gain"]['units'] = 'dB'
	OP_Dictionary['VariableAttributes']["Detector_Gain"]['long_name'] = f'Gain associated with the LHPM data.'
	OP_Dictionary['VariableAttributes']["Detector_Gain"]['ACVSNC_standard_name'] = 'none'

	OP_Dictionary["Detector_Temperature"] = raw_info[:,4].astype(float)
	OP_Dictionary['Dims']['Detector_Temperature'] = 'time'
	OP_Dictionary['VariableAttributes']["Detector_Temperature"] = {}
	OP_Dictionary['VariableAttributes']["Detector_Temperature"]['_FillValue'] = np.nan
	OP_Dictionary['VariableAttributes']["Detector_Temperature"]['short_name'] = 'detector_T'
	OP_Dictionary['VariableAttributes']["Detector_Temperature"]['units'] = 'degC'
	OP_Dictionary['VariableAttributes']["Detector_Temperature"]['long_name'] = f'Temerature of the LHMP detector.'
	OP_Dictionary['VariableAttributes']["Detector_Temperature"]['ACVSNC_standard_name'] = 'none'  

	OP_Dictionary["pitch"] = raw_info[:,5].astype(float)
	OP_Dictionary['Dims']['pitch'] = 'time'
	OP_Dictionary['VariableAttributes']["pitch"] = {}
	OP_Dictionary['VariableAttributes']["pitch"]['_FillValue'] = np.nan
	OP_Dictionary['VariableAttributes']["pitch"]['short_name'] = 'pitch'
	OP_Dictionary['VariableAttributes']["pitch"]['units'] = 'degree'
	OP_Dictionary['VariableAttributes']["pitch"]['long_name'] = f'Corrected pitch derived from IMU.'
	OP_Dictionary['VariableAttributes']["pitch"]['ACVSNC_standard_name'] = 'none'  

	OP_Dictionary["roll"] = raw_info[:,6].astype(float)
	OP_Dictionary['Dims']['roll'] = 'time'
	OP_Dictionary['VariableAttributes']["roll"] = {}
	OP_Dictionary['VariableAttributes']["roll"]['_FillValue'] = np.nan
	OP_Dictionary['VariableAttributes']["roll"]['short_name'] = 'roll'
	OP_Dictionary['VariableAttributes']["roll"]['units'] = 'degree'
	OP_Dictionary['VariableAttributes']["roll"]['long_name'] = f'Corrected roll derived from IMU.'
	OP_Dictionary['VariableAttributes']["roll"]['ACVSNC_standard_name'] = 'none'  

	OP_Dictionary["heading"] = raw_info[:,7].astype(float)
	OP_Dictionary['Dims']['heading'] = 'time'
	OP_Dictionary['VariableAttributes']["heading"] = {}
	OP_Dictionary['VariableAttributes']["heading"]['_FillValue'] = np.nan
	OP_Dictionary['VariableAttributes']["heading"]['short_name'] = 'IMU_heading'
	OP_Dictionary['VariableAttributes']["heading"]['units'] = 'degree'
	OP_Dictionary['VariableAttributes']["heading"]['long_name'] = f'Heading derived from the IMU.'
	OP_Dictionary['VariableAttributes']["heading"]['ACVSNC_standard_name'] = 'none'  

	OP_Dictionary["IMU_Pressure"] = raw_info[:,8].astype(float)
	OP_Dictionary['Dims']['IMU_Pressure'] = 'time'
	OP_Dictionary['VariableAttributes']["IMU_Pressure"] = {}
	OP_Dictionary['VariableAttributes']["IMU_Pressure"]['_FillValue'] = np.nan
	OP_Dictionary['VariableAttributes']["IMU_Pressure"]['short_name'] = 'IMU_P'
	OP_Dictionary['VariableAttributes']["IMU_Pressure"]['units'] = 'Pa'
	OP_Dictionary['VariableAttributes']["IMU_Pressure"]['long_name'] = f'Air pressure measured by the IMU.'
	OP_Dictionary['VariableAttributes']["IMU_Pressure"]['ACVSNC_standard_name'] = 'none'  
	'''
	OP_Dictionary["IMU_Temperature"] = raw_info[:,9].astype(float)
	OP_Dictionary['Dims']['IMU_Temperature'] = 'time'
	OP_Dictionary['VariableAttributes']["IMU_Temperature"] = {}
	OP_Dictionary['VariableAttributes']["IMU_Temperature"]['_FillValue'] = np.nan
	OP_Dictionary['VariableAttributes']["IMU_Temperature"]['short_name'] = 'IMU_T'
	OP_Dictionary['VariableAttributes']["IMU_Temperature"]['units'] = 'degC'
	OP_Dictionary['VariableAttributes']["IMU_Temperature"]['long_name'] = f'Temerature of the IMU.'
	OP_Dictionary['VariableAttributes']["IMU_Temperature"]['ACVSNC_standard_name'] = 'none'  
	'''

	OP_Dictionary["IMU_Altitude"] = raw_info[:,9].astype(float)
	OP_Dictionary['Dims']['IMU_Altitude'] = 'time'
	OP_Dictionary['VariableAttributes']["IMU_Altitude"] = {}
	OP_Dictionary['VariableAttributes']["IMU_Altitude"]['_FillValue'] = np.nan
	OP_Dictionary['VariableAttributes']["IMU_Altitude"]['short_name'] = 'IMU_Alt'
	OP_Dictionary['VariableAttributes']["IMU_Altitude"]['units'] = 'm'
	OP_Dictionary['VariableAttributes']["IMU_Altitude"]['long_name'] = f'Temerature measured by the IMU.'
	OP_Dictionary['VariableAttributes']["IMU_Altitude"]['ACVSNC_standard_name'] = 'none'  

	OP_Dictionary["Raw_Signal"] = raw_data
	OP_Dictionary['Dims']['Raw_Signal'] = np.array(['time','H_pixel','V_pixel'])
	OP_Dictionary['VariableAttributes']["Raw_Signal"] = {}
	OP_Dictionary['VariableAttributes']["Raw_Signal"]['_FillValue'] = 0
	OP_Dictionary['VariableAttributes']["Raw_Signal"]['short_name'] = 'raw_signal'
	OP_Dictionary['VariableAttributes']["Raw_Signal"]['units'] = 'DN'
	OP_Dictionary['VariableAttributes']["Raw_Signal"]['long_name'] = 'Raw output from the LHMP detector.'
	OP_Dictionary['VariableAttributes']["Raw_Signal"]['ACVSNC_standard_name'] = 'none'  
	OP_Dictionary['VariableAttributes']["Raw_Signal"]['ancillary'] = 'et, gain, detector_T'
	
	ncwrite.Initiate(output_filename, OP_Dictionary, dims, GlobParams) 

def append_data(raw_data_dict,output_filename):

	raw_data = raw_data_dict['image_data_list']
	raw_info = raw_data_dict['image_info_list']
	OP_Dictionary = {}

	OP_Dictionary["time"] = raw_info[:,3].astype(int)
	OP_Dictionary["Detector_Exposure_Time"] = raw_info[:,0].astype(int)
	OP_Dictionary["Detector_Gain"] = raw_info[:,1].astype(float)
	OP_Dictionary["Detector_Temperature"] = raw_info[:,4].astype(float)
	OP_Dictionary["pitch"] = raw_info[:,5].astypraw_infoe(float)
	OP_Dictionary["roll"] = raw_info[:,6].astype(float)
	OP_Dictionary["heading"] = raw_info[:,7].astype(float)
	OP_Dictionary["IMU_Pressure"] = raw_info[:,8].astype(float)
	OP_Dictionary["IMU_Altitude"] = raw_info[:,9].astype(float)
	OP_Dictionary["Raw_Signal"] = raw_data
	ncwrite.write_to(output_filename, OP_Dictionary) 