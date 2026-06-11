Usage
=====
Acknowledgements
----------------

LHMP is being developed in collaboration with NASA Langley Research Center and the Hampton University.


Copyright
---------

.. include:: ../LICENSE


Configuring the Raspberry Pi
----------------------------

This section summarizes the steps required to setup the environment needed to start collecting data with a Pheonix 5.0 Polarization camera (LUCID Vision Labs Inc., 2023) and a Raspberry Pi 5.

Hardware Requirements
	-A GigE vision polarization camera 
		.. note:: 

			Any should work however it must be a GenICam compliant machine vision camera/device

		a) 12V Power supply
		b) Ethernet cable

	-Rasberry Pi 5 running Debian (trixie) x64
		.. note::

			Prefer remote connection with Raspberry Pi Connect
		
		a) 3.3V Power supply or 12V-3.3V RPi HAT 

	-Yahboom IMU 10-Axis (CMP-10A)
		a) USB-C to USB-A cable

	-Yahboom GPS (ATGM336H-5N)
		a) 4 GPIO wires for I2C connection 
		b) External attena  

1) Install ArenaSDK Software (ArenaSDK_v#.#.#_Linux_ARM64)
	.. note::

		Full details in 'README_ARM64.txt'. Replace #.#.# with current version. 


	a) Set jumbo frames
		.. code-block:: console

			$ sudo ip link set eth0 mtu 9000

	b) Extract the tarball to your desired location:	
		.. code-block:: console

	   		$ tar -xvzf ArenaSDK_v#.#.#_Linux_ARM64.tar.gz
	    
	c) Run the ArenaSDK_Linux_ARM64.conf file:	
		.. code-block:: console

	   		$ cd ~/Documents/ArenaSDK_Linux_ARM64
	   		$ sudo sh Arena_SDK_ARM64.conf

2) Install HDF5 and netCDF4
	Install both HDF5 and netCDF4 repositories to handle data storage:
		.. code-block:: console

			$ sudo apt install libnetcdf-dev libhdf5-dev
			$ pip install netCDF4


3) Set Camera IP address and set IPv Settings
	a) Select Advanced Options under the 'Wirelss LAN' dropdown menu. 
	b) Navigate to 'IPv6 Settings' tab and set the 'Method' to 'Disabled'
	c) Navigate to 'IPv4 Settings' tab and set the 'Method' to 'Manual'
	d) While in 'IPv4 Settings', add the following IP address to the 'Address' list: 169.254.4.205 with a 'Netmask' of 16


4) Install arena api
	.. note::

		Full details in '~/arena_api-#.#.#-py3-none-any/README.txt'. Replace #.#.# with current version.

	a) Install standard openCV:
		.. code-block:: console
	
			$ pip install opencv-python

	b) Install arena api:
		.. code-block:: console

			$ cd ~/Documents/arena_api-#.#.#-py3-none-any
			$ pip install arena_api-#.#.#-py3-none-any.whl
			$ pip install -r examples/requirements_lin_arm64.txt
			$ sudo apt-get install python3-tk

5) Install GPS support
	.. note::

		Full details at 'https://ozzmaker.com/berrygps-setup-guide-raspberry-pi/'

	a) Disable the serial console and enable the serial port:
		.. code-block:: console

			$ sudo raspi-config

		i) Select "5. Inteferface options"
		ii) Select "No" to disable the serial console
		iii) Select "Yes" to enable the serial port

	e) Point RPi5 to the correct UART interface:
		.. code-block:: console

			$ sudo nano /boot/firmware/config.txt
			
		Add 'dtparam=uart0_console' to end of file, save, and exit

	f) Install GPSD services:
		.. code-block:: console

			$ sudo apt-get install gpsd-clients gpsd -y

	g) Point gpsd to correct device: '/dev/ttyUSB0'
		.. code-block:: console

			$ sudo nano /etc/default/gpsd

		Replace 'DEVICES=""' with 'DEVICES="/dev/ttyUSB0"'

	h) After install, collect GPS data using:
		.. code-block:: console
		
			$ gpspipe -r -d -l -o ~/GPS_Data/`date +"%Y%m%d-%H-%M-%S"`.nmea


	i) Install .nmea decoder.
		.. code-block:: console

			$ python3 -m pip install --upgrade pynmeagps
			

6) Install IMU support
	.. note::

		Full details at 'https://docs.circuitpython.org/projects/icm20x/en/latest/api.html#'

	a) pip3 install adafruit-circuitpython-icm20x --break-system-packages

Example of running and plotting data
------------------------------------

This section shows the steps required to collect test data from the LHMP replica and ensure instrument functionality. 

1) Set appropriate directory with python scripts:
	.. code-block:: console

		$ cd ~/Documents

2) Run sample python script:
	.. code-block:: console

		$ python3
		>>> import test_sample
		>>> test_sample.run()

c) Demosaic and plot test data:
	.. code-block:: console

		$ pip install polanalyser
		$ python3
		>>> import test_plot
		>>> test_plot.demosaic_test()
		>>> test_plot.standard_test()

Instructions for building sphinx documentation locally
------------------------------------------------------

This section describes how to build sphinx documentation locally. This is only required for the software updating workflow but is not required for strictly opperational LHMP replicas. 

	a) Install matplotlib:
		.. code-block:: console

			$ pip install matplotlib

	b) Install basic sphinx package:
		.. code-block:: console

			$ pip install sphinx

	c) Install html theme for sphinx:
		.. code-block:: console

			$ pip install sphinx_rtd_theme

	d) Install pdf builder for sphinx:
		.. code-block:: console

			$ pip install sphinx-simplepdf

	e) Build sphinx:
		.. code-block:: console

			$ sphinx-build -b html source docs

Test the instrument functionality 
---------------------------------

.. autofunction:: test_sample.run


.. autofunction:: test_sample.run


.. autofunction:: data_file_save.gen_file


.. autofunction:: data_file_save.append_data


.. autofunction:: test_plot.standard_test


.. autofunction:: test_plot.demosaic_test


.. autofunction:: nc_write.initiate


.. autofunction:: nc_write.append


.. automodule:: IMU_read
	:members:

Perform dark calibration measurements
-------------------------------------

.. autofunction:: dark_cal_data_collection.dark_current


.. autofunction:: dark_cal_data_collection.dark_read


Visualize dark calibration measurements
---------------------------------------

.. autofunction:: dark_cal_data_processing.dark_current


.. autofunction:: dark_cal_data_processing.dark_read


