"""Driver class for alarms"""
from __future__ import print_function
import pyvisa
import http.client, urllib
import smtplib, ssl


#libraries needed to use notify.run
from notify_run import Notify 
import requests

#library used for Twilio, old lab alarm software
from trycourier import Courier


class oscilloscope_funcs():
    """functions for FlexDDS-NG DUAL Wieserlabs"""

    def __init__(self):
        rm = pyvisa.ResourceManager()
        self.inst = rm.open_resource('USB0::0x0AAD::0x01D6::201287::INSTR')


    def turn_on_channel_1(self):
        CH1 = 'ON'
        return self.inst.write(f'CHAN1:STAT {CH1}')
    
    def turn_on_channel_2(self):
        CH2 = 'ON'
        return self.inst.write(f'CHAN1:STAT {CH2}')
    
    def turn_on_channel_3(self):
        CH3 = 'ON'
        return self.inst.write(f'CHAN1:STAT {CH3}')
    
    def turn_on_channel_4(self):
        CH4 = 'ON'
        return self.inst.write(f'CHAN1:STAT {CH4}')

    def turn_off_channel_1(self):
        CH1 = 'OFF'
        return self.inst.write(f'CHAN1:STAT {CH1}')
    
    def turn_off_channel_2(self):
        CH2 = 'OFF'
        return self.inst.write(f'CHAN1:STAT {CH2}')
    
    def turn_off_channel_3(self):
        CH3 = 'OFF'
        return self.inst.write(f'CHAN1:STAT {CH3}')
    
    def turn_off_channel_4(self):
        CH4 = 'OFF'
        return self.inst.write(f'CHAN1:STAT {CH4}')

    def set_vertical_scale(self, channel, scale):
        if channel == 'CH1':
            set_scale = self.inst.write(f'CHANnel1:SCALe {scale}')
        if channel == 'CH2':
            set_scale = self.inst.write(f'CHANnel2:SCALe {scale}')
        if channel == 'CH3':
            set_scale = self.inst.write(f'CHANnel3:SCALe {scale}')
        if channel == 'CH3':
            set_scale = self.inst.write(f'CHANnel4:SCALe {scale}')

        return set_scale
    
    def read_voltage(self, channel):
        #raading CH1 DC value
        self.inst.write(f'DVM1:ENABle\n')
        self.inst.write(f'DVM1:SOUR ' + channel + '\n')
        self.inst.write(f'DVM1:TYPE DC\n')
        CH1_voltage = self.inst.query(f'DVM1:RES?')
        CH1_voltage.rfind('\n')
        CH1_voltage = CH1_voltage[:13]
        CH1_voltage = float(CH1_voltage)
        CH1_voltage = round(CH1_voltage, 3)
        return CH1_voltage

    def close(self):
        return self.inst.close()


class alarm_funcs():
    def send_email(self, message):
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = "arquslab@gmail.com"  

        #receivers
        francesco_email = "francesco.scazza@units.it"  
        omar_email = "omar.abdelkarim@ino.cnr.it"  
        alessandro_email = "alessandrothomas.muzifalconi@phd.units.it"  
        riccardo_email = "riccardo.panza@phd.units.it"
        sara_email = "sara.sbernardori@phd.units.it"
        password = 'jpef iktl phdq dmek'

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, [francesco_email, omar_email, alessandro_email, riccardo_email, sara_email], message)
            # server.sendmail(sender_email, [omar_email], message)


if __name__ == '__main__':
    AC = alarm_funcs()
    # AC.send_email('ciao!')

