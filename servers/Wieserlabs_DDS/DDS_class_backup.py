"""Driver class for FlexDDS-NG Wieserlabs"""
from __future__ import print_function
import time
from pyvisa.constants import StopBits, Parity
import pyvisa
import logging
import os
import pandas as pd
import time
import numpy as np

#date_file = datetime.datetime.now()
#date_file = "%s" % ('set STP0')

#__path__ = "D:/LabRAD/LabRADCodes/servers/DDS_Wieserlabs/"
#filename = date_file
#fullpath = __path__ + str(filename) + ".csv"

#with open(fullpath, "w", newline='') as file:
#    writer = csv.writer(file, delimiter=',')
#    writer.writerow(['channel', 'freq', 'amp', 'phase'])
#    writer.writerow([1, 60e6, 5, 0])

#df = pd.read_csv("D:/LabRAD/LabRADCodes/servers/DDS_Wieserlabs/set STP0.csv")
#channel = int(df.iloc[0][0])
#freq = float(df.iloc[0][1])
#amp = int(df.iloc[0][2])
#phase = int(df.iloc[0][3])

max_amp = '0x3fff'  # 14 bits

def hex2bin(hex_num):
    bits_num = 16
    return bin(int(hex_num, 16))[2:].zfill(bits_num)

def hex2dec(hex_num):
    # convert a hex number to a decimal
    bits_num = 16
    return int(hex_num, bits_num)

def dec2hex(dec_num):
     return hex(int(np.round(dec_num,0)))

# We need to convert a frequency, amp, phase to DDS compatible language
def freq_to_word(f):
    # f in Hz
    if f < 0 or f >= 1e9:
        logging.warning("freq needs to be in range [0,1e9)")
        num = 0
    num = round(2**32/1e9*f) & 0xffff_ffff

    return (f"{num:0{8}x}")


def amp_to_word(amp):
    # amplitude must be larger than 0 and can't be more than 0x3fff.
    # However it is given in percent, so 0x3fff is 100%.
    return f"{round(max(0, min(0x3fff, 0x3fff*amp))):0{4}x}"


def phase_to_word(phase):
    phase = phase % 360
    p = round(2**16 * phase / 360)
    return (f"{p:0{4}x}")


def ASF_func(a, afull=10):
    ASF_dec = int(10**((a - afull)/20) * (2**14 - 1))
    ASF_hex = hex(ASF_dec)
    return ASF_hex


class DDS_funcs():
    """functions for FlexDDS-NG DUAL Wieserlabs"""

    def __init__(self):
        rm = pyvisa.ResourceManager()
        self.inst = rm.open_resource('ASRL12::INSTR')

    def poweroff(self):
        """turn off the instrument"""
        quest = input('are you sure you want to power off the DDS?: y/n')
        if quest == 'y':
            return self.inst.query('poweroff')
        else:
            pass

    def reset(self):
        """Hard reset the device and perform a reboot. It is not recommended to do this frequently,
        especially on Windows operating systems, because it will disconnect and reconnect the USB port"""
        return self.inst.query('reset')

    def reset_channel(self, channel):
        """Hard reset the device and perform a reboot. It is not recommended to do this frequently,
        especially on Windows operating systems, because it will disconnect and reconnect the USB port"""
        return self.inst.query(f'dcp {channel} wr:DDS_RESET=1')

    def set_full_amp(self, channel, freq, phase):
        "set a single tone with max amplitude and a certain frequency and phase"
        freq2ftw = str(freq_to_word(freq))
        amp2atw = max_amp
        phase2ptw = str(phase_to_word(phase))
        return self.inst.query(f'dcp {channel} spi:stp0={amp2atw}{phase2ptw}{freq2ftw}')

    
    def edit_amp(self, channel):
        """allows to match latency and to get ASF from STP.
        To get this you need to activate the 7th and the 24th bit on the CFR2.
        ---> 00000001000000000000000010000000 in binary ---> 0x01000080 in hex"""
        return self.inst.query(f'dcp {channel} spi:cfr2=0x01000080')

    def BNC_IN_A_RISING(self, channel):
        return self.inst.query(f'dcp {channel} wait::BNC_IN_A_RISING')

    def CONFIGURE_ROUTING(self, channel, route, inv, BNC_channel):
        """This functions routes a BNC inputs
        route (string): type of ramp generator (usually OSK or CTRL)
        inv (inversion bit) = 0 or 1. if 1 is set OPMODE is inverted
        BNC_channel (string): A, B, C"""
        if BNC_channel == 'A':
            BNC_channel = bin(5).replace('b', '0')

        if BNC_channel == 'B':
            BNC_channel = bin(8).replace('b', '0')

        if BNC_channel == 'C':
            BNC_channel = bin(11).replace('b', '0')

        return self.inst.query(f'dcp {channel} wr:CFG_{route}=0b010_{inv}_000_{BNC_channel}')

    def ASF_amp(self, channel, amp):
        """set amp from ASF.
            amp (int) in dBm."""
        amp2atw = ASF_func(amp)
        return self.inst.query(f'dcp {channel} spi:asf=' + amp2atw)

        return self.inst.query(f'dcp {channel} wr:CFG_{route}=0b010_{inv}_000_{BNC_channel}')

    def OSK_gate(self, channel):
        """Switch on/off the RF output, i.e. to gate the RF output via the OSK functionality of the AD9910"""
        return self.inst.query(f'dcp {channel} spi:CFR1=0b0000000_11000001_00000010_00000000')

    def DRR(self, channel, dwell_time):
        """dwell_time (float):
        Dwell time for each step  in nanoseconds, must be > 0."""
        rate = int(dwell_time / 4)
        return self.inst.query(f'dcp {channel} spi:DRR=0x{rate:04x}{rate:04x}')

    def DRSS(self, channel, low_amp, high_amp, n_steps=100000):
        """ step_size (float):
        Step size in dBm, must be > 0."""

        step = int((2**(32-14) * (int(ASF_func(high_amp), 16) -
                   int(ASF_func(low_amp), 16)))/n_steps) & 0xffff_ffff
        return self.inst.query(f'dcp {channel} spi:DRSS=0x{step:08x}{step:08x}')

    def DRL(self, channel, low_amp, high_amp):
        """ step_size (float):
        Step size in Hz, must be > 0."""

        # set sweep limits
        low_amp_bin = str(hex2bin(ASF_func(low_amp))) + '00'
        high_amp_bin = str(hex2bin(ASF_func(high_amp))) + '00'

        low_amp_dec = int(low_amp_bin, 2)
        high_amp_dec = int(high_amp_bin, 2)

        return self.inst.query(f'dcp {channel} spi:DRL=0x{high_amp_dec:04x}0000_{low_amp_dec:04x}0000')

    def no_dwell_enable(self, channel, no_dwell):
        """no_dwell (int) = 0(freq), 1(phase), 2(amp)."""
        return self.inst.query(f'dcp {channel} spi:CFR2=0x01{no_dwell}c0080')

    def DDS_reset(self):
        return self.inst.query('dds reset')

    def update(self):
        return self.inst.query('dcp update:u')

    def start(self):
        return self.inst.query('dcp start')

    def close(self):
        return self.inst.close()

    def set_param(self, channel, freq, amp, phase):

        # freq = float(input('set a frequency in Hz: '))
        # amp = int(input('set an amplitude in dBm: '))
        # phase = float(input('set a phase: '))

        freq2ftw = str(freq_to_word(freq))
        amp2atw = ASF_func(amp)
        # amp2atw = max_amp
        phase2ptw = str(phase_to_word(phase))

        return self.inst.query(f'dcp {channel} spi:stp0={amp2atw}{phase2ptw}{freq2ftw}')

    def single_tone(self, channel, freq, amp, phase):
        """ Generate a single tone
        Parameters:
            channel: 0 or 1, the channel on the slot
            freq: Frequency in Hz
            amp: The amplitude in dBm
            phase: The phase of the note in degrees (0..360)"""
        self.DDS_reset()
        self.edit_amp(channel)
        self.set_param(channel, freq, amp, phase)
        self.update()
        self.start()
        self.close()

        print(f"channel {channel} set!")

    def gate(self, channel, amp, freq, phase, route, inv, BNC_channel):
        self.DDS_reset()
        # set OSK bits (switch on/off RF)
        self.OSK_gate(channel)
        # set amplitude
        self.ASF_amp(channel, amp)
        # set frequency and phase, amp. irrelevant locked by OSK
        self.set_param(channel, freq, amp, phase)
        self.update()
        # flush settings in the AD9910
        self.CONFIGURE_ROUTING(channel, route, inv, BNC_channel)
        self.start()

        print(f'gate set on channel {channel}!')

    def trigger_amp_ramp(self, channel, freq, amp, phase, low_amp, high_amp, dwell_time, no_dwell=2):
        # magically it works. I don't why and I don't know how. I changed randomly some bits.
        """ Generate an amplitude ramp
        Parameters:
            channel: 0 or 1, the channel on the slot
            freq: Frequency in Hz
            amp: initial amplitude in dBm
            phase: The phase of the note in degrees (0..360)
            low_amp int: lower ramp limit in dBm
            high_amp int: higher ramp limit in dBm
            dwell time in nanoseconds
            step_size in Hz
            no_dwell (int = 0, 1, 2): (see no_dwell_enable function)
            """

        self.DDS_reset()
        self.edit_amp(channel)
        self.set_param(channel, freq, amp, phase)
        self.update()
        self.BNC_IN_A_RISING(channel)
        self.DRR(channel, dwell_time)
        self.DRSS(channel, low_amp, high_amp)
        self.DRL(channel, low_amp, high_amp)
        # enable ramp generator and set no-dwell high bit (destination: amplitude).
        # Here I changed the fifth '0' with a '2'. Maybe 0 is for frequency and 2 for amplitude?
        # I think: 0 (frequency), 1(phase), 2(amplitude)
        self.no_dwell_enable(channel, no_dwell)
        # IO UPDATE to commit register changes
        self.inst.query('dcp 0 wr:CFG_DRCTL=0b0100_0_000_0101')
        self.update()
        self.start()

        print(f'amplitude ramp set on channel {channel}!')

    # Added by Ale on 03/08/2023.
    # The modulation is working but we need to tune the scale factors etc... 
    def enable_am(self, channel):
        
        # enable parallel data port
        self.inst.query('dcp spi:CFR2=0b00000000_00000000_01010000')
        # set scale factor S0: here S0 = 2^12 = 0x1000
        self.inst.query(f'dcp {channel} wr:AM_S0=0x1000')
        # set offset O0: here O0 = 0 
        self.inst.query(f'dcp {channel} wr:AM_O0=0') 
        # set global offset O: here O = 2^15 = 8000
        self.inst.query(f'dcp {channel} wr:AM_O=0x8000') 
        # choose amplitude modulation, flush coeff.
        self.inst.query(f'dcp {channel} wr:AM_CFG=0x2000_0000') 
        self.update()
        self.start()
        self.close()
       
        print(f'Amplitude modulation set on channel {channel}!')

    # Added by Ale on 03/08/2023.
    def set_fm(self, channel, f_min, f_max, amp):

        # Find minimum and maximum frequency tuning word, i.e. min/max frequencies of the modulation 
        min_freqtuningword = freq_to_word(f_min)  
        max_freqtuningword = freq_to_word(f_max)

        # min ans max of D values (modulation data, see manual). Divided by 2^15 due to AD9910 15 bits
        d_min = hex2dec(min_freqtuningword)/2**15
        d_max = hex2dec(max_freqtuningword)/2**15

        # find scaling factor S0 and offset O:
        S0 = str(dec2hex((d_max - d_min)*2**12 / (2**15 - 1 + 2**15)))
        O = str(dec2hex((d_min*(2**15 - 1) - d_max*(-2**15)) / (2**15 - 1 + 2**15)))
        
        # set amplitude to amp and set FTW to zero (pg. 46 of the manual)
        self.edit_amp(channel)
        self.set_param(channel, 0, amp, 0)
        self.update()
        """allows to match latency and to get ASF from STP.
        To get this you need to activate the 7th and the 24th bit on the CFR2.
        ---> 00000001000000000000000010000000 in binary ---> 0x01000080 in hex"""
        # sinc filter and sine output (not needed)
        # ob is a prefix indicating that the bits are in binary
        self.inst.query(f'dcp {channel} spi:CFR1=0b_01000001_00000000_00000000')
        # enable parallel data port, set FM gain to 15 -> maxim from AD9910 datasheet for FM gain. These are the last 4 bits (1111) of the string below
        self.inst.query(f'dcp {channel} spi:CFR2=0b_00000000_00000000_01011111')
        # set scale factor S0
        self.inst.query(f'dcp {channel} wr:AM_S0={S0}')
        # set channel offset O0: here O0 = 0 
        self.inst.query(f'dcp {channel} wr:AM_O0=0') 
        # set global offset O:
        self.inst.query(f'dcp {channel} wr:AM_O={O}') 
        # choose frequency modulation, flush coeff.
        self.inst.query(f'dcp {channel} wr:AM_CFG=0x2000_0002') 
        self.update()
        self.start()
        self.close()
        
        print(f'Frequency modulation set on channel {channel}!')

if __name__ == '__main__':
    DDS = DDS_funcs()
   # DDS.single_tone(0, 120e6, 3, 0)
    #DS.gate(0, 5, 30e6, 0, 'OSK', 0, 'A')
    # DDS.trigger_amp_ramp(0, 30e6, 5, 0, 0, 5, 600)
    DDS.set_fm(0, 85e6, 135e6, 3)
