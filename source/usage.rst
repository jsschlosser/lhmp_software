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

This section summarizes the steps required to setup the environment needed to run a GigE Vision (i.e., genicam) camera on a Raspberry Pi 4b. Here we use a Pheonix 5.0 Polarization camera (LUCID Vision Labs Inc., 2023) that is built around Sony's IMX250MYR CMOS.

Hardware Requirements
	1) Any GigE vision camera should work however it must be a GenICam compliant machine vision camera/device. 
		a) Power supply.
	
	2) Rasberry Pi 4b running Debian GNU/Linux 12 (bookworm) x64. Prefer remote connection with Raspberry Pi Connect. 
		a) Power supply.
	
	3) Ethernet Cable.

Setup Hardware
	a) Connect camera to Raspberry Pi via ethernet cable.

	b) Power Raspberry Pi.

Install ArenaSDK Software (ArenaSDK_v0.1.78_Linux_ARM64)
	.. note::

		Full details in 'README_ARM64.txt'


	a) Set jumbo frames
		.. code-block:: console

			$ sudo ip link set enp0s8 mtu 9000

	b) Set receive buffers
		.. code-block:: console

			$ sudo ethtool -g enp0s8
			$ sudo ethtool -G enp0s8 rx 4096

	c) Set socket buffer size
		.. code-block:: console

			$ sudo sh -c "echo 'net.core.rmem_default=33554432' >> /etc/sysctl.conf"
			$ sudo sh -c "echo 'net.core.rmem_max=33554432' >> /etc/sysctl.conf"
			$ sudo sysctl -p
		
	d) Reverse path filtering
		.. code-block:: console

			$ sudo sh -c "echo 'net.core.rmem_default=33554432' >> /etc/sysctl.conf"
			$ sudo sh -c "echo 'net.core.rmem_max=33554432' >> /etc/sysctl.conf"
			$ sudo sysctl -p

	e) Extract the tarball to your desired location:	
		.. code-block:: console

	   		$ tar -xvzf ArenaSDK_Linux_ARM64.tar.gz
	    
	f) Run the ArenaSDK_Linux_ARM64.conf file	
		.. code-block:: console

	   		$ cd ~/Documents/ArenaSDK_v0.1.78_Linux_ARM64/ArenaSDK_Linux_ARM64
	   		$ sudo sh Arena_SDK_ARM64.conf


Install arena api
	.. note::

		Full details in '~/arena_api-2.7.1-py3-none-any/README.txt'

	a) Setup virtual environment.
		.. code-block:: console
	
			$ python3 -m venv myvirtualenv

	b) Activate virtual environment.
		.. code-block:: console
	
			$ source ~/myvirtualenv/bin/activate

	d) Install standard openCV.
		.. code-block:: console
	
			$ pip install opencv-python

	c) Install arena api.
		.. code-block:: console

			$ cd arena_api-2.7.1-py3-none-any
			$ pip install arena_api-2.7.1-py3-none-any.whl
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
	a) Activate virtual environment.
		.. code-block:: console
	
			$ source ~/myvirtualenv/bin/activate

	b) Set appropriate directory with python scripts.
		.. code-block:: console
	
			$ cd ~/Documents

	c) Run desired python script.
		.. code-block:: console
	
			$ python3
			$ import TestSample
			$ TestSample.Run()


Instructions for building sphinx documentation locally
------------------------------------------------------

This section describes how to build the sphinx documentation locally. 


	a) Activate virtual environment.
		.. code-block:: console

			$ source ~/myvirtualenv/bin/activate


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


.. autofunction:: Raw_Capture.Run


.. autofunction:: raw_data_file_gen.Run


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