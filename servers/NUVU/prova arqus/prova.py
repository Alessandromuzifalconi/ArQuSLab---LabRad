import numpy as np
import h5py
from ctypes import *
import ctypes
from nuvu_cam_wrapper1 import Nuvu_cam_wrapper
import matplotlib.pyplot as plt


cam=Nuvu_cam_wrapper()


cam.setCalibratedEmGain(50)
cam.getCalibratedEmGain(1)
print(cam.calibratedEmGain.value)

frames_number=1

images = []
cam.setShutterMode(1)
cam.camStart(frames_number)
for i in range(frames_number):
    cam.name = 'image_{i}' 
    cam.read()
    cam.saveImage(0)

cam.setShutterMode(2)


cam.getSize()

buf_type = ctypes.c_uint16 * (cam.width.value * cam.height.value)
buffer_ptr = ctypes.cast(cam.ncImage, ctypes.POINTER(buf_type))

image_array = np.ctypeslib.as_array(buffer_ptr.contents)

image_array = image_array.reshape((cam.height.value, cam.width.value))

plt.imshow(image_array, cmap='gray')
plt.show()

print(cam.height.value,cam.width.value)

cam.closeCam()