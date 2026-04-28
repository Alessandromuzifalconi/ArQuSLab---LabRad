from labrad import connect
import time

cxn = connect()


cam = cxn.emccd



cam.set_attribute('calibrated_em_gain', 1)



cam.set_attribute('name_cube', 'fast_kinetics')
cam.fast_kinetics(5, 5)




