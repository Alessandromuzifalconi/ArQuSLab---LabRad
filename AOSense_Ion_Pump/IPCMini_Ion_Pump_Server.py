#ArQuSLab (arquslab@units.it), November 2022

"""
### BEGIN NODE INFO
[info]
name = AOSense_Ion_Pump
version = 
description = measure of pressure with Agilent IPCMini Ion Pump controller

[startup]
cmdline = %PYTHON% %FILE%
timeout = 30

[shutdown]
# message = 987654321
# setting = kill
timeout = 30
### END NODE INFO
"""


from twisted.internet import reactor
from labrad.server import LabradServer, setting
import numpy as np
from picosdk.usbtc08 import usbtc08 as tc08
from picosdk.functions import assert_pico2000_ok
import time
import matplotlib.pyplot as plt

from influxdb_client import InfluxDBClient, Point, Dialect
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from os import path
import sys

_root = path.abspath(path.join('//ARQUS-NAS/ArQuS Shared/LabRad/servers/AOSense_Ion_Pump/lib'))
sys.path.append(_root)
from IPCMini_Ion_Pump_Device import IPC_Mini_Driver

import datetime
from pathlib import Path



class AgilentTurbo(LabradServer):
    name = "AOSense_Ion_Pump"
    period = 20
    
    # @inlineCallbacks
    def initServer(self):  # Do initialization here
        self._loop_call_1 = reactor.callLater(0, self._RP_DB)

    def init_DB(self):  # Do initialization here
        client = InfluxDBClient.from_config_file("//ARQUS-NAS/ArQuS Shared/LabRad/influx_ini_files/config_influx.ini")  # calling client from .ini file
        bucket = 'IPCMini_db'
        write_api = client.write_api(write_options=SYNCHRONOUS)
        return bucket, write_api

    @setting(10)
    def _RP_DB(self, c=None, data=None):

        time_started = time.time()

        IPCMini = IPC_Mini_Driver()
        RP = IPCMini.read_pressure()

        bucket, write_api = self.init_DB()

        point = {
        "measurement": "pressure",
        "tags": {
            "room": "arqus_lab",
        },
        "fields": {
            "channel": RP,
        }
        }
        
        if RP !=0:
            write_api.write(bucket=bucket, record=point)
            IPCMini.close()
        else:
            IPCMini.close()

        sleep_duration = max(self.period - (time.time()-time_started), 0)
        self._loop_call = reactor.callLater(sleep_duration, self._RP_DB)
        return RP
    
    

__server__ = AgilentTurbo()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
