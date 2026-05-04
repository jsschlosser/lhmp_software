import os
import numpy as np
import polanalyser as pa
from netCDF4 import Dataset
import cv2
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
def demosaic_test():
	"""
	Function for demosaicing and visualizing DoLP, AoLP, intensity, and the Stoke's vector components.
  
	"""  

	pathto_raw_data_file = '../BayerRG8_test.nc'
	data = Dataset(pathto_raw_data_file,'r')
	data_dictionary = {}		 
	for key in data.variables.keys():
		vals = data.variables[key][:]
		print(key)
		data_dictionary[key] = vals#np.where(vals == '--', np.nan, vals)
	image_data = data_dictionary['Raw_Signal']
	dataset_length = len(image_data[:,0,0])
	h_pixel_length = len(image_data[0,:,0])
	v_pixel_length = len(image_data[0,0,:])
	angles = np.deg2rad([0, 45, 90, 135])
	for i1 in range(0,dataset_length):
		# Demosaic the raw image into four polarization channels (0, 45, 90, 135 degrees)
		# The 'pa.COLOR_PolarRGB' option handles the combined RGGB-polarization filter array.
		# The output is a set of 12 full-resolution images (R, G, B for each of the 4 angles).
		img_000_bgr, img_045_bgr, img_090_bgr, img_135_bgr = pa.demosaicing(image_data[i1,:,:], pa.COLOR_PolarRGB) 	
		# Calculate the Stokes vector per-pixel
		image_list_bgr = [img_000_bgr, img_045_bgr, img_090_bgr, img_135_bgr]
		image_list = np.sum(image_list_bgr,axis=3)
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
		q = s1/s0
		u = s2/s0

		norm_s0 = mcolors.Normalize(vmin=np.min(s0), vmax=np.max(s0))
		s0_vis = (norm_s0(s0)*255).astype('uint8')
		total_intensity_png_name = f'../LeveL_1_data/S0_total_{i1}.tiff'
		cv2.imwrite(total_intensity_png_name, s0_vis)

		norm_q = mcolors.Normalize(vmin=np.min(q), vmax=np.max(q))
		q_vis = (norm_q(q)*255).astype('uint8')
		q_png_name = f'../LeveL_1_data/q_total_{i1}.tiff'
		cv2.imwrite(q_png_name, q_vis)

		norm_u = mcolors.Normalize(vmin=np.min(u), vmax=np.max(u))
		u_vis = (norm_u(u)*255).astype('uint8')
		u_png_name = f'../LeveL_1_data/u_total_{i1}.tiff'
		cv2.imwrite(u_png_name, u_vis)

		norm_dolp = mcolors.Normalize(vmin=np.min(img_dolp_total), vmax=np.max(img_dolp_total))
		img_dolp_vis = (norm_dolp(img_dolp_total)*255).astype('uint8')
		DOLP_png_name = f'../LeveL_1_data/DOLP_total_{i1}.tiff'
		cv2.imwrite(DOLP_png_name, img_dolp_vis)

		norm_aolp = mcolors.Normalize(vmin=np.min(img_aolp_total), vmax=np.max(img_aolp_total))
		img_aolp_vis = (norm_aolp(img_aolp_total)*255).astype('uint8')
		AOLP_png_name = f'../LeveL_1_data/AOLP_total_{i1}.tiff'
		cv2.imwrite(AOLP_png_name, img_aolp_vis)

		
		DOLP_png_name = f'../LeveL_1_data/DOLP_color_{i1}.tiff'
		AOLP_png_name = f'../LeveL_1_data/AOLP_color_{i1}.tiff'
		img_dolp_vis = (img_dolp_bgr * 255).astype('uint8')
		img_aolp_vis =(img_aolp_bgr * 255).astype('uint8')
		cv2.imwrite(DOLP_png_name, img_dolp_vis)
		cv2.imwrite(AOLP_png_name, img_aolp_vis)
		for i2 in [0,1,2]:
			intensity_png_name = f'../LeveL_1_data/S{i2}_color_{i1}.tiff'
			stks = img_stokes_bgr[:,:,:,i2]
			norm_stokes = mcolors.Normalize(vmin=np.min(stks), vmax=np.max(stks))
			img_stokes_vis = (norm_stokes(stks)*255).astype('uint8')
			cv2.imwrite(intensity_png_name, img_stokes_vis)

def standard_test():
	"""
	Function for visualizing standard polarizer DoLP and AoLP.
  
	""" 

	pathto_raw_data_file = '../PolarizedDolp_BayerRG8_test.nc'
	data = Dataset(pathto_raw_data_file,'r')
	data_dictionary = {}		 
	for key in data.variables.keys():
		vals = data.variables[key][:]
		print(key)
		data_dictionary[key] = vals#np.where(vals == '--', np.nan, vals)
	image_data = data_dictionary['Raw_Signal']
	dataset_length = len(image_data[:,0,0])
	h_pixel_length = len(image_data[0,:,0])
	v_pixel_length = len(image_data[0,0,:])
	angles = np.deg2rad([0, 45, 90, 135])
	for i1 in range(0,dataset_length):
		DOLP_png_name = f'../LeveL_1_data/DOLP_standard_{i1}.tiff'
		dolp_mono = np.squeeze(image_data[i1,:,:])
		norm_dolp = mcolors.Normalize(vmin=np.min(dolp_mono), vmax=np.max(dolp_mono))
		img_dolp_vis = (norm_dolp(dolp_mono)*255).astype('uint8')

		#img_dolp_vis = pa.applyColorToDoP(dolp_mono) 
		cv2.imwrite(DOLP_png_name, img_dolp_vis)

	pathto_raw_data_file = '../PolarizedAolp_BayerRG8_test.nc'
	data = Dataset(pathto_raw_data_file,'r')
	data_dictionary = {}		 
	for key in data.variables.keys():
		vals = data.variables[key][:]
		print(key)
		data_dictionary[key] = vals#np.where(vals == '--', np.nan, vals)
	image_data = data_dictionary['Raw_Signal']
	dataset_length = len(image_data[:,0,0])
	h_pixel_length = len(image_data[0,:,0])
	v_pixel_length = len(image_data[0,0,:])
	angles = np.deg2rad([0, 45, 90, 135])
	for i1 in range(0,dataset_length):
		AOLP_png_name = f'../LeveL_1_data/AOLP_standard_{i1}.tiff'
		aolp_mono = np.squeeze(image_data[i1,:,:])
		norm_aolp = mcolors.Normalize(vmin=np.min(aolp_mono), vmax=np.max(aolp_mono))
		img_aolp_vis = (norm_aolp(aolp_mono)*255).astype('uint8')
		cv2.imwrite(AOLP_png_name, img_aolp_vis)