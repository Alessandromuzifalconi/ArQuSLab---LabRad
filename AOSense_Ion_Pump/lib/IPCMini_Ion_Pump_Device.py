"""Driver for IPCMini Ion Pump Controller"""
from __future__ import print_function
import serial
from pyvisa.constants import StopBits, Parity
from CRC_calculator import Serial_Functions

class IPC_Mini_Driver():
    """Driver for IPCMini Ion Pump Controller"""

    def __init__(self):
        self.ser = serial.Serial(
            port = 'COM8',
            baudrate = 9600,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            bytesize = serial.EIGHTBITS,
            timeout = 1, # IMPORTANT, can be lower or higher
            # inter_byte_timeout=0.1 # Alternative
            xonxoff=False
            )
        

    def close(self):
        self.ser.close()         

    def read_pressure(self):

        STX = b'\x02'
        ADDR = b'\x80'
        WIN = b'\x38' + b'\x31' + b'\x32'
        COM = b'\x30'
        ETX = b'\x03'
        CRC = Serial_Functions.CRC(self, b'0x38', b'0x31', b'0x32')
        print(CRC)
        CRC = b'\x38\x38'
        newline = b'\x0A' #\n in hex, D for \r

        command = STX + ADDR + WIN + COM + ETX + CRC + newline
        self.ser.write(command)
        msg = self.ser.readline()
        msg = msg[6:14]
        
        if msg == b'':
            msg = int(0)

        else:
            msg = msg.decode('utf-8')
            msg = float(msg)
        return msg





if __name__ == '__main__':
    Turbo = IPC_Mini_Driver()
    print(Turbo.read_pressure())


