"""
This module contains helper functions for rearrangment of tones.
--
Omar Abdel Karim <omarkabd@gmail.com>, June2023
"""

import numpy as np
import numba
import random


def order_1D_array(amplitude_array, tones_array):
    """
    Reorder 1D array by shiting the tones on the right in presence of defects.

    Arguments:
        amplitude_array (numpy.ndarray):
        The amplitudes array.

        tones_array (numpy.ndarray):
            The tones array.

    Returns:
        numpy.ndarray:
            reordered 1D array.
    """


    modified_tones_array = list(tones_array)  # Create a copy of the sequence

    for i in range(len(amplitude_array)):
        if amplitude_array[i] == 0:
            for j in range(i):
                if modified_tones_array[j] != 0:
                    modified_tones_array[j] += 4e6
        if amplitude_array[i] == 0:
            modified_tones_array[i] = 0

    return modified_tones_array

def simulate_defects(amplitude_array):
    """
    Simulates holes (0 ampitude) in amplitudes array.

    Arguments:

        amplitude_array (numpy.ndarray):
            The amplitudes array.

    Returns:
        numpy.ndarray:
            array with holes.
    """
    length = len(amplitude_array)
    num_zeros = length//2
    zero_indices = random.sample(range(length), num_zeros)
    
    for i in zero_indices:
        amplitude_array[i] = 0
    
    return amplitude_array