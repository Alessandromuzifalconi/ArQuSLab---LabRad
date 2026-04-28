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
import msvcrt

from labrad import units
from pylablib.devices import Thorlabs

class thorlabs_camera_server(LabradServer):
    name = "thorlabs_camera"
    config = dict(
        exposure_time = 0.05 * units.s,
        gain = 7.0 *units.dB,
        trigger_source='ext',
        save_folder = '//ARQUS-CAM/Experiments/ytterbium174/',
        trigger_polarity = 'rise',
        capture_mode = 0,
        save_enable = True)
    last_image = None

    # @inlineCallbacks
    def initServer(self):  # Do initialization here
        Cameras_list = Thorlabs.list_cameras_tlcam()
        #self._device = Thorlabs.ThorlabsTLCamera(serial=Cameras_list[0])
        self._queue = None
        print('Camera open')
        self.read_config(filename = '//ARQUS-NAS/ArQuS Shared/Parts/Cameras/Thorcam/Python codes/initialization/ThorCam_ini.txt') 
        #self.set_config()
        #if self.config["capture_mode"] == 0:
        #    self.start_live()
      
    def read_config (self,filename = '//ARQUS-NAS/ArQuS Shared/Parts/Cameras/Thorcam/Python codes/initialization/ThorCam_ini.txt'):
        # Reads  configuration from file and stores information in self.config dictionary
        with open (filename, 'r') as ini_file:
            lines = ini_file.readlines()
            ini_file.close()
        exposure_time = float(lines[0][15:-2])
        gain  = lines[1][6:-4]
        trigger_source = lines[2][16:-1]
        save_folder = lines[3][13:-1]
        capture_mode = float(lines[4][14:-1])
        save_enable = bool(int(lines[5][13:-1]))

        self.config["exposure_time"] = exposure_time
        self.config["gain"] = gain
        self.config["trigger_source"] = trigger_source
        self.config["save_folder"] = save_folder
        self.config["capture_mode"] = capture_mode
        self.config["save_enable"] = save_enable

        print('Camera configuration: ')
        print(f'exposure time: {self.config["exposure_time"]} s,')
        print(f'gain: {self.config["gain"]} dB,')
        print(f'trigger source: {self.config["trigger_source"]},')
        print(f'save enabled: {self.config["save_enable"]},')
        if self.config["save_enable"]:
            print(f'images save folder: {self.config["save_folder"]}')
        if self.config["capture_mode"] == 0:
            print(f'capture mode {int(self.config["capture_mode"])}: take an individual image for every experimental shot')
        elif self.config["capture_mode"] == 1:
            print(f'capture mode {int(self.config["capture_mode"])}: take 2 images and compute optical density for every experimental shot')
        elif self.config["capture_mode"] == 2:
            print(f'capture mode {int(self.config["capture_mode"])}: take {self.config["frames_number"]} images and compute average')
    
    def set_config (self):
        self.exposure_time(exp_time= self.config["exposure_time"])
        self.gain(gain= self.config["gain"])
        self.trigger_source(source = self.config["trigger_source"])
        self.trigger_polarity(polarity =  self.config["trigger_polarity"])
        print('Camera configured')
    

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

    @setting(1, 'exposure_time', exp_time='v[s]{exp_time}', returns='v[s]')
    def exposure_time(self, c, exp_time=None):
        """
        Returns or sets the exposure time.

        Note:
        Returns actual exposure time after setting it. This value can deviate
        from the set value due to the finite increment of the exposure time.
        """
        if exp_time is not None:
            exp_time = exp_time[units.s]
            exposure_time = yield self._device.set_exposure(exp_time) # in seconds
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

    @setting(5,'start live',returns = 's')
    def start_live(self, c = None):
        """
        """
        acquisition_in_progress = True
        self._device.start_acquisition(frames_per_trigger=1)
        print('Camera starting live acquisition')
        print('Press X to abort acquisition')
        while acquisition_in_progress == True:
            self._device.wait_for_frame()
            frame = self._device.read_oldest_image()
            self.last_image = frame.astype(np.uint32)
            if self.config["save_enable"] == True:
                foldername = self.config["save_folder"]
                filename = 'last_image_filename.txt'
                # Save file 
                with open (foldername+filename, 'r') as file:
                    # Read filename and path from our .txt file
                    save_path = file.readline()
                save_folder = save_path.split('shots')[0] + 'images'
                # Check if folder exists, if it does not exist create it
                if not os.path.isdir(save_folder):
                    os.mkdir(save_folder)
                save_file = save_path.split('shots')[1]
                save_path = save_folder + save_file
                start_time = time.perf_counter()
                cv2.imwrite(save_path + '_image.tiff', frame)
                end_time = time.perf_counter()

                # Calculate elapsed time
                elapsed_time = end_time - start_time
                print('image saved as: ' + save_file + f'_image.tiff in: {elapsed_time} s')
            else:
                print('imaged acquired but not saved')
        if msvcrt.kbhit():
            text = msvcrt.getch().decode('utf-8')
            if text == 'X':      
                print(f'You entered {text}: aborting acquisition...')         
                acquisition_in_progress = False
                self._device.close()
                msg = yield ('Acquisition aborted')
                print(msg)
                returnValue (msg)

    @setting(6, 'frame_grab', dirname='s{name}',name='s{name}', fmt='s{format}')
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
