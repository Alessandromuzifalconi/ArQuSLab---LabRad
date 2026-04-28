# -*- coding: utf-8 -*-
"""
Created on Fri Jan 28 12:04:27 2022

@author: ARQUSLAB1
"""
import matplotlib.pyplot as plt
import cv2 
plt.rcParams.update({'font.size':18})

# Pylablib library for interfacing with devices:
#    https://pypi.org/project/pylablib/
# Cameras control:
# https://pylablib.readthedocs.io/en/latest/devices/cameras_basics.html#cameras-basicspi

# Thorlabs DC
# https://pylablib.readthedocs.io/en/latest/devices/uc480.html#cameras-uc480

from pylablib.devices import Thorlabs

# Get list of all connected cameras
Cameras_list = Thorlabs.list_cameras_tlcam()

Thorlabs_cam = Thorlabs.ThorlabsTLCamera(serial='20842')
# Set exposure (exposure time in seconds)
Thorlabs_cam.set_trigger_mode('ext')
Thorlabs_cam.setup_ext_trigger('rise')
Thorlabs_cam.set_gain(20)
Thorlabs_cam.set_exposure(20*10**-3) # in seconds
Thorlabs_cam.start_acquisition(frames_per_trigger=1)
i = 1
format = 'tif'
dirname = 'C:/Users/ARQUSLAB-ADMIN.DESKTOP-IIQDMVF/Desktop/prova/'
while True:
    print('Waiting for frame...')
    Thorlabs_cam.wait_for_frame()
    frame = Thorlabs_cam.read_oldest_image()
    name = f'My_image{i}'
    cv2.imwrite(dirname+name+'.'+format, frame)
    print('Saved an image')
    i+=1