# ArQuSLab <arquslab@units.it>, February 2023
"""
### BEGIN NODE INFO
[info]
name = Wieserlabs_DDS
version =
description = set single tone profile

[startup]
cmdline = %PYTHON% %FILE%
timeout = 30

[shutdown]
# message = 987654321
# setting = kill
timeout = 30
### END NODE INFO
"""

from DDS_class import DDS_funcs
from twisted.internet import task
from twisted.internet import reactor
from labrad.server import LabradServer, setting

from influxdb_client import InfluxDBClient, Point, Dialect
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS

from DDS_class import DDS_funcs

from notify_run import Notify 

class DDS_class(LabradServer):
    name = "Wieserlabs_DDS"

    # @inlineCallbacks
    def initServer(self):  # Do initialization here
        # os.chdir("D:/LabRAD/LabRADCodes/servers/DDS_Wieserlabs")
        # os.system("start cmd.exe /k python single_tone_params.py")
        #return self.set_single_tone()
        pass

    
    @setting(10, channel='i', freq='v[]', amp='v[]', phase='v[]')
    def set_single_tone(self, c, channel, freq, amp, phase):
        DDS = DDS_funcs()
        return DDS.single_tone(channel, freq, amp, phase)

    @setting(11)
    def reset(self, c=None, data=None):
        DDS = DDS_funcs()
        return DDS.reset()

    @setting(12, channel='i')
    def reset_channel(self, c, channel):
        DDS = DDS_funcs()
        return DDS.reset_channel(channel)

    @setting(13, channel='i', freq='v[]', phase='v[]')
    def set_full_amp(self, c, channel, freq, phase):
        DDS = DDS_funcs()
        return DDS.set_full_amp(channel, freq, phase)

    @setting(14, channel='i')
    def enable_am(self, c, channel):
        DDS = DDS_funcs()
        return DDS.enable_am(channel)
   
    @setting(15, channel='i')
    def set_fm(self, c, channel, fmin, fmax, amp, route, BNC_channel, inv = 0):
        DDS = DDS_funcs()
        return DDS.set_fm(channel, fmin, fmax, amp, route, BNC_channel, inv)
    
    @setting(16, channel='i', freq='v[]', amp='v[]', phase='v[]')
    def set_gated_tone(self, c, channel, freq, amp, phase, route, BNC_channel):
        DDS = DDS_funcs()
        inv = 0
        return DDS.gate(channel, freq, amp, phase, route , inv, BNC_channel)

__server__ = DDS_class()
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
    # set_single_tone(0, 100e6, 3, 0)
    # DDS = DDS_funcs()
    # DDS.single_tone(0, 100e6, 3, 0)
    # DDS.set_fm(0, 85e6, 135e6, 3, 'OSK', 'A')
