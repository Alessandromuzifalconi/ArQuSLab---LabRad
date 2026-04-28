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
from labrad import units
import os


def compute_optical_density(atoms_pic, light_pic):
        l = 556e-9
        sigma = 3*l**2/2*np.pi
        return -(1/sigma) * np.log(atoms_pic/light_pic)


class pvcam_camera_server (LabradServer):
    name = "PVCAM_camera"
    config = dict(
        id='',
        exposure_time=1 * units.ms,
        temperature_setpoint = 0 * units.degC,
        trigger_mode='Edge Trigger',
        readout_port = 'Sensitivity',
        save_folder = '//ARQUS-CAM/Experiments/ytterbium174/',
        capture_mode = 0,
        save_enable = True,
        frames_number = 1)
    
    last_image = None

    def initServer(self):  # Do initialization here
        pvc.init_pvcam()                   # Initialize PVCAM 
        cam = next(Camera.detect_camera()) # Use generator to find first camera. 
        self._device = cam
        self._queue = None
        self._device.open()  # Open the camera.
        print('Camera open')
        self.read_config(filename = '//ARQUS-NAS/ArQuS Shared/Parts/Cameras/Kinetix sCMOS/Python codes/initialization/PVCAM_ini.txt') 
        self.set_config()
        if self.config["capture_mode"] == 0:
            self.start_live()
        elif self.config["capture_mode"] == 1:
            self.optical_density()
        elif self.config["capture_mode"] == 2:
            self.average(frames_num=self.config["frames_number"])

    def read_config (self,filename = '//ARQUS-NAS/ArQuS Shared/Parts/Cameras/Kinetix sCMOS/Python codes/initialization/PVCAM_ini.txt'):
        # Reads  configuration from file and stores information in self.config dictionary
        with open (filename, 'r') as ini_file:
            lines = ini_file.readlines()
            ini_file.close()
        temperature_setpoint = float(lines[0][22:25])
        exposure_time = float(lines[1][15:16])
        trigger_mode = lines[2][14:-1]
        readout_port  = lines[3][14:-1]
        save_folder = lines[4][13:-1]
        capture_mode = float(lines[5][14:-1])
        frames_number= int(lines[6][15:-1])
        save_enable = bool(int(lines[7][13:-1]))
        self.config["id"] = self.get_name()
        self.config["temperature_setpoint"] = temperature_setpoint
        self.config["exposure_time"] = exposure_time
        self.config["trigger_mode"] = trigger_mode
        self.config["readout_port"] = readout_port
        self.config["save_folder"] = save_folder
        self.config["capture_mode"] = capture_mode
        self.config["frames_number"] = frames_number
        self.config["save_enable"] = save_enable
        print('Camera configuration: ')
        print(f'id: {self.config["id"]},')
        print(f'temperature setpoint: {self.config["temperature_setpoint"]} °C,')
        print(f'trigger mode: {self.config["trigger_mode"]},')
        print(f'readout port: {self.config["readout_port"]}, bit depth: {self._device.bit_depth}')
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
        
    @setting(1, 'get name')
    def get_name(self, c = None):
        """Returns camera name."""
        return self._device.name
    
    @setting(2, 'get temperature', returns='v')
    def get_temperature(self, c):
        """Returns camera actual temperature (not necessarily equal to setpoint)."""
        temperature = yield self._device.temp
        returnValue(temperature * units.degC)

    @setting(3, 'temperature setpoint', temperature_setpoint='v[degC]{temperature_setpoint}', returns='v[degC]')
    def temperature_setpoint(self, c = None, temperature_setpoint = None):
        """
        Returns or sets the camera temperature setpoint.
        If temperature_setpoint is None it gets the temperature of the camera, otherwise it changes it to the setpoint and returns the new value
        """
        if temperature_setpoint is not None:
            self._device.temp_setpoint = int(temperature_setpoint[units.degC])
        temperature_setpoint = yield self._device.temp_setpoint
        returnValue(temperature_setpoint*units.degC)

    @setting(4, 'exposure time', exp_time ='v[ms]{exp_time}', returns='v[s]')
    def exposure_time(self, c = None, exp_time = None):
        """
        Returns or sets the camera exposure time.
        If exposure time is None it gets the exposure time of the camera, otherwise it changes it to the new exposure time and returns the new value
        """
        if exp_time is not None:
            self._device.exp_time = int(exp_time[units.ms])
        exp_time = yield self._device.exp_time
        returnValue(exp_time*units.ms)

    @setting(5, 'trigger mode', trig_set = 's{exp_set}', returns='s')
    def trigger_mode(self, c = None,trig_set = None):
        """
        Returns exposure mode of the camera (i.e. trigger mode)
        If exposure set is None it gets the exposure mode of the camera, otherwise it changes it to the new exposure mode and returns the new value
        """
        if trig_set is not None:
            self._device.exp_mode = trig_set

        trig_set = yield self._device.exp_modes[self._device.exp_mode]
        returnValue(trig_set)

    @setting(6, 'get frame and save', save_image ='b{save_image}',returns = 's')
    def get_frame_and_save(self, c = None, save_image = True):
        """
        Saves acquired image
        """
        img = yield self._device.get_frame()
        self.last_image = img.astype(np.uint32)
        if save_image:
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
            cv2.imwrite(save_path + '_image.tiff', img)
            returnValue ('image saved as: ' + save_path + '_image.tiff')
        else:
            returnValue ('image captured but not saved')

    @setting(7, 'get frame', returns = '*2w')
    def get_frame(self, c):
        """
        Returns instantaneous camera frame as array 
        """
        img = yield self._device.get_frame()
        self.last_image = img.astype(np.uint32)

        returnValue (img.astype(np.uint32))

    @setting(8,'readout port', readout_set = '?{readout_set}', returns='s')
    def readout_port(self, c = None, readout_set = None):
        """
        Returns readout port of the camera (i.e. camera mode: Dynamic Range, Sensitivity, etc...)
        If readout set is None it gets mode of the camera, otherwise it changes it to the new mode and returns the new value
        """
        if readout_set is not None:
            self._device.readout_port = readout_set
        readout_set = yield self._device.readout_port
        if readout_set == 0:
            readout_port_string = 'Sensitivity'
        elif readout_set == 1:
            readout_port_string = 'Speed'
        elif readout_set == 2:
            readout_port_string = 'Dynamic Range'
        elif readout_set == 3:
            readout_port_string = 'Sub-Electron'
        returnValue(readout_port_string)

    @setting(9,'get sequence', frames_number = 'w{frames_number}',returns = '*3w')
    def get_sequence(self, c = None,frames_number = 1):
        """
        Returns sequence of frames as array 
        """
        stack = yield self._device.get_sequence(num_frames=frames_number)
        returnValue (stack.astype(np.uint32))

    @setting(10,'start live',returns = 's')
    def start_live(self, c = None):
        """
        """
        acquisition_in_progress = True
        self._device.start_live()
        print('Camera starting live acquisition')
        print('Press X to abort acquisition')
        while acquisition_in_progress == True:
            frame_status = yield self._device.check_frame_status()
            if frame_status == 'FRAME_AVAILABLE':
                frame, fps, frame_count = yield self._device.poll_frame(copyData=False)
                frame = frame['pixel_data']
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
                    self._device.abort()
                    msg = yield ('Acquisition aborted')
                    print(msg)
                    returnValue (msg)
                
    @setting(11,'close camera', returns='s')
    def close_camera(self,c):
        self._device.abort()
        self._device.close()
        msg = yield 'Camera closed'
        print(msg)
        returnValue(msg)
    
    @setting(12,'open camera', returns='s')
    def open_camera(self,c):
        self._device.open()
        msg = yield 'Camera opened'
        print(msg)
        returnValue(msg)

    @setting(13, 'get last image', returns = '*2w')
    def get_last_image(self, c):
        """
        Returns last camera frame as array 
        """
        last = yield self.last_image
        returnValue (last)
    
    @setting(14, 'compute optical density', returns = 's')
    def optical_density(self, c = None):
        """
        """
        acquisition_in_progress = True
        self._device.start_live()
        print('Camera starting live acquisition')
        print('Press X to abort acquisition')
        while acquisition_in_progress == True:
            frame_number = 1
            images = []
            while frame_number <= 2:
                frame_status = yield self._device.check_frame_status()
                if frame_status == 'FRAME_AVAILABLE':
                    frame, fps, frame_count = yield self._device.poll_frame(copyData=False)
                    images.append(frame['pixel_data'])
                    frame_number += 1
            OD = compute_optical_density(images[0], images[1]) 
            self.last_image = OD.astype(np.uint32)     
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
                cv2.imwrite(save_path + '_ODimage.tiff', OD)
                print('optical density image saved as: ' + save_file + '_ODimage.tiff')
            else:
                print('optical density imaged acquired but not saved')
            if msvcrt.kbhit():
                text = msvcrt.getch().decode('utf-8')
                if text == 'X':      
                    print(f'You entered {text}: aborting acquisition...')         
                    acquisition_in_progress = False
                    self._device.abort()
                    msg = yield ('Acquisition aborted')
                    print(msg)
                    returnValue (msg)
                
    @setting(15, 'compute average', frames_num = 'w{frames_num}', returns = 's')
    def average(self, c = None, frames_num = None):
        """
        """
        if frames_num == None:
            frames_num = self.config["frames_number"]
        acquisition_in_progress = True
        self._device.start_live()
        print('Camera starting live acquisition')
        print('Press X to abort acquisition')
        while acquisition_in_progress == True:
            frame_number = 1
            images = []
            while frame_number <= frames_num:
                frame_status = yield self._device.check_frame_status()
                if frame_status == 'FRAME_AVAILABLE':
                    frame, fps, frame_count = yield self._device.poll_frame(copyData=False)
                    images.append(frame['pixel_data'])
                    print(f'Image {frame_number} acquired') 
                    frame_number += 1
                    self.last_image = frame['pixel_data'].astype(np.uint32)     
            images = np.asarray(images)
            avg = np.mean(images, axis = 0)
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
                cv2.imwrite(save_path + f'_AVG{frames_num}image.tiff', avg)
                print('average image saved as: ' + save_file + f'_AVG_{frames_num}_image.tiff')
            else:
                print('average imaged acquired but not saved')
            if msvcrt.kbhit():
                text = msvcrt.getch().decode('utf-8')
                if text == 'X':      
                    print(f'You entered {text}: aborting acquisition...')         
                    acquisition_in_progress = False
                    self._device.abort()
                    msg = yield ('Acquisition aborted')
                    print(msg)
                    returnValue (msg)


__server__ = pvcam_camera_server()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
