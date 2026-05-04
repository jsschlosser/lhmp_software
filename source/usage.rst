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

This section summarizes the steps required to setup the environment needed to run a GigE Vision (i.e., genicam) camera on a Raspberry Pi 5. Here we use a Pheonix 5.0 Polarization camera (LUCID Vision Labs Inc., 2023) that is built around Sony's IMX250MYR CMOS.

Hardware Requirements
	1) Any GigE vision camera should work however it must be a GenICam compliant machine vision camera/device. 
		a) Power supply.
	
	2) Rasberry Pi 4b running Debian GNU/Linux 12 (bookworm) x64. Prefer remote connection with Raspberry Pi Connect. 
		a) Power supply.
	
	3) Ethernet Cable.


Install ArenaSDK Software (ArenaSDK_v0.1.78_Linux_ARM64)
	.. note::

		Full details in 'README_ARM64.txt'


	a) Set jumbo frames
		.. code-block:: console

			$ sudo ip link set eth0 mtu 9000


	e) Extract the tarball to your desired location:	
		.. code-block:: console

	   		$ tar -xvzf ArenaSDK_v#.#.#_Linux_ARM64.tar.gz
	    
	    .. note::

	   		replace #.#.# with current version.

	f) Run the ArenaSDK_Linux_ARM64.conf file	
		.. code-block:: console

	   		$ cd ~/Documents/ArenaSDK_Linux_ARM64
	   		$ sudo sh Arena_SDK_ARM64.conf

Install HDF5 and netCDF4

	.. code-block:: console

		$ sudo apt install libnetcdf-dev libhdf5-dev
		$ pip install netCDF4

Set Camera IP address and set IPv Settings

		Select Advanced Options under the 'Wirelss LAN' dropdown menu. 

		Navigate to 'IPv6 Settings' tab and set the 'Method' to 'Disabled'

		Navigate to 'IPv4 Settings' tab and set the 'Method' to 'Manual'

		While in 'IPv4 Settings', add the following IP address to the 'Address' list: 169.254.4.205 with a 'Netmask' of 16.


Install arena api
	.. note::

		Full details in '~/arena_api-#.#.#-py3-none-any/README.txt'. Replace #.#.# with current version.

	a) Install standard openCV.
		.. code-block:: console
	
			$ pip install opencv-python

	b) Install arena api.
		.. code-block:: console

			$ cd ~/Documents/arena_api-#.#.#-py3-none-any
			$ pip install arena_api-#.#.#-py3-none-any.whl
			$ pip install -r examples/requirements_lin_arm64.txt
			$ sudo apt-get install python3-tk

Install GPS support
	.. note::

		Full details at 'https://ozzmaker.com/berrygps-setup-guide-raspberry-pi/'

	a) Disable the serial console and enable the serial port.
		.. code-block:: console

			$ sudo raspi-config

		Select "5. Inteferface options".

		Select "No" to disable the serial console.

		Select "Yes" to enable the serial port.

	b) Point RPi5 to the correct UART interface '/dev/serial0'.
		.. code-block:: console

			$ sudo nano /boot/firmware/config.txt
			
		Add 'dtparam=uart0_console' to end of file, save, and exit.

	c) Install GPSD services.
		.. code-block:: console

			$ sudo apt-get install gpsd-clients gpsd -y
			$ sudo nano /etc/default/gpsd

		Replace 'DEVICES=”″' with 'DEVICES=”/dev/serial0″'

Run GPS service when collecting data
	.. code-block:: console
		
		gpspipe -r -d -l -o /home/pi/`date +”%Y%m%d-%H-%M-%S”`.nmea

Example of running programs in Arena api
-----------------------------------------

	b) Set appropriate directory with python scripts.
		.. code-block:: console
	
			$ cd ~/Documents

	c) Run desired python script.
		.. code-block:: console
	
			$ python3
			>>> import TestSample
			>>>  TestSample.Run()


Instructions for building sphinx documentation locally
------------------------------------------------------

This section describes how to build the sphinx documentation locally. 

	b) Install matplotlib.
		.. code-block:: console

			$ pip install matplotlib

	c) Install basic sphinx package.
		.. code-block:: console

			$ pip install sphinx

	d) Install html theme for sphinx.
		.. code-block:: console

			$ pip install sphinx_rtd_theme

	e) Install pdf builder for sphinx.
		.. code-block:: console

			$ pip install sphinx-simplepdf

	f) Build sphinx.
		.. code-block:: console

			$ sphinx-build -b html source docs

Test the instrument functionality 
---------------------------------

.. autofunction:: TestSample.Run


.. autofunction:: data_caputre.Run


.. autofunction:: data_file_save.Run


.. autofunction:: TestPlot.standard_test


.. autofunction:: TestPlot.demosaic_test

Perform dark calibration measurements
-------------------------------------

.. autofunction:: Dark_cal_data_collection.DarkCurrent


.. autofunction:: Dark_cal_data_collection.DarkRead

Visualize dark calibration measurements
---------------------------------------

.. autofunction:: Dark_cal_data_processing.DarkCurrent


.. autofunction:: Dark_cal_data_processing.DarkRead