from genericpath import isdir
from pyvcam import pvc 
from pyvcam.camera import Camera   

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet.defer import (inlineCallbacks, returnValue, Deferred,
                                    DeferredQueue)

from labrad.server import LabradServer, setting
import cv2
import msvcrt
import time


import numpy as np
import matplotlib.pyplot as plt
from labrad import units
import os


def readout_port_2_int (port):
    """
    Convert string of readout port to integer for telling the camera
    """
    return {'Sensitivity':0, 'Speed':1, 'Dynamic Range':2, 'Sub-Electron':3}[port]

SENSOR_SIZE = 2400


class pvcam_camera_server (LabradServer):
    name = "PVCAM_camera"    
    last_image = None

    def initServer(self):  # Do initialization here
        pvc.init_pvcam()                   # Initialize PVCAM 
        cam = next(Camera.detect_camera()) # Use generator to find first camera. 
        self._device = cam
        self._queue = None

    def start_worker(self):
        self._acquisition_data = None
        self._acquisition_listeners = []
        self._queue = DeferredQueue()

    def query(self, cmd, arg=None):
        deferred = Deferred()
        self._queue.put([cmd, arg, deferred])

    @inlineCallbacks
    def _validate_feature(self, feature_name, value):
        min_value, max_value = yield self.query(
            '{}_range'.format(feature_name))
    
    @setting(1, 'get attribute')
    def get_attr(self, c, attr):
        if attr == 'name':
            return self._device.name
        elif attr == 'temperature':
            temperature = yield self._device.temp
            return(temperature)
        elif attr == 'exposure_time':
            exp_time = yield self._device.exp_time
            return(exp_time)
        elif attr == 'trigger_mode':
            trig_set = yield self._device.exp_modes[self._device.exp_mode]
            return(trig_set)
        elif attr == 'readout_port':
            read_port = yield self._device.readout_port 
            return(read_port)
        elif attr == 'gain':
            gain = yield self._device.gain 
            return(gain)
        elif attr == 'expose_out_mode':
            gain = yield self._device.exp_out_mode 
            return(gain)
        else:
            print(f'Attribute {attr} not available to get')

    @setting(2, 'set attribute')
    def set_attr(self, c, attr, attr_value):
        if attr == 'temperature':
            self._device.temp_setpoint = attr_value
            temperature_setpoint = yield self._device.temp_setpoint
            return(temperature_setpoint)
        elif attr == 'exposure_time':
            self._device.exp_time = (attr_value)
            exp_time = yield self._device.exp_time
            return(exp_time)
        elif attr == 'trigger_mode':
            self._device.exp_mode = attr_value
            trig_set = yield self._device.exp_modes[self._device.exp_mode]
            return(trig_set)
        elif attr == 'readout_port':
            self._device.readout_port = readout_port_2_int(attr_value)
            read_port = yield self._device.readout_port 
            return(read_port)
        elif attr == 'gain':
            self._device.gain = attr_value
            gain = yield self._device.gain 
            return(gain)
        elif attr == 'roi':
            if len(attr_value) == 2:
                width, height = attr_value[0]
                center_x, center_y = attr_value[1]

                self._device.set_roi(s1 = center_x-width//2+1, p1 =  center_y-height//2+1, w =  width, h = height)
                msg = f'roi of size ({width} x {height}) centered in ({center_x}, {center_y})'
            else:
                self._device.reset_rois
                msg = 'Resets the ROI list to default, which is full frame'
            return(msg)
        elif attr == 'binning':
            bins = tuple(attr_value)
            self._device.binning = bins
            msg = f'binning of size {bins} (binning is applied after roi)'
            return(msg)
        elif attr == 'exposure_resolution':
            self._device.exp_res = attr_value
            msg = f'exposure res set to {attr_value} (0 = ms, 1 = us)'
            return(msg)
        elif attr == 'expose_out_mode':
            self._device.exp_out_mode = attr_value
            msg = f'expose out mode set to {attr_value}'
            return(msg)
        else:
            print(f'Attribute {attr} is a labscript attribute: it is not set by the server')

    @setting(3, 'get frame', returns = '*2w')
    def get_frame(self, c):
        """
        Returns instantaneous camera frame as array 
        """
        print('Waiting for trigger')
        img = yield self._device.get_frame(exp_time = int(self._device.exp_time))
        print(f'Got a {img.shape} image')
        returnValue(img.astype(np.uint32))

    @setting(4,'open camera', returns='s')
    def open_camera(self,c):
        self._device.open()
        msg = yield 'Camera opened'
        print(msg)
        returnValue(msg)

    @setting(5,'close camera', returns='s')
    def close_camera(self,c):
        self._device.abort()
        self._device.close()
        msg = yield 'Camera closed'
        print(msg)
        returnValue(msg)

    @setting(6,'abort acquisition', returns='s')
    def abort_acquisition(self,c):
        self._device.abort()
        msg = yield 'Acquisition aborted'
        print(msg)
        returnValue(msg)
   
    @setting(9,'get sequence', frames_number = 'w{frames_number}',returns = '*3w')
    def get_sequence(self, c = None, frames_number = 1):
        """
        Returns sequence of frames as array 
        """
        stack = yield self._device.get_sequence(num_frames=frames_number,exp_time = int(self._device.exp_time))
        returnValue (stack.astype(np.uint32))


__server__ = pvcam_camera_server()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
