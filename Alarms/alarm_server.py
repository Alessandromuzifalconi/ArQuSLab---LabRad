# ArQuSLab <arquslab@units.it>, February 2023
"""
### BEGIN NODE INFO
[info]
name = room_alarm
version =
description = sends alarm when exceeding value 

[startup]
cmdline = %PYTHON% %FILE%
timeout = 70

[shutdown]
# message = 987654321
# setting = kill
timeout = 70
### END NODE INFO
"""

from trycourier import Courier
from twisted.internet import task
from twisted.internet import reactor
from labrad.server import LabradServer, setting

from alarm_class import alarm_funcs
import time

from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from influxdb_client import InfluxDBClient

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style


def read_DB():
    client = InfluxDBClient.from_config_file("//ARQUS-NAS/ArQuS Shared/LabRad/influx_ini_files/config_influx.ini")  # calling client from .ini file
    query_api = client.query_api()


    lab_temp_query = 'from(bucket: "data_logger")\
    |> range(start: -20s)\
    |> filter(fn: (r) => r._measurement == "temperature")\
    |> filter(fn: (r) => r._field == "channel_113")'

    XGS_pressure_query = 'from(bucket: "AgilentXGS600-db")\
    |> range(start: -3s, stop: -1s)\
    |> filter(fn: (r) => r._measurement == "pressure")\
    |> filter(fn: (r) => r._field == "channel")'

    AOSENSE_pressure_query = 'from(bucket: "IPCMini_db")\
    |> range(start: -30s)\
    |> filter(fn: (r) => r._measurement == "pressure")\
    |> filter(fn: (r) => r._field == "channel")'
    
    return query_api, lab_temp_query, XGS_pressure_query, AOSENSE_pressure_query

class room_alarm_server(LabradServer):
    name = "room_alarm"
    period = 120

    UPPER_ROOM_TEMPERATURE_THRESHOLD = 23
    UPPER_XGS_PRESSURE_THRESHOLD = 2e-10
    UPPER_AOSENSE_PRESSURE_THRESHOLD = 1e-9

    # @inlineCallbacks
    def initServer(self):  # Do initialization here
        self._loop_call = reactor.callLater(0, self._set_temperature_alarm)
        self._loop_call = reactor.callLater(0, self._set_pressure_alarm_XGS)
        self._loop_call = reactor.callLater(0, self._set_pressure_alarm_AOSENSE)
    
   
    @setting(10)
    def _set_temperature_alarm(self, c=None, data=None):
        time_started = time.time()
        AC = alarm_funcs()
        query_api, lab_temp_query, XGS_pressure_query, AOSENSE_pressure_query = read_DB()
        lab_temp_result = query_api.query(query=lab_temp_query)

        try:
            lab_temp_results = []
            for table in lab_temp_result:
                for record in table.records:
                    lab_temp_results.append((record.get_field(), record.get_value()))

            first_lab_temp_value = lab_temp_results[0][1]

            if first_lab_temp_value > self.UPPER_ROOM_TEMPERATURE_THRESHOLD:
                print('temperature alarm! sending email...')
                message = 'Subject: {}\n\n{}'.format('Temperature alarm!', f'Actual temperature is: {first_lab_temp_value} degrees (air conditioned thermistor)')
                AC.send_email(message)

            sleep_duration = max(self.period - (time.time()-time_started), 0)
            self._loop_call = reactor.callLater(sleep_duration, self._set_temperature_alarm)

        except:
            print('==================================================================================================================================================\n')
            print(f"{Fore.RED}NO AVAILABLE TEMPERATURE DATA! CHECK IF DATA LOGGER SERVER IS ON!{Style.RESET_ALL}\n")
            print('==================================================================================================================================================\n')
            sleep_duration = max(self.period - (time.time()-time_started), 0)
            self._loop_call = reactor.callLater(sleep_duration, self._set_temperature_alarm)



    @setting(11)
    def _set_pressure_alarm_XGS(self, c=None, data=None):
        time_started = time.time()
        AC = alarm_funcs()
        query_api, lab_temperature_query, XGSAOSENSE_pressure_query, AOSENSE_pressure_query = read_DB()
        lab_pressure_result = query_api.query(query=XGSAOSENSE_pressure_query)

        try:
            lab_pressure_results = []
            for table in lab_pressure_result:
                for record in table.records:
                    lab_pressure_results.append((record.get_field(), record.get_value()))

            #assigns a small value to first_lab_pressure_value when the IPCMini controller fails writing on influxDB
            if len(lab_pressure_results) != 2:
                first_lab_pressure_value = self.UPPER_XGS_PRESSURE_THRESHOLD*1e-1
                second_lab_pressure_value = self.UPPER_XGS_PRESSURE_THRESHOLD*1e-1

            elif len(lab_pressure_results) == 2:
                first_lab_pressure_value = lab_pressure_results[0][1]
                second_lab_pressure_value = lab_pressure_results[1][1]

            if first_lab_pressure_value and second_lab_pressure_value > self.UPPER_XGS_PRESSURE_THRESHOLD:
                print('pressure alarm! sending email...')
                message = 'Subject: {}\n\n{}'.format('Pressure alarm!', f'Actual pressure is: {second_lab_pressure_value} mbar (measured with Bayard Alpert gauge)')
                AC.send_email(message)

            sleep_duration = max(self.period - (time.time()-time_started), 0)
            self._loop_call = reactor.callLater(sleep_duration, self._set_pressure_alarm_XGS)

        except:
            print('==================================================================================================================================================\n')
            print(f"{Fore.RED}NO AVAILABLE PRESSURE DATA! CHECK IF XGS SERVER IS ON!{Style.RESET_ALL}\n")
            print('==================================================================================================================================================\n')
            sleep_duration = max(self.period - (time.time()-time_started), 0)
            self._loop_call = reactor.callLater(sleep_duration, self._set_pressure_alarm_XGS)



    @setting(12)
    def _set_pressure_alarm_AOSENSE(self, c=None, data=None):
        time_started = time.time()
        AC = alarm_funcs()
        query_api, lab_temperature_query, XGS_pressure_query, AOSENSE_pressure_query = read_DB()
        lab_pressure_result = query_api.query(query=AOSENSE_pressure_query)

        try:
            lab_pressure_results = []
            for table in lab_pressure_result:
                for record in table.records:
                    lab_pressure_results.append((record.get_field(), record.get_value()))
            
            # print(len(lab_pressure_results))

            #assigns a small value to first_lab_pressure_value when the IPCMini controller fails writing on influxDB
            if len(lab_pressure_results) == 0:
                first_lab_pressure_value = self.UPPER_AOSENSE_PRESSURE_THRESHOLD*1e-1

            elif len(lab_pressure_results) != 0:
                first_lab_pressure_value = lab_pressure_results[0][1]


            if first_lab_pressure_value > self.UPPER_AOSENSE_PRESSURE_THRESHOLD:
                print('pressure alarm! sending email...')
                message = 'Subject: {}\n\n{}'.format('Pressure alarm!', f'Actual pressure is: {first_lab_pressure_value} mbar (measured with AOSense ion pump gauge)')
                AC.send_email(message)

            sleep_duration = max(self.period - (time.time()-time_started), 0)
            self._loop_call = reactor.callLater(sleep_duration, self._set_pressure_alarm_AOSENSE)

        except:
            print(lab_pressure_results)
            print('==================================================================================================================================================\n')
            print(f"{Fore.RED}NO AVAILABLE PRESSURE DATA! CHECK IF IPCMini SERVER IS ON!{Style.RESET_ALL}\n")
            print('==================================================================================================================================================\n')
            sleep_duration = max(self.period - (time.time()-time_started), 0)
            self._loop_call = reactor.callLater(sleep_duration, self._set_pressure_alarm_AOSENSE)

   

__server__ = room_alarm_server()
if __name__ == '__main__':
    from labrad import util
    print(f'{Fore.GREEN} waiting a minute to be sure that other servers are already initialized {Style.RESET_ALL}')
    time.sleep(60)
    util.runServer(__server__)
    