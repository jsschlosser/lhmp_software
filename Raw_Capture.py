from arena_api.system import system
import os
import time
from pathlib import Path
import cv2 
import numpy as np 
import time
import datetime
import IMU_read_v2
ser = IMU_read_v2.ser
from zoneinfo import ZoneInfo
import raw_data_file_gen_v2
genfile = raw_data_file_gen_v2.gen_file
adddata = raw_data_file_gen_v2.append_data
def Run(camera_settings):
    """
    Function for capturing samples with the LHMP.

    :param camera_settings: dictionary containing the gain and exposure time camera settings as well as the acquisition duration 
    :type camera_settings: numpy dictionary        
    :return: dictionary of raw image data in digital number along with the image metadata of exposure time (us), gain, acquisition time (UTC), sensor temperature (degC)
    :rtype: numpy dictionary
    """  
    
    devices = system.create_device()    
    #print(devices)
    image_data_list = [] # Store acquired images
    image_info_list = [] # Store acquired image meta info (Gain, Exposure Time, Acquisition Time, etc.,)

    if len(devices)>0:
        utc_now = datetime.datetime.now(ZoneInfo("UTC"))  
        today_utc_date = utc_now.date()             
        midnight_utc = datetime.datetime.combine(today_utc_date, datetime.time(0,0,0), tzinfo=ZoneInfo("UTC"))    

        #devices = system.create_device()
        device = system.select_device(devices)  

        tl_stream_nodemap = device.tl_stream_nodemap # Get device stream nodemap   
        tl_stream_nodemap['StreamAutoNegotiatePacketSize'].value = True # Enable stream auto negotiate packet size
        tl_stream_nodemap['StreamPacketResendEnable'].value = True # Enable stream packet resend
        
        device_nm = device.nodemap
        device_nm['BlackLevelRaw'].value = 0
        device_nm['GainAuto'].value = camera_settings['GainAuto']  #'Continuous'
        if device_nm['GainAuto'].value == 'Off':
            device_nm['GainRaw'].value = camera_settings['GainSetting']
        device_nm['ExposureAuto'] .value = camera_settings['ExposureAuto'] 
        if device_nm['ExposureAuto'] .value == 'Off':
            device_nm['ExposureTimeRaw'].value = camera_settings['ExposureTimeSetting']     

        # Get nodes ---------------------------------------------------------------
        nodes = device_nm.get_node(['Width', 'Height', 'PixelFormat']) 

        # Nodes
        nodes['Width'].value = nodes['Width'].max   

        height = nodes['Height']
        height.value = height.max   

        # Set pixel format (e.g., 'PolarizedDolp_BayerRG8', 'BayerRG8', etc.)
        nodes['PixelFormat'].value = camera_settings['PixelFormat']
        
        start_time = time.time()
        #print(f"Starting image acquisition for {camera_settings['acquisition_duration']} seconds...")
        #IMUdata = IMU10axis.run(10) # run IMU for 10 seconds
        #IMUdata = np.nanmean(IMUdata,axis=0)# take average IMU data
        i_count = 0
        output_dictionary = {}
        timedif = time.time() - start_time
        while timedif < camera_settings['acquisition_duration']: # Continuously fetch and process images
            timedif = time.time() - start_time
            with device.start_stream():
                RXdata = ser.read(1)#一个一个读
                RXdata = int(RXdata.hex(),16) #转成16进制显示
                IMU_read_v2.DueData(RXdata)
                IMUdata = np.hstack((IMU_read_v2.Angle,IMU_read_v2.baro))
                print(IMUdata)
                image_buffer = device.get_buffer()  # Optional args         

                """
                np.ctypeslib.as_array() detects that Buffer.pdata is (uint8, c_ubyte)
                type so it interprets each byte as an element.
                For 16Bit images Buffer.pdata must be cast to (uint16, c_ushort)
                using ctypes.cast(). After casting, np.ctypeslib.as_array() can
                interpret every two bytes as one array element (a pixel).
                """
                nparray_reshaped = np.ctypeslib.as_array(image_buffer.pdata,
                                                        (image_buffer.height,
                                                        image_buffer.width))        
                
                utc_now = datetime.datetime.now(ZoneInfo("UTC"))            

                # Calculate the time difference (timedelta)
                time_since_midnight = utc_now - midnight_utc                

                # Get the total number of seconds as a float
                seconds_after_midnight = time_since_midnight.total_seconds()

                gainvalue = device_nm['GainRaw'].value
                exposuretimevalue = device_nm['ExposureTimeRaw'].value 
                DeviceT = device_nm['DeviceTemperature'].value #
                outputdata = [exposuretimevalue, gainvalue, utc_now, seconds_after_midnight, DeviceT]
                outputdata = np.hstack((outputdata,IMUdata))
                
                image_data_list.append(nparray_reshaped.copy()) # Store the image data
                image_info_list.append(outputdata)
                
                output_dictionary['image_data_list'] = np.array(image_data_list)
                output_dictionary['image_info_list'] = np.array(image_info_list)
                if i_count == 0:
                    genfile(output_dictionary,camera_settings['output_filename'])
                    image_data_list = [] 
                    image_info_list = [] 
                elif timedif==camera_settings['acquisition_duration']-1:
                    adddata(output_dictionary,camera_settings['output_filename'])
                    image_data_list = [] 
                    image_info_list = [] 
                elif i_count-1 % camera_Settings['save_rate'] == 0:
                    adddata(output_dictionary,camera_settings['output_filename'])
                    image_data_list = [] 
                    image_info_list = [] 
                i_count +=1
                device.requeue_buffer(image_buffer)    

    #output_dictionary['image_orientation_list'] = np.array(IMUdata)


    #return output_dictionary
