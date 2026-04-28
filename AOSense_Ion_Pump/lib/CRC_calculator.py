

class Serial_Functions():
    """Functions to calculate parts of the message to send to the ion pump controller """

    def CRC(self, WIN1, WIN2, WIN3):

        scale = 16         ## equals to hexadecimal
        num_of_bits = 8

        ADDR = b'0x80'
        COM = b'0x30'
        ETX = b'0x03'

        ADDR_bin = bin(int(ADDR, scale))[2:].zfill(num_of_bits)
        WIN1_bin = bin(int(WIN1, scale))[2:].zfill(num_of_bits)
        WIN2_bin = bin(int(WIN2, scale))[2:].zfill(num_of_bits)
        WIN3_bin = bin(int(WIN3, scale))[2:].zfill(num_of_bits)
        COM_bin = bin(int(COM, scale))[2:].zfill(num_of_bits)
        ETX_bin = bin(int(ETX, scale))[2:].zfill(num_of_bits)

        y = int(ADDR_bin, 2) ^ int(WIN1_bin, 2) ^ int(WIN2_bin, 2) ^ int(WIN3_bin, 2) ^ int(COM_bin, 2) ^ int(ETX_bin, 2)
        CRC_bin = str(('{0:b}'.format(y)))
        CRC_hex = str(hex(int(CRC_bin, 2)))

        CRC_hex = CRC_hex.replace("0x","")
        CRC_hex = CRC_hex.encode('ascii')
        CRC_hex.hex()
        CRC = bytes(CRC_hex.hex(), 'utf-8')
        return b'0x' + CRC

if __name__ == '__main__':
    Turbo = Serial_Functions()
    # print(Turbo.CRC(b'0x38', b'0x31', b'0x32'))