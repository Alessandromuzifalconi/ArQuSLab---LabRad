import labrad
from labrad import units
import os

#connecting to labrad
cxn = labrad.connect()
cam = cxn.thorlabs_camera

print(cam.exposure_time(25*units.ms))
print(cam.gain(20.0*units.dB))
print(cam.trigger_source('ext'))
print(cam.trigger_polarity('rise'))
cam.frame_grab('C:/Users/ARQUSLAB-ADMIN.DESKTOP-IIQDMVF/Desktop/ImageServerTests', 'test_image', 'tif')

