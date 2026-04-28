# ArQuSLab <arquslab@units.it>, November 2022
"""
### BEGIN NODE INFO
[info]
name = cassone_agilent
version =
description = cassone agilent driver

[startup]
cmdline = %PYTHON% %FILE%
timeout = 60

[shutdown]
# message = 987654321
# setting = kill
timeout = 30
### END NODE INFO
"""

from twisted.internet import task
from twisted.internet import reactor
from labrad.server import LabradServer, setting

from pathlib import Path
import numpy as np
from cassone_agilent_functions import cassone_funcs


class cassone_agilent(LabradServer):
    name = "cassone_agilent"
    default_config = dict(
    device='GPIB1::8::INSTR')

    # @inlineCallbacks
    def initServer(self):  # Do initialization here
        self._device = cassone_funcs(self.default_config['device'])

    @setting(1, returns='w')
    def set_freq(self, c, frequency):
        """set frequency"""
        print(f'Frequency set to {frequency}')
        return self._device.set_freq(frequency)
        
    @setting(2, returns='w')
    def set_amp(self, c, amplitude):
        """set amplitude"""
        return self._device.set_amp(amplitude)
        
    @setting(3)
    def read_freq_list(self, c):
        """read list of frequencies"""
        return self._device.read_freq_list()
    
             
    @setting(4, n_vector = 'i')
    def make_freq_list(self, c, n_vector, values_list):
        """Makes list of points.
        It takes in input three space-separated values.
        For a sweep the style is: (min max step)
        For constant values the style is: (number number number_of_repetitions)

            Arguments:
                n_vector (int):
                    Number of segments. 
                values_list (float array):
                    min max step frequency in MHz       
        """     
        self._device.make_freq_list(n_vector, values_list)
        return print('Frequency list written')
    

    @setting(5, n_vector = 'i')
    def make_list(self, c, n_vector, freq_values_list, amp_values_list, dwell_values_list):
        """Makes list of points.
        It takes in input three space-separated values.
        For a sweep the style is: (min max step)
        For constant values the style is: (number number number_of_repetitions)

            Arguments:
                n_vector (int):
                    Number of segments. 
                values_list (float array):
                    min max step frequency in MHz       
        """     
        self._device.make_list(n_vector, freq_values_list, amp_values_list,dwell_values_list)
        return print(f' List written')
    
    @setting(6)
    def write_list(self, c, freq_values, amp_values, dwell_values, trigger_steps):
        self._device.write_list (freq_values, amp_values, dwell_values, trigger_steps)
        return print(f'List written')

__server__ = cassone_agilent()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
    
