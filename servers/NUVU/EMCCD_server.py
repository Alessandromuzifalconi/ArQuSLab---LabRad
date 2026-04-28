from nuvu_cam_wrapper1 import Nuvu_cam_wrapper


from twisted.internet import task
from twisted.internet import reactor
from twisted.internet.defer import (inlineCallbacks, returnValue, Deferred,
                                    DeferredQueue)

from labrad.server import LabradServer, setting
import cv2



import threading

import numpy as np
import matplotlib.pyplot as plt
from labrad import units
import os
import tifffile as tiff
import shutil

class NuvuCameraServer(LabradServer):
    name = "emccd"
    last_image = None

    def initServer(self):
        self._camera = Nuvu_cam_wrapper()

        
    @inlineCallbacks
    def _validate_feature(self, feature_name, value):
        if feature_name.lower() == 'em_gain' :
            min_value, max_value = yield self._camera.getemgainrange()
        elif feature_name.lower() == 'detector_temp':
            min_value, max_value = yield self._camera.getemgaintemprange()
        else:
            raise ValueError(f"Unknown feature '{feature_name}'")

        if not (min_value <= value <= max_value):
            raise ValueError(f"'{feature_name}' must be between '{min_value}' and '{max_value}'")

        returnValue(value)

    @setting(1, 'get attribute')
    def get_attribute(self, c, name):
        method_name = f"get_{name}"
        getter = getattr(self._camera, method_name, None)

        if getter is None or not callable(getter):
            raise AttributeError(f"proprietà '{name}'non trovata nel wrapper")
        
        return getter()
        
    
    @setting(2, 'set attribute', value='?')
    def set_attribute(self, c, name, value):
        method_name = f"set_{name}"
        setter = getattr(self._camera, method_name, None)

        if setter is None or not callable(setter):
            raise AttributeError(f"proprietà '{name}'non trovata nel wrapper")
        
        setter(value)

    @setting(3,'get frame')
    def get_frame(self, c):
        self._camera.setShutterMode(1)
        self._camera.camStart(1)
        

        

        image = self._camera.get_image()
        
        self._camera.saveImage()
        self._camera.camStop
        self._camera.setShutterMode(2)

        

        
        


    @setting(4, 'frames i, frames_per_cube i, nome (s?)', returns='')
    def save_cubes(self, c, frames, frames_per_cube):   
     
        
        self._camera.save_images(frames, frames_per_cube)
        



    @setting(5,'get images')         #0 per continuos acquisition
    def get_images(self, c, nbr_imgs):

        
        images = self._camera.get_images(nbr_imgs)

       # output_folder = "C:\\Users\\ARQUSLAB-ADMIN.DESKTOP-IIQDMVF\\Pictures\\Andrea Nuvu"

      #  os.makedirs(output_folder, exist_ok = True)

     #   for i, image in enumerate(images):
      #      filename = os.path.join(output_folder, f"image_{i:03}.png")
       #     cv2.imwrite(filename, image)
            
    @setting(6, 'processing')
    def processing(self, c, nbr_imgs_bias, proc, img_da_prendere):
        self._camera.createbias(nbr_imgs_bias)
        self._camera.set_proc(f'{proc}')

        
        
        

        self._camera.get_images(img_da_prendere)



    @setting(7, 'fast kinetics')
    def fast_kinetics(self, c, nbr_bursts, discard_count):
        roiwidth = 512
        roiheight = 32
        roix = 0
        roiy = 512-32
        
        subimagedelay = 0.001
        waitingtime = 3 - subimagedelay

       
        
        self._camera.set_roi_size(0, roiwidth, roiheight)
        self._camera.set_roi_position(0, roix, roiy)

        self._camera.applyRoi()
        self._camera.set_kinetics()
        self._camera.set_discard(discard_count)
        self._camera.setExposureTime(subimagedelay)
        self._camera.setWaitingTime(waitingtime)
        
        self._camera.get_subimage_count()
        subimmagini = self._camera.subimage_per_burst.value
        print(f'farai {subimmagini} immagini per burst')

        
        self._camera.save_images(nbr_bursts*subimmagini, subimmagini)


        source_dir = r'C:\\Users\\ARQUSLAB-ADMIN'  # Cartella da cui prendere le immagini
        dest_dir = 'C:\\Users\\ARQUSLAB-ADMIN\\Pictures\\NuPixel Images'  # Cartella di destinazione

        images = [f for f in os.listdir(source_dir) if f.lower().endswith('.tiff')]


        os.makedirs(dest_dir, exist_ok=True)

        for image in images:
            source_path = os.path.join(source_dir, image)  # Percorso completo del file sorgente
            dest_path = os.path.join(dest_dir, image)     # Percorso completo del file destinazione
            shutil.move(source_path, dest_path)






    @setting(8,'abort')
    def abort(self, c):

        self._camera.camStop()

__server__ = NuvuCameraServer()
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)