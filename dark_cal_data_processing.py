import numpy as np 
from netCDF4 import Dataset
import matplotlib as mpl
import matplotlib.pyplot as plt
from pylab import rcParams
import os
import sys

def DarkCurrent(pathto_raw_dark_cal_data=None):
	"""
	Takes LHMP dark measurements (in DN) and plots them against temparature. Requires numpy, matplotlib, and pylab.

	:param pathto_raw_dark_cal_data: Path to dark calibration dataset.
	:type pathto_raw_dark_cal_data: string		

	"""	

	# set path to data file in netCDF format and read in to python dictionary.
	pathto_raw_dark_cal_data = '../DarkCurrent.nc'
	dark_cal_data = Dataset(pathto_raw_dark_cal_data,'r')
	dark_cal_data_dictionary = {}
	for key in dark_cal_data.variables.keys():
		print(key)
		vals = dark_cal_data.variables[key][:]
		dark_cal_data_dictionary[key] = vals# np.where(vals == '--', np.nan, vals)#vals#

	image_data = dark_cal_data_dictionary['Raw_Signal'] # sensor data to be processed and plotted
	sensor_temp = dark_cal_data_dictionary['Detector_Temperature'] # sensor temperature to be processed and plotted
	Img_Data = image_data.reshape(len(sensor_temp),-1) # reformat pixelated sensor data to be visualized against temperature
	#print(image_data[image_data>0])
	#time_avgd_data = np.mean(image_data,axis=(1,2))
	#time_stdv_data = np.std(image_data,axis=(1,2))

	# set plot visualization parameters.
	fs =14
	lw = 1.5	
	plt.rcParams.update({'font.size': fs})
	plt.rcParams['font.family'] = 'serif'
	plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']#	
	rcParams['figure.figsize'] = 5, 3 # W, H
	fig,ax2=plt.subplots(1) # create figure and subplot
	# plot sensor data of each pixel against temperature for each time step.
	for i in range(len(sensor_temp)):
		y = Img_Data[i,:]
		x = np.squeeze(sensor_temp[i]*np.ones((1,len(Img_Data[i,:]))))
		ax2.scatter(x[y>0],y[y>0])
	#ax2.errorbar(sensor_temp,time_avgd_data, yerr=time_stdv_data, linestyle='none', elinewidth=1.5, ecolor='k', zorder=0, capsize=3.5)
	#ax2.plot(sensor_temp,time_avgd_data,marker='o', color='r', linestyle='none', markeredgewidth=1.5, markersize=7.5, markeredgecolor='k', zorder=1)

	ax2.set_xlabel(r"Sensor Temperature ($\degree$C)")
	ax2.set_ylabel(r"Sensor Signal (DN)")
	ax2.set_ylim(np.nanmax(Img_Data)-0.1,np.nanmax(Img_Data)+0.1)
	plt.tight_layout()
	plt.savefig(f"../DarkCal/DarkCurrent_plt.jpg", dpi=300)
	plt.close() # 

def dark_read(pathto_raw_dark_cal_data=None):
	"""
	Takes LHMP dark measurements (DN) and plots them against exposure time (us). Requires numpy, matplotlib, and pylab.

	:param pathto_raw_dark_cal_data: Path to dark calibration dataset.
	:type pathto_raw_dark_cal_data: string		

	"""	

	# set path to data file in netCDF format and read in to python dictionary.
	pathto_raw_dark_cal_data = '../DarkRead.nc'
	dark_cal_data = Dataset(pathto_raw_dark_cal_data,'r')
	dark_cal_data_dictionary = {}
	for key in dark_cal_data.variables.keys():
		vals = dark_cal_data.variables[key][:]
		dark_cal_data_dictionary[key] = vals#np.where(vals == '--', np.nan, vals)#vals#

	image_data = dark_cal_data_dictionary['Raw_Signal'] # sensor data to be processed and plotted
	sensor_et = dark_cal_data_dictionary['Detector_Exposure_Time'] # sensor temperature to be processed and plotted
	Img_Data = image_data.reshape(len(sensor_et),-1) # reformat pixelated sensor data to be visualized against temperature
	#print(image_data[image_data>0])
	#time_avgd_data = np.mean(image_data,axis=(1,2))
	#time_stdv_data = np.std(image_data,axis=(1,2))

	# set plot visualization parameters.
	fs =14
	lw = 1.5	
	plt.rcParams.update({'font.size': fs})
	plt.rcParams['font.family'] = 'serif'
	plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']#	
	rcParams['figure.figsize'] = 5, 3 # W, H
	fig,ax2=plt.subplots(1) # create figure and subplot

	# plot sensor data of each pixel against temperature for each time step.
	for i in range(len(sensor_et)):
		y = Img_Data[i,:]
		x = np.squeeze(sensor_et[i]*np.ones((1,len(Img_Data[i,:]))))*10**(-6)
		ax2.scatter(x[y>0],y[y>0])
	#ax2.errorbar(sensor_temp,time_avgd_data, yerr=time_stdv_data, linestyle='none', elinewidth=1.5, ecolor='k', zorder=0, capsize=3.5)
	#ax2.plot(sensor_temp,time_avgd_data,marker='o', color='r', linestyle='none', markeredgewidth=1.5, markersize=7.5, markeredgecolor='k', zorder=1)

	ax2.set_xlabel(r"Exposure Time (second)")
	ax2.set_ylabel(r"Sensor Signal (DN)")
	ax2.set_ylim(np.nanmax(Img_Data)-0.1,np.nanmax(Img_Data)+0.1)
	plt.tight_layout()
	plt.savefig(f"../DarkCal/DarkRead_plt.jpg", dpi=300)
	plt.close() # 