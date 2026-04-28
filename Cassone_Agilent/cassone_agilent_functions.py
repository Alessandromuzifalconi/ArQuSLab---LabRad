"""Driver class for Agilent Cassone"""
from __future__ import print_function
import numpy as np
import pyvisa
from pyvisa.constants import StopBits, Parity


class cassone_funcs:
    """Driver for Agilent Cassone"""

    def __init__(self, device):
        rm = pyvisa.ResourceManager()
        self.inst = rm.open_resource(device)
        # print(rm.list_resources())

    def close(self):
        self.inst.close()

    def set_freq(self, frequency):
        freq = self.inst.write(f':FREQ {frequency} MHz')
        return freq

    def set_amp(self, amplitude):
        freq = self.inst.write(f':POW {amplitude} DBM')
        return freq

    def read_freq_list(self):
        return self.inst.query(':LIST:FREQ?')

    def make_freq_list(self, n_vector, values):
        freq_matrix = np.zeros((n_vector, 3))
        for i in range(n_vector):
            for j in range(3):
                freq_matrix[i][j] = np.asarray(values)[i][j]
        vectors_matrix = np.zeros((1, n_vector), dtype=object)
        for i in range(n_vector):
            if freq_matrix[i][0] != freq_matrix[i][1]:
                if freq_matrix[i][0] < freq_matrix[i][1]:
                    vectors_matrix[0][i] = np.arange(freq_matrix[i][0], freq_matrix[i][1]+freq_matrix[i][2], freq_matrix[i][2])*1e6
                elif freq_matrix[i][0] > freq_matrix[i][1]:
                    vectors_matrix[0][i] = np.arange(freq_matrix[i][0], freq_matrix[i][1]-freq_matrix[i][2], -freq_matrix[i][2])*1e6
            elif freq_matrix[i][0] == freq_matrix[i][1]:
                vectors_matrix[0][i] = np.array([freq_matrix[i][0]] * int(freq_matrix[i][2]))*1e6
        vectors_matrix = vectors_matrix.ravel()
        joined_string = ''.join(map(str, vectors_matrix))

        joined_string = joined_string.replace('[', '').replace(' ', ',').replace(']', ',' ).replace('\n', '')
        self.inst.write(':list:FREQ ' + joined_string)
        self.inst.write(':list:POW ' + '10')
        return 
    
    def make_list(self, n_vector, freq_values, amp_values, dwell_values):
        freq_matrix = np.zeros((n_vector, 3))
        amp_matrix = np.zeros((n_vector, 3))

        if len(dwell_values) != n_vector:
            raise Exception(f' Length of dwell values array {len(dwell_values)} is different from number of ramps {n_vector}')
       

        for i in range(n_vector):
            for j in range(3):
                freq_matrix[i][j] = np.asarray(freq_values)[i][j]
                amp_matrix[i][j] = np.asarray(amp_values)[i][j]
        freq_vectors_matrix = np.zeros((1, n_vector), dtype=object)
        amp_vectors_matrix = np.zeros((1, n_vector), dtype=object)
        dwell_vector = np.zeros(n_vector, dtype=object)

        # Frequency list
        for i in range(n_vector):
            if freq_matrix[i][0] != freq_matrix[i][1]:
                if freq_matrix[i][0] < freq_matrix[i][1]:
                    freq_vectors_matrix[0][i] = np.arange(freq_matrix[i][0], freq_matrix[i][1]+freq_matrix[i][2], freq_matrix[i][2])*1e6
                elif freq_matrix[i][0] > freq_matrix[i][1]:
                    freq_vectors_matrix[0][i] = np.arange(freq_matrix[i][0], freq_matrix[i][1]-freq_matrix[i][2], -freq_matrix[i][2])*1e6
            elif freq_matrix[i][0] == freq_matrix[i][1]:
                freq_vectors_matrix[0][i] = np.array(np.repeat(freq_matrix[i][0], int(freq_matrix[i][2])))*1e6

        freq_vectors_matrix = freq_vectors_matrix.ravel()
        # Amplitude list 
        for i in range(n_vector):
            if amp_matrix[i][0] != amp_matrix[i][1]:
                if amp_matrix[i][0] < amp_matrix[i][1]:
                    amp_vectors_matrix[0][i] = np.arange(amp_matrix[i][0], amp_matrix[i][1]+amp_matrix[i][2], amp_matrix[i][2])
                elif amp_matrix[i][0] > amp_matrix[i][1]:
                    amp_vectors_matrix[0][i] = np.arange(amp_matrix[i][0], amp_matrix[i][1]-amp_matrix[i][2], -amp_matrix[i][2])
            elif amp_matrix[i][0] == amp_matrix[i][1]:
                amp_vectors_matrix[0][i] = np.array(np.repeat(amp_matrix[i][0], freq_vectors_matrix[i].size))
        amp_vectors_matrix = amp_vectors_matrix.ravel()
       
        # Dwell list
        for i in range(n_vector):
            dwell_vector[i] = np.array(np.repeat(dwell_values[i], freq_vectors_matrix[i].size))
        dwell_vector = dwell_vector.ravel()

        self.write_list_old(freq_vectors_matrix,amp_vectors_matrix,dwell_vector)
        return 
    
    def write_list_old (self, freq_values, amp_values, dwell_values):
        # Frequency
        N_steps = 0
        for i in range(freq_values.size):
            N_steps += freq_values[i].size
        print(f'{N_steps} frequency steps written')
        joined_string = ''.join(map(str, freq_values))
        joined_string = joined_string.replace('[', '').replace(' ', ',').replace(']', ',' ).replace('\n', '')
        self.inst.write(':list:FREQ ' + joined_string)

        # Amplitude
        N_steps = 0
        for i in range(amp_values.size):
            N_steps += amp_values[i].size
        print(f'{N_steps} amplitude steps written')
        joined_string = ''.join(map(str, amp_values))
        joined_string = joined_string.replace('[', '').replace('  ',',').replace(' ', ',').replace(']', ',' ).replace('\n', '').replace(',,',',')
        self.inst.write(':list:POW ' + joined_string)

        # Dwell times
        N_steps = 0
        for i in range(dwell_values.size):
           N_steps += dwell_values[i].size
        print(f'{N_steps} dwell steps written')
        joined_string = ''.join(map(str, dwell_values))
        joined_string = joined_string.replace('[', '').replace(' ', ',').replace(']', ',' ).replace('\n', '')
        self.inst.write(':list:DWELL ' + joined_string)
        self.inst.write(':list:TRIG:SOUR IMM')
        self.inst.write(':TRIG:SOUR IMM')
        return
    

    def write_list (self, freq_values, amp_values, dwell_values,trigger_steps):
        # Frequency
        print(f'{freq_values.size} frequency steps written')
        joined_string = ','.join(map(str, freq_values))
        # print(f'Frequencies: {joined_string}')
        # joined_string = joined_string.replace('[', '').replace(' ', ',').replace(']', ',' ).replace('\n', '')
        # print(f'Frequencies: {joined_string}')
        self.inst.write(':list:FREQ ' + joined_string)

        # Amplitude
        print(f'{amp_values.size} amplitude steps written')
        joined_string = ','.join(map(str, amp_values))
        # joined_string = joined_string.replace('[', '').replace('  ',',').replace(' ', ',').replace(']', ',' ).replace('\n', '').replace(',,',',')
        self.inst.write(':list:POW ' + joined_string)

        # Dwell times
        print(f'{dwell_values.size} dwell steps written')
        joined_string = ','.join(map(str, dwell_values))
        # joined_string = joined_string.replace('[', '').replace(' ', ',').replace(']', ',' ).replace('\n', '').replace(',,',',')
        # print(joined_string.replace(',,',','))
        self.inst.write(':list:DWELL ' + joined_string)

        # Triggers
        if trigger_steps:
            self.inst.write(':list:TRIG:SOUR EXT')
        else:
            self.inst.write(':list:TRIG:SOUR IMM')
        self.inst.write(':TRIG:SOUR EXT')
        self.inst.write(':DISP:REM 1')
        return
    
if __name__ == '__main__':
    freq_list = []
    freq_list.append(np.arange(562.5,563.5,0.1)*1e6)
    freq_list.append(np.arange(563.5,562.5,-0.1)*1e6)
    freq_list = np.asarray(freq_list)
    print(freq_list)
    amp_list = []
    amp_list.append(np.ones(freq_list.size)*17)
    print(amp_list)
    dwell_list = []
    dwell_list.append(np.ones(freq_list.size)*100e-3)
    print(dwell_list)

    CF = cassone_funcs(device='GPIB1::8::INSTR')
    CF.write_list(freq_list, np.asarray(amp_list), np.asarray(dwell_list))
    # CF.set_amp(16)