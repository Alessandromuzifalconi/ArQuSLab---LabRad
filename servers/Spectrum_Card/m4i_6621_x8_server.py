# ArQuSLab <arquslab@units.it>, May 2023
"""
### BEGIN NODE INFO
[info] :()
name = m4i.6621-x8
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

from F_spectrum_m4i_6621_x8_device_v2 import SpectrumM4i6621x8Device
from twisted.internet import task
from twisted.internet import reactor
from labrad.server import LabradServer, setting


import matplotlib.pyplot as plt

import numpy as np

from labrad import units


class spectrum_card_server(LabradServer):
    name = "m4i.6621-x8"

    # @inlineCallbacks
    def initServer(self):  # Do initialization here
        self._device = None
        self._device = SpectrumM4i6621x8Device()
        self._device.open()

    @setting(1, returns = 's')
    def _card_type(self, c):
        """returns the model of the card."""
        return self._device.card_type

    @setting(2, returns = 'w')
    def _serial_number(self, c):
        """returns the serial number of the Spectrum M4i.6621-x8 card."""
        return self._device.serial_number

    @setting(3, returns = 'w')
    def _bytes_per_sample(self, c):
        """returns the used number of bytes per sample."""
        return self._device.bytes_per_sample
   
    @setting(4)
    def _enable_ch_0(self, c):
        return self._device.enable_ch_0()

    @setting(5)
    def _enabled_channel_count(self, c):
        """check how many channels are opened (int)."""
        return self._device.enabled_channel_count

    @setting(6)
    def _max_sample_rate(self, c):
        """check max sample rate."""
        return self._device.max_sample_rate

    @setting(7, rate = 'w')
    def _sample_rate(self, c, rate):
        """set sample rate."""
        return self._device.set_sample_rate(rate)

    @setting(8, returns = 'w')
    def _get_sample_rate(self, c):
        """get sample rate."""
        return self._device.sample_rate

    @setting(9, n_loops = 'w')
    def _loops(self, c, n_loops):
        """set number of loops."""
        return self._device.set_loops(n_loops)
    
    @setting(10, returns = ['s', 'w'])
    def _get_loops(self, c,):
        """get number of loops."""
        return self._device.get_loops

    @setting(11, amp = 'w')
    def _amp_CH0(self, c, amp):
        """set amplitude of CH 0."""
        self._device.amplitude_ch_0(amp)
    
    @setting(12, returns = 'w')
    def _get_amp_CH0(self, c,):
        """get amplitude of CH 0."""
        return self._device.get_amplitude_ch_0

    @setting(13, amp = 'w')
    
    def _amp_CH1(self, c, amp):
        """set amplitude of CH 1."""
        return self._device.amplitude_ch_1(amp)
    
    @setting(14, returns = 'w')
    def _get_amp_CH1(self, c,):
        """get amplitude of CH 1."""
        return self._device.get_amplitude_ch_1

    @setting(15, activate = 'b')
    def _enable_out_CH0(self, c, activate):
        """CH0 start output."""
        self._device.enable_out_ch_0(activate)
    
    @setting(16, returns = 'b')
    def _get_enabled_out_CH0(self, c,):
        """get info about CH0 output."""
        return self._device.get_enabled_out_ch_0

    @setting(17, returns = 'w')
    def _FPGA_temperature(self, c,):
        """get FPGA temperature."""
        return self._device.temperature_base_control

    @setting(18, size = 'w')
    def _mem_size(self, c, size):
        """set memory size."""
        return self._device.set_mem_size(size)
    
    @setting(19, returns = 'w')
    def _get_mem_size(self, c):
        """get memory size."""
        return self._device.mem_size

    @setting(20)
    def _enable_trigger(self, c):
        """enables trigger."""
        return self._device.enable_trigger()

    @setting(21, activate = 'b', array = '*v', stop = 'b')
    def _transfer_numpy_array_to_card(self, c, activate, array, stop):
        """transfers the signal to the card."""
        self._device.transfer_numpy_array_to_card(array, stop)
    
    @setting(22)
    def _start_and_enable_trigger(self, c):
        """starts the card if the trigger signal arrives."""
        return self._device.start_and_enable_trigger()
    
    @setting(23)
    def _start_and_wait_timeout(self, c, timeout):
        """starts the signale and waits timeout."""
        return self._device.start_and_wait_timeout(timeout)

    @setting(24)
    def _start_and_enable_gate(self, c):
        """starts the signale and activate gate replay mode."""
        return self._device.gate_replay_mode()

    @setting(25, segment_size = 'w')
    def _start_and_enable_multiple_replay_mode(self, c, segment_size):
        """starts the signale and ativate gate replay mode."""
        return self._device.multiple_replay_mode(segment_size)

    @setting(26)
    def _close(self, c):
        """close device."""
        return self._device.close()

    @setting(27)
    def _open(self, c):
        """open device."""
        return self._device.open()

    @setting(28)
    def _reset(self, c):
        """reset device."""
        return self._device.reset()

    @setting(29)
    def _start_DMA(self, c):
        """start DMA buffer."""
        return self._device.start_DMA()

    @setting(30, max_segments = 'w', starting_step = 'w')
    def _sequence_mode(self, c, max_segments, starting_step):
        """activate sequence mode, set number of maximum segments and choose starting step."""
        return self._device.sequence_mode(max_segments, starting_step)

    @setting(31, segment = 'w', segment_size = 'w')
    def _set_up_segment(self, c, segment, segment_size):
        """set up the segment data memory."""
        return self._device.set_up_segment(segment, segment_size)

    @setting(32, current_step = 'w', current_segment = 'w', loop = 'w', next_step = 'w', end_loop_on_trig = 'b')
    def _set_up_sequence_memory(self, c, current_step, current_segment, loop, next_step, end_loop_on_trig):
        """set up sequence memory."""
        return self._device.set_up_sequence_memory(current_step, current_segment, loop, next_step, end_loop_on_trig)

    @setting(33, returns = 'w')
    def _max_number_of_segments(self, c):
        """returns the max number of segments the memory can be divided into."""
        return self._device.max_number_of_segments
    
    @setting(34, returns='w')
    def get_param(self, c, setting, kind):
        "Returns arbitrary parameter from spectrum card. expects a string - kind int32"
        if kind == 'int32':
            return self._device._get_param(setting, kind)
        elif kind=='int64':
            return self._device._get_param(setting, kind)


__server__ = spectrum_card_server()
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)

