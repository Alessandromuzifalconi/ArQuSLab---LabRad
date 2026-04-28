# ArQuSLab <arquslab@units.it>, November 2022
"""
### BEGIN NODE INFO
[info]
name = XGS-600_DB
version = 1.2
description = measuring pressure with Bayard Alpert gauge

[startup]
cmdline = %PYTHON% %FILE%
timeout = 30

[shutdown]
# message = 987654321
# setting = kill
timeout = 30
### END NODE INFO
"""


from twisted.internet import task
from twisted.internet import reactor
from labrad.server import LabradServer, setting
from picosdk.discover import find_all_units
import ctypes
import numpy as np
from picosdk.usbtc08 import usbtc08 as tc08
from picosdk.functions import assert_pico2000_ok
import time
import matplotlib.pyplot as plt

from influxdb_client import InfluxDBClient, Point, Dialect
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from AgilentXGS import XGS600Driver



class AgilentXGS_DB(LabradServer):
    name = "XGS-600_DB"
    period = 1
    # @inlineCallbacks
    def initServer(self):  # Do initialization here
        self._loop_call = reactor.callLater(0, self._RP_DB)

    def init_DB(self):  # Do initialization here

        client = InfluxDBClient.from_config_file("D:/LabRAD/LabRADCodes/influx_ini_files/config_AgilentXGS.ini")  # calling client from .ini file
        bucket = 'AgilentXGS600-db'
        write_api = client.write_api(write_options=SYNCHRONOUS)

        return bucket, write_api

    @setting(10)
    def _RP_DB(self, c=None, data=None):

        time_started = time.time()

        XGS = XGS600Driver()
        RP = XGS.read_all_pressures()[0]

        bucket, write_api = self.init_DB()
        

        point = {
        "measurement": "pressure",
        "tags": {
            "location": "boh",
            "room": "arqus_lab",
        },
        "fields": {
            "channel": RP,
        }
        }

        write_api.write(bucket=bucket, record=point)

        XGS.close()
        sleep_duration = max(self.period - (time.time()-time_started), 0)
        self._loop_call = reactor.callLater(sleep_duration, self._RP_DB)
        return RP


__server__ = AgilentXGS_DB()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
