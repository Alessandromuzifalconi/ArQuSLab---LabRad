from genericpath import isdir
import DCAM.dcam as dcam 

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


# def readout_port_2_int (port):
#     """
#     Convert string of readout port to integer for telling the camera
#     """
#     return {'Sensitivity':0, 'Speed':1, 'Dynamic Range':2, 'Sub-Electron':3}[port]

# SENSOR_SIZE = 2400


class orca_camera_server (LabradServer):
    name = "Orca_camera"    
    last_image = None

    def initServer(self,serial_number = '000549'):  # Do initialization here
        self.timeout = 5000*20

        global dcamAPI
        import DCAM.dcam as dcamAPI  
        
        # Dictionary with all available properties names and their property IDs
        self.propList = {}
        print('Initialize DCAM API ...')
        if dcamAPI.Dcamapi.init() is False:
            msg = 'Dcamapi.init() fails with error {}'.format(dcamAPI.DCAMERR(dcamAPI.Dcamapi.lasterr()).name)
            dcamAPI.Dcamapi.uninit()
            raise RuntimeError(msg)        
        

        self._camera = dcamAPI.Dcam(0) # connect to first available camera; for many cameras you should iterate on i = 0
        print('Connected to camera:')
        print(f'Camera model: {self._camera.dev_getstring(dcamAPI.DCAM_IDSTR.MODEL)}')
        print(f'Camera {self._camera.dev_getstring(dcamAPI.DCAM_IDSTR.CAMERAID)}')
        if self._camera.dev_open():
            idprop = self._camera.prop_getnextid(0)
            while idprop is not False:
                output = '0x{:08X}: '.format(idprop)
                propname = self._camera.prop_getname(idprop)
                
                if propname is not False:
                    self.propList[propname]=output
                idprop = self._camera.prop_getnextid(idprop)
        self._queue = None

        # propID = dcamAPI.DCAM_IDPROP.__getattr__('DCAM_PIXELTYPE').value
        # print(f"Camera {self._camera.get_attribute('DCAM_PIXELTYPE')}")



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
    def get_attribute(self, c, name):
        """Return current values dictionary of attribute of the given name.
        Args:
            name (str): Property name to read
            
        Returns:
            dict: Dictionary of property values with structure as defined in
                :obj:`set_attribute`.
        """
        try:
            propID = dcamAPI.DCAM_IDPROP.__getattr__(name).value
            value = yield self._camera.prop_getvalue(propID)
            return value
        except Exception as e:
            # Add some info to the exception:
            raise Exception(f"Failed to get attribute {name}") from e
    
    @setting(2, 'set attribute')
    def set_attribute(self, c, name, value):
        """Sets all attribues in attr_dict.          
        Args:
            attr_dict (dict): dictionary of property dictionaries to set for the camera.
        """
        try:
            propID = dcamAPI.DCAM_IDPROP.__getattr__(name).value
            self._camera.prop_setvalue(propID,value)
            print("Set Attribute: ", name ," with ID: ", propID, " to value: ", value)
        except:
            print(f'Attribute {name} could not be set to value: {value}')
        return value
    
    @setting(3, 'get frame', returns = '*2w')
    def get_frame(self,c):
        """Acquire a single image and return it
        
        Returns:
            numpy.array: Acquired image
        # """
        self._camera.buf_alloc(nFrame=1) # allocate 1 frame in the buffer
        self._camera.cap_snapshot() # capture the image

        if self._camera.wait_capevent_frameready(self.timeout) is not False:
            img = yield self._camera.buf_getlastframedata()
        else:
            dcamerr = dcamAPI.Dcamapi.lasterr()
            if dcamerr.is_timeout():
                print('===: timeout')
            else:
                msg='Dcam.wait() fails with error {}'.format(dcamAPI.DCAMERR(dcamerr).name)
                raise RuntimeError(msg)
        self._camera.cap_stop()  # Andre's implementation#otherwise cannot realease buffer?? Boh (Ale)
        self._camera.buf_release()
        print(f'Got a {img.shape} image')
        return img.astype(np.uint32)
    
    @setting(4,'get sequence',returns = '*3w')
    def get_sequence(self, c, frames_number):
        """
        Returns sequence of frames as array 
        """
        images = []
        self._camera.buf_alloc(nFrame=frames_number) # allocate frames in the buffer
        self._camera.cap_snapshot()
        for img_n in range(frames_number):
            if self._camera.wait_capevent_frameready(self.timeout):
                image = yield self._camera.buf_getframedata(img_n)
            else:
                dcamerr = dcamAPI.Dcamapi.lasterr()
                if dcamerr.is_timeout():
                    raise RuntimeError('===: timeout')
                else:
                    msg='Dcam.wait() fails with error {}'.format(dcamAPI.DCAMERR(dcamerr).name)
                    raise RuntimeError(msg)
            images.append(image)
        # print(np.asarray(images).shape)                  
        self._camera.cap_stop()  # Andre's implementation#otherwise cannot realease buffer?? Boh (Ale)
        self._camera.buf_release()
        # print(f"Got {len(images)} of {frames_number} images.")
        returnValue(np.asarray(images).astype(np.uint32))
    
  
    @setting(5,'open camera', returns='s')
    def open_camera(self,c):
        self._camera.dev_open()
        msg = yield 'Camera opened'
        print(msg)
        returnValue(msg)

    @setting(6,'close camera', returns='s')
    def close_camera(self,c):
        self._camera.dev_close()
        msg = yield 'Camera closed'
        print(msg)
        returnValue(msg)

    def abort_acquisition(self):
        """Sets :obj:`_abort_acquisition` flag to break buffered acquisition loop."""
        self._abort_acquisition = True

        # # stack = yield self._device.get_sequence(num_frames=frames_number,exp_time = int(self._device.exp_time))
        # returnValue (stack.astype(np.uint32))

__server__ = orca_camera_server()
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)


