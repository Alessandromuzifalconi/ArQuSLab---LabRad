# file: nuvu_cam_wrapper.py
# author: Guillaume Allain
# date: 28/04/18
# desc: Wrapper that englobes every methods we would like to use with the
#       nuvu. Essentially inherit most of the method from nc_camera but
#       wraps them in an easily readable class that add methods for init
#       and use of the camera

from nc_camera1 import *
import numpy as np
import time
import os
import cv2

class Nuvu_wrapper_error(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Nuvu_cam_wrapper(nc_camera):
    def __init__(self, targetDetectorTemp=-35, readoutMode=1, binning=1,
                 exposureTime=0.25, fps=30, index=0):
        super().__init__()
        self.__fps = fps
        
        self.openCam(nbBuff=4)
        self.setReadoutMode(readoutMode)
        self.getCurrentReadoutMode()
        self.setSquareBinning(binning)
        self.camInit()
        self.set_target_detector_temp(targetDetectorTemp)
        self.set_exposure_time(exposureTime)
        self.isrunning = False
        # self.setTimeout(self.exposureTime.value + self.waitingTime.value
        #                 + self.readoutTime.value + 500.0)
        self.setTimeout(1000)
        self.isrunning = False
    #Deactivated disconnect_if_error
    def disconnect_if_error(f):
        """Decorator that disconnect the camera if the method fails"""
        def func(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                # args[0].closeCam()
                # print('Successfull emergency disconnect of Nuvu Camera')
                raise e from None
        return func

    @property
    def real_fps(self):
        return self.__real_fps

    @disconnect_if_error
    def millisecond_to_fps(self,arg):
        return 1/(arg/1000)

    @disconnect_if_error
    def fps_to_millisecond(self,arg):
        return (1/arg)*1000

    @disconnect_if_error
    def set_fps(self,fps):
        if self.fps_to_millisecond(fps) <= (self.exposureTime.value
                                               + self.readoutTime.value):
            raise Nuvu_wrapper_error("FPS to small, change exposure time first")
        current_exp_time = self.exposureTime.value
        current_read_time = self.readoutTime.value
        self.setWaitingTime(self.fps_to_millisecond(fps)
                            - current_exp_time
                            - current_read_time)
        self.getWaitingTime()
        self.__real_fps = self.millisecond_to_fps(self.exposureTime.value
                                                  + self.waitingTime.value
                                                  + self.readoutTime.value)

    @disconnect_if_error
    def set_exposure_time(self, new_exposure_time):
        if new_exposure_time >= (self.fps_to_millisecond(self.__fps)
                                -self.readoutTime.value):
            raise Nuvu_wrapper_error("Exposure time too large, change FPS first")
        self.setExposureTime(new_exposure_time)
        self.getExposureTime()
        self.getReadoutTime()
        self.set_fps(self.__fps)

    @disconnect_if_error
    def set_calibrated_em_gain(self, new_em_gain):
        super(Nuvu_cam_wrapper, self).setCalibratedEmGain(int(new_em_gain))
        super(Nuvu_cam_wrapper, self).getCalibratedEmGain()

    def get_calibrated_em_gain(self):
        
        return self.calibratedEmGain.value

   
    @disconnect_if_error
    def get_image64(self):
        #get directly 64bit image
        return self.get_image().astype(np.float64)

    @disconnect_if_error
    def get_image(self):
        #get a uint16 image
        self.flushReadQueue()
        return self.getImg()
    

    @disconnect_if_error
    def get_sequence(self, nbr_imgs, nbr_cubes):
        #get a sequence
        
        super(Nuvu_cam_wrapper, self).saveSequence(nbr_imgs, nbr_cubes)
        
    def stop_sequence(self):
        super(Nuvu_cam_wrapper, self).stopSequence()

    @disconnect_if_error
    def get_bias(self):
        exposure_old = self.exposureTime.value
        self.setExposureTime(0)
        time.sleep(0.1)
        img = self.get_image()
        self.setExposureTime(exposure_old)
        self.getExposureTime()
        return img

    @disconnect_if_error
    def get_bias64(self):
        return self.get_bias().astype(np.float64)

    @disconnect_if_error
    def camStart(self, nbr_images = 0):
        super(Nuvu_cam_wrapper,self).camStart(nbr_images)
        self.isrunning = True

    @disconnect_if_error
    def camStop(self):
        super(Nuvu_cam_wrapper,self).camAbort()

        self.isrunning = False
        super(Nuvu_cam_wrapper, self).setShutterMode(2)

    @disconnect_if_error
    def get_component_temp(self,component):
        """
        Méthode qui récupère la température du composant spécifié et la
        stoque dans la valeur associée
        :param comp: identifiant du composant. 0=CCD, 1=controleur,
        2=powerSupply, 3=FGPA, 4=heatSink
        :return: None
        """
        super(Nuvu_cam_wrapper, self).getComponentTemp(component)
        values = [self.detectorTemp,self.controllerTemp,self.powerSupplyTemp, self.fpgaTemp,self.heatsinkTemp]
        return values[component].value

    @disconnect_if_error
    def get_ccd_temp(self):
        '''Récupère et retourne la valeur de température du CCD'''
        return self.get_component_temp(0)

    @disconnect_if_error
    def set_target_detector_temp(self,target):
        self.setTargetDetectorTemp(target)
        self.getTargetDetectorTemp()

    def get_target_detector_temp(self):
        return self.targetDetectorTemp.value

    @disconnect_if_error
    def set_roi_size(self,region,roiWidth,roiHeight):
        super(Nuvu_cam_wrapper, self).setRoiSize(region,roiWidth,roiHeight)
        

    @disconnect_if_error
    def set_roi_position(self, region, roix, roiy):
        super(Nuvu_cam_wrapper, self).setRoiPosition(region, roix, roiy)

    @disconnect_if_error
    def save_cube_as_images(cube, frames_number, output_dir = 'images'):
        os.makedirs(output_dir, exist_ok=True)
        
        for i in range(frames_number):
            image = cube[i]
            filename = os.path.join(output_dir, f"image{i:03d}.png")
            cv2.imwrite(filename, image)

    @disconnect_if_error
    def get_current_readout_speed(self):
        super(Nuvu_cam_wrapper, self).getCurrentReadoutMode()
        return (self.horizFreq.value, self.vertFreq.value)
    
    @disconnect_if_error
    def set_readout_mode(self, mode):
        super(Nuvu_cam_wrapper, self).setReadoutMode(mode)

    @disconnect_if_error
    def get_readout_modes(self):
        super(Nuvu_cam_wrapper, self).getNbrReadoutModes()
        list = np.empty((self.nbrReadoutMode.value + 1, 3), dtype='object')
        list[0] = ('amplitype', 'vertfreq', 'horizfreq')
        for i in range(self.nbrReadoutMode.value):
            super(Nuvu_cam_wrapper, self).getReadoutMode(i + 1)
            list[i + 1] = (self.ampliType.value, self.vertFreq.value, self.horizFreq.value)
        print(list)


    @disconnect_if_error
    def get_images(self, nbr_imgs):
        super(Nuvu_cam_wrapper, self).setShutterMode(1)
        self.camStart(nbr_imgs)
        images = []
        i = 0
        name = self.name
        if nbr_imgs == 0: #continous acquisition
            while self.isrunning:
                   

                   i = i + 1
                   self.name = f'{name}_{i}'
                   super(Nuvu_cam_wrapper, self).read()
                   
                   self.saveImage()
            


        else:
            for i in range(nbr_imgs):
                
                
                super(Nuvu_cam_wrapper, self).read()
                self.name = f'{name}_{i}'
                self.saveImage()
                
                image = images.append(self.ncImage)
                images.append(image)

        return images
    

    @disconnect_if_error
    def save_images(self, nbr_imgs_to_save, nbr_imgs_per_cube):
        
        super(Nuvu_cam_wrapper, self).saveSequence(nbr_imgs_per_cube, 0)
        super(Nuvu_cam_wrapper, self).setShutterMode(1)
        self.camStart(nbr_imgs_to_save)
        images = []
        for i in range (nbr_imgs_to_save):
            super(Nuvu_cam_wrapper, self).read()
            images.append(self.ncImage)
        super(Nuvu_cam_wrapper, self).stopSequence()
        self.camStop()
        super(Nuvu_cam_wrapper, self).setShutterMode(CLOSE)
        

        return images
    

    @disconnect_if_error
    def set_proc(self, proc):
        super(Nuvu_cam_wrapper, self).setProc(f'{proc}')


    @disconnect_if_error
    def createbias(self, nbr_imgs):
        super(Nuvu_cam_wrapper, self).createBias(nbr_imgs)

    @disconnect_if_error
    def get_proc_type(self):
        super(Nuvu_cam_wrapper, self).getProc()
        return self.procType
    
    @disconnect_if_error
    def set_kinetics(self, nbr_imgs = -1):
        super(Nuvu_cam_wrapper, self).setFastKinetics(nbr_imgs)

    @disconnect_if_error
    def set_discard(self, discard_count):
        super(Nuvu_cam_wrapper, self).setKineticsDiscard(discard_count)

    @disconnect_if_error
    def get_subimage_count(self):
        super(Nuvu_cam_wrapper, self).getKineticsImageCount()
        return self.subimage_per_burst.value
    
    @disconnect_if_error
    def set_waiting_time(self, waitingtime):
        super(Nuvu_cam_wrapper, self).setWaitingTime(waitingtime)

    @disconnect_if_error
    def get_waiting_time(self):
        self.getWaitingTime()

        return self.waitingTime.value

    @disconnect_if_error
    def get_exposure_time(self):
        self.getExposureTime()

        return self.exposureTime.value
    
    def set_name_cube(self, nome):
        self.namec = f'{nome}'

    def set_name_image(self, nome):
        self.name = f'{nome}'

    

if __name__ == '__main__':
    pass