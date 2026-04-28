import time
import datetime
import csv



def params():
    channel_p = input('choose channel to edit (0 or 1): ')
    freq_p = float(input('set a frequency in Hz: '))
    amp_p = int(input('set an amplitude in dBm: '))
    phase_p = float(input('set a phase: '))
    return channel_p, freq_p, amp_p, phase_p

channel, freq, amp, phase = params()

date_file = datetime.datetime.now()
date_file = "%s" % ('set STP0')

__path__ = "D:/LabRAD/LabRADCodes/servers/DDS_Wieserlabs/"
filename = date_file
fullpath = __path__ + str(filename) + ".csv"

with open(fullpath, "a+", newline='') as file:
    writer = csv.writer(file, delimiter=',')
    writer.writerow(['channel', 'freq', 'amp', 'phase'])
    writer.writerow([channel, freq, amp, phase])