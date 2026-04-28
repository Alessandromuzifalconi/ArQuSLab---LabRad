from os import path
import sys
import numpy as np
import ctypes
import time
from F_wavegen_v3 import *

# Since the example code does not have an explicit license, we need to
# dynamically load the library.
_root = path.abspath(path.join('//arqus-nas/ArQuS Shared/LabRad/servers/Spectrum_Card/lib/'))
sys.path.append(_root)

import pyspcm  # noqa: E402
from pyspcm import int32, int64, uint64, ptr16, c_void_p, byref, cast  # noqa: E402
import spcm_tools  # noqa: E402
from spcm_tools import szTypeToName  # noqa: E402


def memcopy(buffer, array):
    """Helper function to copy numpy array to buffer used for DMA."""
    import ctypes

    if array.shape[0] == 1:
        ctypes.memmove(buffer, array.ctypes.data_as(ptr16), 2 * array.size)
    else:
        new_array = np.zeros(2 * array.shape[1], dtype=np.int16)
        new_array[::2] = array[0, :]
        new_array[1::2] = array[1, :]

        ctypes.memmove(
            buffer,
            new_array.ctypes.data_as(ptr16),
            2 * new_array.size)


class SpectrumM4i6621x8Device:
    """
    Wrapper class for the Spectrum M41-6631-x8 AWG card.

    Arguments:
        address (str, optional):
            The address of the card, '/dev/spcm0' by default. Only needs to be
            changed when multiple cards are used inside the same computer.
    """
    DAC_RANGE = 2**15 - 1  # half of the output levels due to polarity

    def __init__(self, address: str = '/dev/spcm0'):
        self._address = address
        self._card = None

    def open(self) -> None:
        """
        Open the device and lock access for other processes.

        Raises:
            RuntimeError: If the device could not be opened.
        """
        if self._card is not None:
            self.close()

        address = pyspcm.create_string_buffer(self._address.encode('ascii'))
        self._card = pyspcm.spcm_hOpen(address)
        if self._card is None:
            raise RuntimeError(f'Card {self._address} could not be found.')

    def close(self) -> None:
        """
        Close the device and unlock access for other processes.
        """
        if self._card is None:
            return 'ciao'

        pyspcm.spcm_vClose(self._card)
        self._card = None

    def reset(self) -> None:
        """
        Reset the device.
        """
        should_open = True

        if self._card is None:
            should_open = False
            self.open()

        pyspcm.spcm_dwSetParam_i32(
            self._card, pyspcm.SPC_M2CMD, pyspcm.M2CMD_CARD_RESET)

        # need to close and open again to finalize reset
        self.close()

        if should_open:
            self.open()

    @property
    def card_type(self) -> int:
        """Card type (int)."""
        sCardName = self._get_param('SPC_PCITYP')
        return szTypeToName(sCardName)

    def start_and_enable_trigger(self) -> None: # modified by Fabrizio on 10/10/2025
        """
        Start the output of the card and enable the trigger.
        """
        self._assert_card()
        pyspcm.spcm_dwSetParam_i32(
            self._card,
            pyspcm.SPC_M2CMD,
            pyspcm.M2CMD_CARD_START | pyspcm.M2CMD_CARD_ENABLETRIGGER | pyspcm.M2CMD_CARD_WAITTRIGGER)

    def stop(self) -> None:
        """
        Stop the output of the card.
        """
        self._assert_card()
        pyspcm.spcm_dwSetParam_i32(
            self._card, pyspcm.SPC_M2CMD, pyspcm.M2CMD_CARD_STOP)

    def enable_ch_0(self) -> None:
        """
        Enable channel 0 and disable channel 1.

        Note that this does not enable the output of channel 0, see
        enable_out_ch_0.
        """
        self._assert_card()
        pyspcm.spcm_dwSetParam_i64(
            self._card, pyspcm.SPC_CHENABLE, pyspcm.CHANNEL0)

    def enable_ch_1(self) -> None:
        """
        Enable channel 1 and disable channel 0.

        Note that this does not enable the output of channel 1, see
        enable_out_ch_1.
        """
        self._assert_card()
        pyspcm.spcm_dwSetParam_i64(
            self._card, pyspcm.SPC_CHENABLE, pyspcm.CHANNEL1)

    def enable_ch_all(self) -> None:
        """
        Enable channel 0 and 1.

        Note that this does not enable the output of the channel, see
        enable_out_ch_0 and enable_out_ch_1.
        """
        self._assert_card()
        pyspcm.spcm_dwSetParam_i64(
            self._card, pyspcm.SPC_CHENABLE, pyspcm.CHANNEL0 | pyspcm.CHANNEL1)

    def replay_standard_continous_mode(self) -> None:
        """
        Set the card to replay the standard continous mode.
        """
        self._assert_card()
        pyspcm.spcm_dwSetParam_i32(
            self._card, pyspcm.SPC_CARDMODE, pyspcm.SPC_REP_STD_CONTINUOUS)

    def transfer_numpy_array_to_card(self, array: np.ndarray, stop) -> None:
        """
        Transfer data from a numpy array to the memory of the card for replay.

        Arguments:
            array (numpy.ndarray):
                Numpy array with the data to be transferred. Here, the first
                axis corresponds to the channel and the second axis to the
                samples as a function of time.

        Raises:
            ValueError: If the array shape is invalid.

        Note:
            The values of the array are scaled to the range of the DAC (signed
            16-bit integer) and should only take values between -1 and 1.
            Values outside this range should be avoided since they can lead to
            undefined behavior.
        """
        self._assert_card()

        # stop card if it is running
        if stop == True:
            self.stop()

        enabled_channel_count = self.enabled_channel_count

        # reshape array if only single channel is enabled
        if enabled_channel_count == 1 and array.ndim == 1:
            array = array[np.newaxis, :]

        # ensure array is 2D
        if array.ndim != 2:
            raise ValueError(
                f'Array must be 2D, but is {array.ndim}D.')

        # ensure first axis matches enabled channel count
        if array.shape[0] != enabled_channel_count:
            raise ValueError(
                f'Array must have first axis of length {enabled_channel_count}'
                f', but has length{array.shape[0]}.')

        sample_count = array.shape[1]

        # # ensure second axis matches memory size
        # if sample_count != self.mem_size:
        #     raise ValueError(
        #         f'Array must have second axis of length {self.mem_size}, but'
        #         f' has length {sample_count}.')

        # convert array to 16 bit integer for transfer to card memory
        array = (self.DAC_RANGE * array).astype(np.int16)

        buffer_size = uint64(
            sample_count * self.bytes_per_sample * enabled_channel_count)
        buffer_pointer = c_void_p()
        continouous_buffer_length = uint64(0)

        # allocate buffer according to example code from card manufacturer
        pyspcm.spcm_dwGetContBuf_i64(
            self._card, pyspcm.SPCM_BUF_DATA,
            byref(buffer_pointer),
            byref(continouous_buffer_length))

        if continouous_buffer_length.value < buffer_size.value:
            buffer_pointer = spcm_tools.pvAllocMemPageAligned(
                buffer_size.value)

        # copy data to buffer
        buffer = cast(buffer_pointer, ptr16)
        memcopy(buffer, array)
        
        # transfer buffer to card memory
        pyspcm.spcm_dwDefTransfer_i64(
            self._card, pyspcm.SPCM_BUF_DATA, pyspcm.SPCM_DIR_PCTOCARD,
            int32(0), buffer_pointer, uint64(0), buffer_size)

        pyspcm.spcm_dwSetParam_i32(
            self._card,
            pyspcm.SPC_M2CMD,
            pyspcm.M2CMD_DATA_STARTDMA | pyspcm.M2CMD_DATA_WAITDMA)

    def start_DMA(self) -> None:
        """
        Set the card to replay the standard continous mode.
        """
        pyspcm.spcm_dwSetParam_i32(
            self._card,
            pyspcm.SPC_M2CMD,
            pyspcm.M2CMD_DATA_STARTDMA | pyspcm.M2CMD_DATA_WAITDMA)

    def start_and_wait_timeout(self, timeout) -> None:
        """
        Start the output of the card and wait end of timeout.
        """
        self._assert_card()

        pyspcm.spcm_dwSetParam_i32(self._card, pyspcm.SPC_TIMEOUT, timeout)

        Out = pyspcm.spcm_dwSetParam_i32(
            self._card,
            pyspcm.SPC_M2CMD,
            pyspcm.M2CMD_CARD_START | pyspcm.M2CMD_CARD_ENABLETRIGGER | pyspcm.M2CMD_CARD_WAITREADY)

        if Out == pyspcm.ERR_TIMEOUT:
            pyspcm.spcm_dwSetParam_i32(
                self._card, pyspcm.SPC_M2CMD, pyspcm.M2CMD_CARD_STOP)

    def multiple_replay_mode(self, segment_size) -> None:  # Omar
        """
        Set the card to gate replay mode.
        """
        self._assert_card()
        pyspcm.spcm_dwSetParam_i32(
            self._card, pyspcm.SPC_CARDMODE, pyspcm.SPC_REP_STD_MULTI)
        self._set_param('SPC_SEGMENTSIZE', segment_size, 'int64')

    def gate_replay_mode(self) -> None:  # Omar
        """
        Set the card to gate replay mode.
        """
        self._assert_card()
        pyspcm.spcm_dwSetParam_i32(
            self._card, pyspcm.SPC_CARDMODE, pyspcm.SPC_REP_STD_GATE)

    def sequence_mode(self, max_segments, starting_step) -> None:  # Omar
        """
        Set the card to sequence replay mode.
        """
        self._assert_card()
        pyspcm.spcm_dwSetParam_i32(
            self._card, pyspcm.SPC_CARDMODE, pyspcm.SPC_REP_STD_SEQUENCE)
        self._set_param('SPC_SEQMODE_MAXSEGMENTS', max_segments, 'int64')

        #Defines which of all defined steps in the sequence memory will be used first directly after the card start.
        self._set_param('SPC_SEQMODE_STARTSTEP', starting_step, 'int64')

    def set_up_segment(self, segment, segment_size) -> None:  # Omar
        """
        Set up the segment data memory.
        """
        self._assert_card()
        self._set_param('SPC_SEQMODE_WRITESEGMENT', segment, 'int64')
        self._set_param('SPC_SEQMODE_SEGMENTSIZE', segment_size, 'int64')

    def set_up_sequence_memory(self, current_step, current_segment, loop, next_step, end_loop_on_trig) -> None:  # Omar
        """
        Set up the sequence memory.
        """
        self._assert_card()

        current_step                                #current step is Step#0
        current_segment                             #associated with data memory segment 0
        loop                                        #pattern will be repeated 10 times
        next_step                                   #next step is Step#1

        if end_loop_on_trig == True:
            pyspcm.spcm_dwSetParam_i64(self._card, pyspcm.SPC_SEQMODE_STEPMEM0 + current_step, (pyspcm.SPCSEQ_ENDLOOPONTRIG << 32) | (loop << 32) | (next_step << 16) | (current_segment))

        elif end_loop_on_trig == False:
            pyspcm.spcm_dwSetParam_i64(self._card, pyspcm.SPC_SEQMODE_STEPMEM0 + current_step, (pyspcm.SPCSEQ_ENDLOOPALWAYS << 32) | (loop << 32) | (next_step << 16) | (current_segment))


    def global_software_trigger(self):
        """
        Enable the global software trigger for the card.
        """
        self._assert_card()

        pyspcm.spcm_dwSetParam_i32(
            self._card, pyspcm.SPC_TRIG_ORMASK, pyspcm.SPC_TMASK_SOFTWARE)

        params = (
            pyspcm.SPC_TRIG_ANDMASK,
            pyspcm.SPC_TRIG_CH_ORMASK0,
            pyspcm.SPC_TRIG_CH_ORMASK1,
            pyspcm.SPC_TRIG_CH_ANDMASK0,
            pyspcm.SPC_TRIG_CH_ANDMASK1)

        for param in params:
            pyspcm.spcm_dwSetParam_i32(self._card, param, 0)

    @property
    def serial_number(self) -> int:
        """Serial number of the card (int)."""
        return self._get_param('SPC_PCISERIALNO')

    @property
    def max_number_of_segments(self) -> int:
        """ Returns the maximum number of segments the memory can be divided into (int)."""
        return self._get_param('SPC_SEQMODE_AVAILMAXSEGMENT')

    @property
    def bytes_per_sample(self) -> int:
        """Number of bytes per sample (int)."""
        return self._get_param('SPC_MIINST_BYTESPERSAMPLE')

    @property
    def sample_rate(self) -> int:
        """Sample rate of the card, must be smaller than 1.25 GHz (int)."""
        return self._get_param('SPC_SAMPLERATE', 'int64')

    # @sample_rate.setter
    def set_sample_rate(self, rate: int):
        if rate <= 0 or rate > 1250_000_000:
            raise ValueError(
                'Invalid sample rate, must be > 0 and <= 1250_000_000.')

        self._set_param('SPC_SAMPLERATE', rate, 'int64')

    @property
    def max_sample_rate(self) -> int:
        """Check max sample rate of the card. 625MHz for M4i.6621-x8 (int)."""
        return self._get_param('SPC_PCISAMPLERATE', 'int64')

    @property
    def clock_out_enable(self) -> bool:
        """Clock output signal enabled (bool)."""
        return self._get_param('SPC_CLOCKOUT') == 1

    @clock_out_enable.setter
    def clock_out_enable(self, enable: bool):
        return self._set_param('SPC_CLOCKOUT', 1 if enable is True else 0)

    @property
    def trigger_out(self) -> bool:
        """Trigger output enabled (bool)."""
        return self._get_param('SPC_TRIGGEROUT') == 1

    @trigger_out.setter
    def trigger_out(self, enable: bool):
        enable = 1 if enable is True else 0
        self._set_param('SPC_TRIGGEROUT', enable)

    def enable_trigger(self):
        """
        Enable the global software trigger for the card.
        """
        self._assert_card()

        # Enable Trigger
        # set trigger termination (0 --> 1MOhm, 1 --> 50 Ohm)
        pyspcm.spcm_dwSetParam_i32(self._card, pyspcm.SPC_TRIG_TERM, 0)                                     #1 is for 50Ohm termination, 0 is for 1MOhm termination
        # pyspcm.spcm_dwSetParam_i32 (self._card, pyspcm.SPC_TRIG_EXT0_ACDC, 1)                             #set trigger termination (0 --> DC, 1 --> AC)
        # lower Window Trigger level set to 0.0 V
        pyspcm.spcm_dwSetParam_i32(
            self._card, pyspcm.SPC_TRIG_EXT0_LEVEL0, 2500)
        # upper Window Trigger level set to 1.0 V
        pyspcm.spcm_dwSetParam_i32(
            self._card, pyspcm.SPC_TRIG_EXT0_LEVEL1, 2500)
        # pyspcm.spcm_dwSetParam_i32 (self._card, pyspcm.SPC_TRIG_EXT0_MODE, pyspcm.SPC_TM_HIGH)            #Setting up main window trigger for entering
        # pyspcm.spcm_dwSetParam_i32 (self._card, pyspcm.SPC_TRIG_EXT0_MODE, pyspcm.SPC_TM_WINENTER)        #Setting up main window trigger for entering
        # Setting up primary trigger for rising edges
        pyspcm.spcm_dwSetParam_i32(
            self._card, pyspcm.SPC_TRIG_EXT0_MODE, pyspcm.SPC_TM_POS)

        # Enable external trg0 within the OR mask
        pyspcm.spcm_dwSetParam_i32(
            self._card, pyspcm.SPC_TRIG_ORMASK, pyspcm.SPC_TMASK_NONE | pyspcm.SPC_TMASK_EXT0)

    @property
    def get_amplitude_ch_0(self) -> int:
        """Amplitude of channel 0 in mV between 80 and 2000 (int)."""
        return self._get_param('SPC_AMP0')

    # @amplitude_ch_0.setter
    def amplitude_ch_0(self, amplitude: int) -> int:
        if amplitude < 80 or amplitude > 2000:
            raise ValueError(
                f'Invalid amplitude {amplitude}, must be >= 80 and <= 2000.')

        self._set_param('SPC_AMP0', amplitude)

    @property
    def get_amplitude_ch_1(self) -> int:
        """Amplitude of channel 1 in mV between 80 and 2000 (int)."""
        return self._get_param('SPC_AMP1')

    # @amplitude_ch_1.setter
    def amplitude_ch_1(self, amplitude: int) -> int:
        if amplitude < 80 or amplitude > 2000:
            raise ValueError(
                f'Invalid amplitude {amplitude}, must be >= 80 and <= 2000.')

        self._set_param('SPC_AMP1', amplitude)

    @property
    def get_loops(self) -> int:
        """
        Number of loops in the replay mode (int).

        Note that 0 corresponds to an infinite number of loops until the card
        is stopped.
        """

        loops = self._get_param('SPC_LOOPS', 'int64')

        if loops == 0:
            return 'infinite'
        else:
            return loops

    # @loops.setter
    def set_loops(self, count: int) -> int:
        if count < 0 or count >= 4_000_000:
            raise ValueError(
                f'Invalid loop count {count}, must be >= 0 and < 4_000_000.')

        self._set_param('SPC_LOOPS', count, 'int64')

    @property
    def get_enabled_out_ch_0(self) -> bool:
        """Output of channel 0 enabled (bool)."""
        return self._get_param('SPC_ENABLEOUT0', 'int64') == 1

    # @enable_out_ch_0.setter
    def enable_out_ch_0(self, enable: bool) -> bool:
        enable = 1 if enable is True else 0
        self._set_param('SPC_ENABLEOUT0', enable, 'int64')

    @property
    def get_enable_out_ch_1(self) -> bool:
        """Output of channel 1 enabled (bool)."""
        return self._get_param('SPC_ENABLEOUT1', 'int64') == 1

    # @enable_out_ch_1.setter
    def enable_out_ch_1(self, enable: bool):
        enable = 1 if enable is True else 0
        self._set_param('SPC_ENABLEOUT1', enable, 'int64')

    @property
    def mem_size(self) -> int:
        """
        Memory size used for storing samples, must be multiple of 8 and
        smaller than 4_000_000_000 (int).
        """
        return self._get_param('SPC_MEMSIZE', 'int32')

    # @mem_size.setter
    def set_mem_size(self, size: int) -> int:
        if size < 32 or size > 2_000_000_000:
            raise ValueError(
                'Invalid memory size, must be > 32 and < 2_000_000_000.')

        if size % 8 != 0:
            raise ValueError('Invalid memory size, must be a multiple of 8.')

        self._set_param('SPC_MEMSIZE', size, 'int32')

    @property
    def enabled_channel_count(self) -> int:
        """Number of enabled channels (int)."""
        return self._get_param('SPC_CHCOUNT')

    @property
    def temperature_base_control(self) -> int:
        """Temperature inside FPGA (int)."""
        return self._get_param('SPC_MON_TC_BASE_CTRL')

    @property
    def temperature_module_1(self) -> int:
        """Temperature of amplifier front-end (int)."""
        return self._get_param('SPC_MON_TC_MODULE_1')

    def __del__(self):
        self.close()

    def _assert_card(self):
        if self._card is None:
            raise RuntimeError('Device has been closed.')

    def _get_param(self, param_name: str, kind: str = 'int32') -> int:
        self._assert_card()

        param_value = self._create_param(kind)
        args = (self._card, getattr(pyspcm, param_name), byref(param_value))
        if kind == 'int32':
            pyspcm.spcm_dwGetParam_i32(*args)
        else:
            pyspcm.spcm_dwGetParam_i64(*args)

        return param_value.value

    def _set_param(self, param_name: str, param_value: int,
                   kind: str = 'int32') -> None:
        self._assert_card()

        args = (self._card, getattr(pyspcm, param_name),
                self._create_param(kind, param_value))

        if kind == 'int32':
            pyspcm.spcm_dwSetParam_i32(*args)
        else:
            pyspcm.spcm_dwSetParam_i64(*args)

    @staticmethod
    def _create_param(kind: str = 'int32', value: int = 0):
        if kind not in ('int32', 'int64'):
            raise ValueError(
                f'Invalid parameter type {kind}, must be "int32" or "int64".')

        if isinstance(value, int) is False:
            raise ValueError(
                f'Invalid parameter value {value}, must be integer.')

        if kind == 'int32':
            return int32(value)
        else:
            return int64(value)
