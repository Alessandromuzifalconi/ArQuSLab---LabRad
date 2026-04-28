"""Driver class for data-logger control"""
from __future__ import print_function
import time
import pyvisa
from pyvisa.constants import StopBits, Parity


class data_logger_funcs():
    """Driver for data_logger"""

    def __init__(self):
        rm = pyvisa.ResourceManager()
        # print(rm.list_resources())
        self.inst = rm.open_resource('GPIB0::9::INSTR')

        # If you want to initialize a scan from remote you can do it from here
        # self.inst.write('CONF:TEMP THER,10000, 1, 0.1, (@112)')
        # self.inst.write('ROUT:SCAN (@112)')
        # self.inst.write('TRIG:SOUR TIM')
        # self.inst.write('TRIG:TIM 10')
        # self.inst.write('TRIG:COUN INF')
        # self.inst.write('INIT')
        

    def close(self):
        self.inst.close()

    def read_channels(self):
        temp_list = []
        # self.inst.query('READ?')

        #this is used to initialize a scan and make calculations over one or different channels
        # rt_channel_111 = round(float(self.inst.query('CALC:AVER:MIN? (@111)')), 2)

        # data_str_read = self.inst.query('R? 50000')
        # data_list = []
        # data_str_read = data_str_read.split("+", 1)[1] 
        # for i in data_str_read.split(","):
        #     data_list.append(float(i))            
        # last_values = data_list[-17:]

        # last_values = self.inst.query('DATA:LAST? (@112)')
        rt_channel_111 = round(float(self.inst.query('DATA:LAST? (@111)')), 2)
        rt_channel_112 = round(float(self.inst.query('DATA:LAST? (@112)')), 2)
        rt_channel_113 = round(float(self.inst.query('DATA:LAST? (@113)')), 2)
        rt_channel_114 = round(float(self.inst.query('DATA:LAST? (@114)')), 2)
        rt_channel_115 = round(float(self.inst.query('DATA:LAST? (@115)')), 2)
        rt_channel_116 = round(float(self.inst.query('DATA:LAST? (@116)')), 2)
        rt_channel_117 = round(float(self.inst.query('DATA:LAST? (@117)')), 2)
        rt_channel_118 = round(float(self.inst.query('DATA:LAST? (@118)')), 2)
        rt_channel_119 = round(float(self.inst.query('DATA:LAST? (@119)')), 2)
        rt_channel_120 = round(float(self.inst.query('DATA:LAST? (@120)')), 2)
        rt_channel_201 = round(float(self.inst.query('DATA:LAST? (@201)')), 2)
        rt_channel_211 = round(float(self.inst.query('DATA:LAST? (@211)')), 2)
        rt_channel_213 = round(float(self.inst.query('DATA:LAST? (@213)')), 2)
        rt_channel_214 = round(float(self.inst.query('DATA:LAST? (@214)')), 2)
        rt_channel_215 = round(float(self.inst.query('DATA:LAST? (@215)')), 2)
        rt_channel_218 = round(float(self.inst.query('DATA:LAST? (@218)')), 2)
        rt_channel_219 = round(float(self.inst.query('DATA:LAST? (@219)')), 2)
        rt_channel_220 = round(float(self.inst.query('DATA:LAST? (@220)')), 2)

        # self.inst.write("OUTPUT:ALARM1:SOURCE (@112)")
        # self.inst.write("OUTPut:ALARm:MODE LATCh")
        # self.inst.write("OUTPut:ALARm:SLOPe NEG")
        # self.inst.write("CALC:LIMIT:UPPER:STATE ON,(@120)")  
        # self.inst.write("CALC:LIMIT:UPPER 23.4,(@120)")  

        # self.inst.write("CALC:LIMIT:UPPER 23.4,(@120")  
        # self.inst.write("ALARM:FAIL LOW, (@112)")
        # self.inst.write("ALARM:ENABLE, (@112)")

        # rt_channel_111 = round(float(self.inst.query('MEAS:TEMP? THER,10000, (@111)')), 2)


        # rt_channel_111 = round(float(self.inst.query('READ (@111)')), 2)
        # rt_channel_111 = round(float(self.inst.query('CALC:AVER:MIN? (@111)')), 2)
        # rt_channel_112 = round(float(self.inst.query('CALC:AVER:MIN? (@112)')), 2)
        # rt_channel_113 = round(float(self.inst.query('CALC:AVER:MIN? (@113)')), 2)
        # rt_channel_114 = round(float(self.inst.query('CALC:AVER:MIN? (@114)')), 2)
        # rt_channel_115 = round(float(self.inst.query('CALC:AVER:MIN? (@115)')), 2)
        # rt_channel_116 = round(float(self.inst.query('CALC:AVER:MIN? (@116)')), 2)
        # rt_channel_117 = round(float(self.inst.query('CALC:AVER:MIN? (@117)')), 2)
        # rt_channel_118 = round(float(self.inst.query('CALC:AVER:MIN? (@118)')), 2)
        # rt_channel_119 = round(float(self.inst.query('CALC:AVER:MIN? (@119)')), 2)
        # rt_channel_120 = round(float(self.inst.query('CALC:AVER:MIN? (@120)')), 2)
        # alarm_limit = self.inst.query("SYSTEM:ALARM?")

        # temp_list = [rt_channel_101, rt_channel_102, rt_channel_103, rt_channel_104, rt_channel_105, rt_channel_106, rt_channel_111, rt_channel_112, rt_channel_113, rt_channel_114, rt_channel_115, rt_channel_116, rt_channel_117, rt_channel_118, rt_channel_119, rt_channel_120]
        temp_list = [rt_channel_111, rt_channel_112, rt_channel_113, rt_channel_114, rt_channel_115, rt_channel_116, rt_channel_117, rt_channel_118, rt_channel_119, rt_channel_120, rt_channel_201, rt_channel_211, rt_channel_213, rt_channel_214, rt_channel_215, rt_channel_218, rt_channel_219, rt_channel_220]
        # temp_list = [rt_channel_111]
        # return temp_list, alarm_limit
       
        return temp_list
    
    
    def read_voltage(self):
        volt_list = []
        self.inst.query('READ?')
        rt_channel_120 = round(float(self.inst.query('CALC:AVER:MIN? (@120)')), 5)
        volt_list = [rt_channel_120]
        return volt_list
    
    def read_alarm(self):
        alarm_reading = self.inst.query("SYSTEM:ALARM?")
        return alarm_reading
    
if __name__ == '__main__':
    data = data_logger_funcs()
    # time.sleep(20)
    print(data.read_channels())
    data.close()
