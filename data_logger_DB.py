# ArQuSLab <arquslab@units.it>, November 2022
"""
### BEGIN NODE INFO
[info]
name = data_logger_temp
version =
description = measure temperature with thermocouples 363-0294

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

from influxdb_client import InfluxDBClient, Point, Dialect
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from data_logger import data_logger_funcs

import matplotlib.pyplot as plt
import numpy as np
import time
import csv
import pandas as pd
import datetime
from pathlib import Path


class data_logger_temp(LabradServer):
    name = "data_logger_temp"
    period = 30
    offset_ch102 = 4.6 * 0
    offset_ch101 = 4.0 * 0
    flowmeter_corr = 22000

    # def channels positions:
    channel_101_pos = 'back wall'
    channel_102_pos = 'below cell'
    channel_103_pos = 'RGA feedthrough flange'
    channel_104_pos = 'CF40 bellow bottom'
    channel_105_pos = 'Tombak central part'
    channel_106_pos = 'BAYARD-ALPERT top'
    channel_111_pos = 'sensor in air (atom table)'
    channel_112_pos = 'HEPA filters (atom table)'
    channel_113_pos = 'air conditioned'
    channel_114_pos = 'temperature controller'
    channel_115_pos = 'Bias Y coil'
    channel_116_pos = 'Bias X coil'
    channel_117_pos = 'Bottom MOT coil'
    channel_118_pos = 'Top MOT coil'
    channel_119_pos = 'sensor in air (laser table)'
    channel_120_pos = 'HEPA filters (laser table)'
    channel_201_pos = 'transfer cavity'
    channel_211_pos = 'flowmeter top ext layer'
    channel_213_pos = 'flowmeter top mid layer'
    channel_214_pos = 'flowmeter top int layer'
    channel_215_pos = 'water connection'
    channel_218_pos = 'flowmeter bottom int layer'
    channel_219_pos = 'flowmeter bottom mid layer'
    channel_220_pos = 'flowmeter bottom ext layer'

    # @inlineCallbacks
    def initServer(self):  # Do initialization here
        self._loop_call = reactor.callLater(0, self._RT_DB)
        
    def init_DB(self):  # Do database initialization here

        # client = InfluxDBClient.from_config_file(
        #     "D:/LabRAD/LabRADCodes/influx_ini_files/config_data_logger.ini")  # calling client from .ini file
        client = InfluxDBClient.from_config_file("//ARQUS-NAS/ArQuS Shared/LabRad/influx_ini_files/config_influx.ini")  # calling client from .ini file
        bucket = 'data_logger'
        write_api = client.write_api(write_options=SYNCHRONOUS)

        return bucket, write_api

    @setting(10)
    def _RT_DB(self, c=None, data=None):
        time_started = time.time()

        datalogger_func = data_logger_funcs()
        RC = datalogger_func.read_channels()
        # RV = datalogger_func.read_voltage()

        series = []

        bucket, write_api = self.init_DB()

        # T_channel_101 = RT[0] - self.offset_ch101
        # T_channel_102 = RT[1] - self.offset_ch102
        # T_channel_103 = RT[2]
        # T_channel_104 = RT[3]
        # T_channel_105 = RT[4]
        # T_channel_106 = RT[5]

        T_channel_111 = RC[0] #6
        T_channel_112 = RC[1] #7
        T_channel_113 = RC[2] #8
        T_channel_114 = RC[3] #9
        T_channel_115 = RC[4] #10
        T_channel_116 = RC[5] #11
        T_channel_117 = RC[6] #12
        T_channel_118 = RC[7] #13
        T_channel_119 = RC[8] #14
        T_channel_120 = RC[9] #15
        T_channel_201 = RC[10] #15
        T_channel_211 = RC[11] #15
        T_channel_213 = RC[12] #15
        T_channel_214 = RC[13] #15
        T_channel_215 = RC[14] #15
        T_channel_218 = RC[15] #15
        T_channel_219 = RC[16] #15
        T_channel_220 = RC[17] #15

        #save to CSV file
        date_file = datetime.datetime.now()
        date_file = "%s.%s.%s" % (
            date_file.year, date_file.month, date_file.day)

        __path__ = "//ARQUS-NAS/ArQuS Shared/LabRad/servers/Data_Logger/data_logger_csv_files/"
        filename = date_file
        fullpath = __path__ + str(filename) + ".csv"
        existence = Path(fullpath)

        if existence.is_file() == False:
            with open(fullpath, "a+", newline='') as file:
                writer = csv.writer(file, delimiter=',')
                writer.writerow(["date", self.channel_111_pos, self.channel_112_pos, self.channel_113_pos, self.channel_114_pos, self.channel_119_pos, self.channel_120_pos])


        date = datetime.datetime.now()
        date = "%s.%s.%s.%s.%s" % (
            date.year, date.month, date.day, date.hour, date.minute)
        # date = datetime.datetime.now()
        date_str = str(date)

        with open(fullpath, "a+", newline='') as file:
            writer = csv.writer(file, delimiter=',')
            writer.writerow([date, T_channel_111, T_channel_112, T_channel_113, T_channel_114, T_channel_119, T_channel_120])

        # channel_101 = {
        #     "measurement": "temperature",
        #     "tags": {
        #         "location": self.channel_101_pos,
        #         "room": "arqus_lab",
        #         "type": " thermocouple K-type",
        #         "tape": "glass cell",
        #     },
        #     "fields": {
        #         "channel_101": T_channel_101,
        #     }
        # }
        
        # channel_102 = {
        #     "measurement": "temperature",
        #     "tags": {
        #         "location": self.channel_102_pos,
        #         "room": "arqus_lab",
        #         "tape": "glass cell",
        #         "type": "thermocouple K-type",
        #     },
        #     "fields": {
        #         "channel_102": T_channel_102,
        #     }
        # }
        
        # channel_103 = {
        #     "measurement": "temperature",
        #     "tags": {
        #         "location": self.channel_103_pos,
        #         "room": "arqus_lab",
        #         "tape": "glass cell",
        #         "type": "thermocouple K-type",
        #     },
        #     "fields": {
        #         "channel_103": T_channel_103,
        #     }
        # }
        
        # channel_104 = {
        #     "measurement": "temperature",
        #     "tags": {
        #         "location": self.channel_104_pos,
        #         "room": "arqus_lab",
        #         "tape": "BAYARD ALPERT",
        #         "type": "thermocouple K-type",
        #     },
        #     "fields": {
        #         "channel_104": T_channel_104,
        #     }
        # }
        
        # channel_105 = {
        #     "measurement": "temperature",
        #     "tags": {
        #         "location": self.channel_105_pos,
        #         "room": "arqus_lab",
        #         "tape": "angle valve",
        #         "type": "thermocouple K-type",
        #     },
        #     "fields": {
        #         "channel_105": T_channel_105,
        #     }
        # }
        
        # channel_106 = {
        #     "measurement": "temperature",
        #     "tags": {
        #         "location": self.channel_106_pos,
        #         "room": "arqus_lab",
        #         "tape": "BAYARD ALPERT",
        #         "type": "thermocouple K-type",
        #     },
        #     "fields": {
        #         "channel_106": T_channel_106,
        #     }
        # }

        channel_111 = {
            "measurement": "temperature",
            "tags": {
                "location": self.channel_111_pos,
                "table": "atom",
                "type": "thermistor",
            },
            "fields": {
                "channel_111": T_channel_111,
            }
        }

        channel_112 = {
            "measurement": "temperature",
            "tags": {
                "location": self.channel_112_pos,
                "table": "atom",
                "type": "thermistor",
            },
            "fields": {
                "channel_112": T_channel_112,
            }
        }

        channel_113 = {
            "measurement": "temperature",
            "tags": {
                "location": self.channel_113_pos,
                "room": "arqus_lab",
                "type": "thermistor",
            },
            "fields": {
                "channel_113": T_channel_113,
            }
        }

        channel_114 = {
            "measurement": "temperature",
            "tags": {
                "location": self.channel_114_pos,
                "room": "arqus_lab",
                "type": "thermistor",
            },
            "fields": {
                "channel_114": T_channel_114,
            }
        }

        channel_115 = {
            "measurement": "temperature",
            "tags": {
                "location": self.channel_115_pos,
                "room": "arqus_lab",
                "type": "thermistor",
            },
            "fields": {
                "channel_115": T_channel_115,
            }
        }

        channel_116 = {
            "measurement": "temperature",
            "tags": {
                "location": self.channel_116_pos,
                "room": "arqus_lab",
                "type": "thermistor",
            },
            "fields": {
                "channel_116": T_channel_116,
            }
        }

        channel_117 = {
            "measurement": "temperature",
            "tags": {
                "location": self.channel_117_pos,
                "room": "arqus_lab",
                "type": "thermistor",
            },
            "fields": {
                "channel_117": T_channel_117,
            }
        }

        channel_118 = {
            "measurement": "temperature",
            "tags": {
                "location": self.channel_118_pos,
                "room": "arqus_lab",
                "type": "thermistor",
            },
            "fields": {
                "channel_118": T_channel_118,
            }
        }

        channel_119 = {
            "measurement": "temperature",
            "tags": {
                "location": self.channel_119_pos,
                "table": "laser",
                "type": "thermistor",
            },
            "fields": {
                "channel_119": T_channel_119,
            }
        }

        channel_120 = {
            "measurement": "temperature",
            "tags": {
                "location": self.channel_120_pos,
                "table": "laser",
                "type": "thermistor",
            },
            "fields": {
                "channel_120": T_channel_120,
            }
        }

        channel_201 = {
            "measurement": "temperature",
            "tags": {
                "location": self.channel_201_pos,
                "table": "laser",
                "type": "thermistor",
            },
            "fields": {
                "channel_201": T_channel_201,
            }
        }

        channel_211 = {
            "measurement": "water flux",
            "tags": {
                "location": self.channel_211_pos,
            },
            "fields": {
                "channel_211": T_channel_211/self.flowmeter_corr*60,
            }
        }

        channel_213 = {
            "measurement": "water flux",
            "tags": {
                "location": self.channel_213_pos,
            },
            "fields": {
                "channel_213": T_channel_213/self.flowmeter_corr*60,
            }
        }

        channel_214 = {
            "measurement": "water flux",
            "tags": {
                "location": self.channel_214_pos,
            },
            "fields": {
                "channel_214": T_channel_214/self.flowmeter_corr*60,
            }
        }

        channel_215 = {
            "measurement": "temperature",
            "tags": {
                "location": self.channel_215_pos,
                "room": "arqus_lab",
                "type": "thermistor",
            },
            "fields": {
                "channel_215": T_channel_215,
            }
        }

        channel_218 = {
            "measurement": "water flux",
            "tags": {
                "location": self.channel_218_pos,
            },
            "fields": {
                "channel_218": T_channel_218/self.flowmeter_corr*60,
            }
        }

        channel_219 = {
            "measurement": "water flux",
            "tags": {
                "location": self.channel_219_pos,
            },
            "fields": {
                "channel_219": T_channel_219/self.flowmeter_corr*60,
            }
        }

        channel_220 = {
            "measurement": "water flux",
            "tags": {
                "location": self.channel_220_pos,
            },
            "fields": {
                "channel_220": T_channel_220/self.flowmeter_corr*60,
            }
        }

        # series.extend([channel_101, channel_102, channel_103, channel_104, channel_105, channel_106, channel_111, channel_112, channel_113, channel_114, channel_115, channel_116, channel_117, channel_118, channel_119, channel_120])
        series.extend([channel_111, channel_112, channel_113, channel_114, channel_115, channel_116, channel_117, channel_118, channel_119, channel_120, channel_201, channel_211, channel_213, channel_214, channel_215, channel_218, channel_219, channel_220])
        write_api.write(bucket=bucket, record = [series])

        datalogger_func.close()
        sleep_duration = max(self.period - (time.time()-time_started), 0)
        self._loop_call = reactor.callLater(sleep_duration, self._RT_DB)

__server__ = data_logger_temp()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
    
