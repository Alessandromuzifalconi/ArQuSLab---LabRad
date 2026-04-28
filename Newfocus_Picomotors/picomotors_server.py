# ArqusLab <arqusLab@units.it>, February 2024

"""
### BEGIN NODE INFO
[info]
name = picomotors
version = 1.0
description =

[startup]
cmdline = %PYTHON% %FILE%
timeout = 30

[shutdown]
# message = 987654321
# setting = kill
timeout = 30
### END NODE INFO
"""

from os import path
import sys
import telnetlib
import time

# from twisted.python import log
# from twisted.internet.defer import inlineCallbacks

from labrad.server import LabradServer, setting
from pylablib.devices import Newport




class PicomotorsServer(LabradServer):
    """
    Provides access to the Newfocus 8742 picomotor driver.
    """
    name = 'picomotors'

    # @inlineCallbacks
    def initServer(self):
        self._device = Newport.Picomotor8742("192.168.1.91")
        self._device.open()

    @setting(1)
    def get_id(self, c):
        return self._device.get_id()

    @setting(2)
    def reset(self, c):
        return self._device.reset()
    
    @setting(3, 'get position', channel=['i{channel}', 's{channel}'], returns= ['i', '*i'])
    def get_position(self, c, channel):
        """
        Gets position of a channel.

        Accepts channel number (1-4) string 'all'.
        """
        if channel not in (1, 2, 3, 4, 'all'):
            raise ValueError(f'Invalid channel {channel}, should be '
                             '1, 2, 3, 4 or all')

        return(self._device.get_position(channel))
    
    @setting(4, 'relative move', channel='i{channel}', step_count='i{step_count}', returns='_')
    def relative_move(self, c, channel, step_count):
        """
        Moves one of the connected motors of a certain step.

        Accepts channel number (1-4) and step count (integer).
        """
        if channel not in (1, 2, 3, 4):
            raise ValueError(f'Invalid channel {channel}, should be '
                             '1, 2, 3 or 4.')

        # max_step_count = self._config.get('max_step_count')
        # if abs(step_count) > max_step_count:
        #     raise ValueError(f'Absolute step count {abs(step_count)} > '
        #                      f'{max_step_count} is disallowed.')

        self._device.move_by(channel, step_count)

    @setting(5, 'go to', channel='i{channel}', position='i{position}', returns='_')
    def go_to(self, c, channel, position):
        """
        Moves one of the connected motors to absolute position.

        Accepts channel number (1-4) and step count (integer).
        """
        if channel not in (1, 2, 3, 4):
            raise ValueError(f'Invalid channel {channel}, should be '
                             '1, 2, 3 or 4.')

        # max_position = self._config.get('max_position')
        # if abs(position) > max_position:
        #     raise ValueError(f'Absolute step count {abs(position)} > '
        #                      f'{max_position} is disallowed.')

        self._device.move_to(channel, position)

    @setting(6, 'set position reference', channel='i{channel}', position='i{position}', returns='_')
    def set_position_reference(self, c, channel, position):
        """
        Set the current axis position as a reference (the actual motor position stays the same)

        Accepts channel number (1-4) and position (integer).
        """
        if channel not in (1, 2, 3, 4):
            raise ValueError(f'Invalid channel {channel}, should be '
                             '1, 2, 3 or 4.')

        # max_position = self._config.get('max_position')
        # if abs(position) > max_position:
        #     raise ValueError(f'Absolute step count {abs(position)} > '
        #                      f'{max_position} is disallowed.')

        self._device.set_position_reference(channel, position)

__server__ = PicomotorsServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
