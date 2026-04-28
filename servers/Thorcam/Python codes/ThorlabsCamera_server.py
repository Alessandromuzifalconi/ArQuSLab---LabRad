# ArQuSLab <arquslab@units.it>, November 2023
"""
### BEGIN NODE INFO
[info]
name = thorlabs_camera
version = 1.0
description = server for Thorlabs compact scientific cameras control

### END NODE INFO
"""

from twisted.internet import task
from twisted.internet import reactor
from twisted.internet.defer import (inlineCallbacks, returnValue, Deferred,
                                    DeferredQueue)

from labrad.server import LabradServer, setting

import cv2
import os
import time

from labrad import units
from pylablib.devices import Thorlabs

class thorlabs_camera_server(LabradServer):
    name = "thorlabs_camera"
    config = dict(
        exposure_time = 0.05 * units.s,
        gain = 7.0 *units.dB,
        trigger_mode='Edge Trigger',
        save_folder = '//ARQUS-CAM/Experiments/ytterbium174/',
        capture_mode = 0,
        save_enable = True,
        frames_number = 1)
    last_image = None

    # @inlineCallbacks
    def initServer(self):  # Do initialization here
        Cameras_list = Thorlabs.list_cameras_tlcam()
        #self._device = Thorlabs.ThorlabsTLCamera(serial=Cameras_list[0])
        self._queue = None
        print('Camera open')
        self.read_config(filename = '//ARQUS-NAS/ArQuS Shared/Parts/Cameras/Thorcam/Python codes/initialization/ThorCam_ini.txt') 
        #self.set_config()
      

    def read_config (self,filename = '//ARQUS-NAS/ArQuS Shared/Parts/Cameras/Thorcam/Python codes/initialization/ThorCam_ini.txt'):
        # Reads  configuration from file and stores information in self.config dictionary
        with open (filename, 'r') as ini_file:
            lines = ini_file.readlines()
            ini_file.close()
        exposure_time = float(lines[0][15:-1])
        #trigger_mode = lines[2][14:-1]
        #readout_port  = lines[3][14:-1]
        #save_folder = lines[4][13:-1]
        #capture_mode = float(lines[5][14:-1])
        #frames_number= int(lines[6][15:-1])
        #save_enable = bool(int(lines[7][13:-1]))
        #self.config["id"] = self.get_name()
        self.config["exposure_time"] = exposure_time
        #self.config["trigger_mode"] = trigger_mode
        #self.config["readout_port"] = readout_port
        #self.config["save_folder"] = save_folder
        #self.config["capture_mode"] = capture_mode
        #self.config["frames_number"] = frames_number
        #self.config["save_enable"] = save_enable
        print('Camera configuration: ')
        #print(f'trigger mode: {self.config["trigger_mode"]},')
        print(f'exposure time: {self.config["exposure_time"]} ms,')
        print(f'save enabled: {self.config["save_enable"]},')
        if self.config["save_enable"]:
            print(f'images save folder: {self.config["save_folder"]}')
        if self.config["capture_mode"] == 0:
            print(f'capture mode {int(self.config["capture_mode"])}: take an individual image for every experimental shot')
        elif self.config["capture_mode"] == 1:
            print(f'capture mode {int(self.config["capture_mode"])}: take 2 images and compute optical density for every experimental shot')
        elif self.config["capture_mode"] == 2:
            print(f'capture mode {int(self.config["capture_mode"])}: take {self.config["frames_number"]} images and compute average')
    """
    def set_config (self):
        self.temperature_setpoint(temperature_setpoint= self.config["temperature_setpoint"] *units.degC)
        self.exposure_time(exp_time= self.config["exposure_time"] *units.ms)
        self.trigger_mode(trig_set = self.config["trigger_mode"])
        if self.config["readout_port"] == 'Sensitivity':
            readout_port = 0
        elif self.config["readout_port"] == 'Speed':
            readout_port = 1    
        elif self.config["readout_port"] == 'Dynamic Range':
            readout_port = 2   
        elif self.config["readout_port"] == 'Sub-Electron':
            readout_port = 3 
        else:
            raise Exception(f'Camera mode {self.config["readout_port"]} not in list ("Sensitivity", "Speed", "Dynamic Range", "Sub-Electron")')
        self.readout_port(readout_set = readout_port)
        print('Camera configured')
    """
    #print(f'Camera connected. Serial: {Cameras_list[0]}')

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

    @setting(1, 'exposure_time', duration='v[s]{duration}', returns='v[s]')
    def exposure_time(self, c, duration=None):
        """
        Returns or sets the exposure time.

        Note:
        Returns actual exposure time after setting it. This value can deviate
        from the set value due to the finite increment of the exposure time.
        """
        if duration is not None:
            duration = duration[units.s]
            exposure_time = yield self._device.set_exposure(duration) # in seconds
        else:
            exposure_time = yield self._device.get_exposure()
        returnValue(exposure_time * units.s)

    @setting(2, 'gain', gain='v[dB]{value}', returns='v[dB]')
    def gain(self, c, gain=None):
        """
        Returns or sets the analog gain.

        Note:
        Returns actual analog gain after setting it. This value can deviate
        from the set value due to the finite increment of the exposure time.
        """
        if gain is not None:
            gain = gain[units.dB]
            gain = yield self._device.set_gain(gain)
        else:
            gain = yield self._device.get_gain()
        returnValue(gain * units.dB)

    @setting(3, 'trigger_source', source='s{source}', returns=['s', '_'])
    def trigger_source(self, c, source=None):
        """
        Returns or sets the trigger source ("int", "ext" or "bulb")
        """
        if source is None:
            trigger_source = yield self._device.get_trigger_mode()
            if trigger_source == 'int':
                returnValue('internal')
            elif trigger_source == 'ext':
                returnValue('external')
            elif trigger_source == 'bulb':
                returnValue('bulb')
            else:
                raise ValueError('Unknown trigger source returned by camera '
                                 '"{}"'.format(trigger_source))
        else:
            trigger_source = yield self._device.set_trigger_mode(source)
            returnValue(trigger_source)

    @setting(4, 'trigger_polarity', polarity='s{polarity}', returns=['s', '_'])
    def trigger_polarity(self, c, polarity=None):
        """
        Returns or sets external trigger polarity ("rise" or "fall")
        """
        if polarity is None:
            trigger_polarity = yield self._device.get_ext_trigger_parameters()
            if trigger_polarity == 'rise':
                returnValue('rising')
            elif trigger_polarity == 'fall':
                returnValue('falling')
            else:
                raise ValueError('Unknown trigger polarity returned by camera '
                                 '"{}"'.format(trigger_polarity))
        else:
            trigger_polarity = yield self._device.setup_ext_trigger(polarity)
            returnValue(trigger_polarity)

    @setting(5, 'frame_grab', dirname='s{name}',name='s{name}', fmt='s{format}')
    def frame_grab(self, c, dirname=None, name=None, fmt=None):
        """
        Waits for an external trigger, grabs and saves a single image 
        """
        full_dirname = dirname+"/"+time.strftime("%Y")+"/"+time.strftime("%m")+"/"+time.strftime("%d")+"/"
        if os.path.exists(full_dirname) is False:
            print('Creating folder')
            os.makedirs(full_dirname)
        
        i=1
        while True:
            self._device.start_acquisition(frames_per_trigger=1)
            print('Waiting for trigger...')
            self._device.wait_for_frame()
            frame = self._device.read_oldest_image()
            #cv2.imwrite(full_dirname+'/'+name+'_'+time.strftime("%H")+'_'+time.strftime("%M")+'_'+time.strftime("%S")+'.'+fmt, frame)
            cv2.imwrite(full_dirname+'/'+name+'_'+i+'.'+fmt, frame)
            print('Image '+ name+'_'+time.strftime("%H")+'_'+time.strftime("%M")+'_'+time.strftime("%S")+'.'+fmt+' saved')
            i+=1


__server__ = thorlabs_camera_server()
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
