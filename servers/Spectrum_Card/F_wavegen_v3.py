"""
This module contains helper functions for generating arbitrary waveforms from
single or multiple sinusoidal tones.
--
Nelson Darkwah Oppong <n@darkwahoppong.com>, March 2022
Edited by Omar Abdel Karim, May 2023
Edited by Fabrizio Barbuio, September 2025
"""

from functools import lru_cache
import numpy as np
import numba
from scipy.signal import chirp
import random


def frequency_resolution(sample_count, sample_rate):
    """
    Calculate the frequency resolution of the arbitrary waveform generator.

    Arguments:
        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

    Returns:
        float:
            The frequency resolution of the arbitrary waveform generator.
    """
    return sample_rate / sample_count


def frequency_round(frequency, sample_count, sample_rate):
    """
    Round the frequency to the nearest multiple of the frequency resolution.

    Arguments:
        frequency (float):
            The frequency in Hz.

        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

    Returns:
        float:
            The rounded frequency.
    """
    resolution = frequency_resolution(sample_count, sample_rate)
    return round(frequency / resolution) * resolution


@lru_cache(maxsize=2**4)
def time_steps(sample_count, sample_rate):
    """
    Calculate the time steps of the waveform.

    Arguments:
        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

    Returns:
        numpy.ndarray:
            The time steps of the waveform in seconds.
    """
    return np.arange(sample_count) / sample_rate


@numba.njit(parallel=True)
def _single_tone(times, frequency, amplitude, phase):
    """Optimized function to generate a single tone waveform."""
    frequency *= 2 * np.pi
    return amplitude * np.sin(frequency * times + phase)


def single_tone(sample_count, sample_rate, frequency, amplitude, phase,
                round_frequency=True):
    """
    Generate a single tone sinusoidal waveform.

    Arguments:
        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

        frequency (float):
            The frequency in Hz.

        amplitude (float, optional):
            The amplitude, 1 if None is passed

        phase (float, optional):
            The phase, 0 if None is passed

        round_frequency (bool, optional):
            Whether to round the frequency to the nearest multiple of the
            frequency resolution, True by default.

    Raises:
        ValueError:
            - If the frequency is incompatible with the sample rate and sample
              count (and round_frequency is False).
            - If the amplitude is negative.
            - If the phase is not in [0, 2π).

    Returns:
        numpy.ndarray:
            The waveform.
    """

    if round_frequency is True:
        frequency = frequency_round(frequency, sample_count, sample_rate)
    else:
        _validate_frequency(frequency, sample_count, sample_rate)
    if amplitude is None:
        amplitude = 1.0

    if phase is None:
        phase = 0.0

    amplitude = np.asarray_chkfinite(amplitude)
    phase = np.asarray_chkfinite(phase)

    _validate_amplitude(amplitude)
    # _validate_phase(phase)

    times = time_steps(sample_count, sample_rate)
    return _single_tone(times, frequency, amplitude, phase)

@numba.njit(parallel=True)
def _painting_tone(times, carrier_frequency, modulation_frequency, frequency_amplitude, amplitude, phase):
    """Optimized function to generate a single tone waveform."""
    carrier_frequency *= 2 * np.pi
    frequency_amplitude *= 2 * np.pi
    return amplitude * np.sin( (carrier_frequency + frequency_amplitude * np.cos( modulation_frequency * times ) ) * times + phase)


def painting_tone(sample_count, sample_rate, carrier_frequency, modulation_frequency, frequency_amplitude, amplitude=1.0, phase=0.0,
                round_frequency=True):
    """
    Generate a sinusoidal waveform with frequency modulated with a sinusoidal sweep.

    Arguments:
        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

        carrier_frequency (float):
            The central frequency in Hz.

        modulation_frequency (float):
            The frequency of the modulation in Hz.

        frequency_amplitude (float):
            The amplitude of frequency modulation in Hz.

        amplitude (float, optional):
            The amplitude, 1 by default.

        phase (float, optional):
            The phase, 0 by default.

        round_frequency (bool, optional):
            Whether to round the frequency to the nearest multiple of the
            frequency resolution, True by default.

    Raises:
        ValueError:
            - If the frequency is incompatible with the sample rate and sample
              count (and round_frequency is False).
            - If the amplitude is negative.
            - If the phase is not in [0, 2π).

    Returns:
        numpy.ndarray:
            The waveform.
    """
    
    if round_frequency is True:
        carrier_frequency = frequency_round(carrier_frequency, sample_count, sample_rate)
        modulation_frequency = frequency_round(modulation_frequency, sample_count, sample_rate)
    else:
        _validate_frequency(modulation_frequency, sample_count, sample_rate)
        _validate_frequency(carrier_frequency, sample_count, sample_rate)

    _validate_amplitude(amplitude)
    # _validate_phase(phase)

    times = time_steps(sample_count, sample_rate)
    return _painting_tone(times, carrier_frequency, modulation_frequency, frequency_amplitude, amplitude, phase)


@numba.njit(parallel=False)
def _multi_tone(times, frequencies_count, frequencies, amplitudes, phases):
    """Optimized function to generate a multi tone waveform."""
    summed = np.zeros_like(times, dtype=np.dtype('float'))
    for i in range(frequencies_count):
        summed += _single_tone(
            times, frequencies[i], amplitudes[i], phases[i])

    return summed


def multi_tone(sample_count, sample_rate, frequencies, amplitudes,
               phases, normalize_amplitudes=False, round_frequencies=True):
    """
    Generate a multi tone waveform consisting of multiple single tone
    sinusoidal waveforms.

    Arguments:
        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

        frequencies (numpy.ndarray):
            The frequencies in Hz.

        amplitudes (numpy.ndarray, optional):
            The amplitudes, 1 by default (if None is passed).

        phases (numpy.ndarray, optional):
            The phases, 0 by default (if None is passed).

        normalize_amplitudes (bool, optional):
            Whether to normalize the summmed amplitudes to 1 (True by default).

        round_frequencies (bool, optional):
            Whether to round the frequencies to the nearest multiple of the
            frequency resolution, True by default.

    Raises:
        ValueError:
            - If any of the frequencies is incompatible with the sample rate
              and round_frequencies is False.
            - If any of the amplitudes is negative.
            - If any of the phases is not in [0, 2π).

    Returns:
        numpy.ndarray:
            The waveform.
    """
    frequencies = np.asarray_chkfinite(frequencies)

    if amplitudes is None:
        amplitudes = np.ones_like(frequencies)

    if phases is None:
        phases = np.zeros_like(frequencies)

    amplitudes = np.asarray_chkfinite(amplitudes)
    phases = np.asarray_chkfinite(phases)

    frequencies_count = len(frequencies)
    amplitudes_count = len(amplitudes)
    phases_count = len(phases)

    if amplitudes_count != frequencies_count:
        raise ValueError(
            f'Number of amplitudes ({amplitudes_count}) does not match '
            f'number of frequencies ({frequencies_count}).')

    if phases_count != frequencies_count:
        raise ValueError(
            f'Number of phases ({phases_count}) does not match number '
            'of frequencies ({frequencies_count}).')

    for frequency, amplitude, phase in zip(frequencies, amplitudes, phases):
        if round_frequencies is True:
            frequency = frequency_round(frequency, sample_count, sample_rate)
        else:
            _validate_frequency(frequency, sample_count, sample_rate)
        _validate_amplitude(amplitude)
        # _validate_phase(phase)

    if normalize_amplitudes is True:
        amplitudes /= np.sum(amplitudes)

    times = time_steps(sample_count, sample_rate)
    return _multi_tone(
        times, frequencies_count, frequencies, amplitudes, phases)
    
@numba.njit(parallel=True) #Fabrizio
def _pq_phase(times, starting_frequency, duration, ending_frequency, phi):
    """
    Computes the phase of a piecewise quadratic function by dividing the time interval in two, where
    the first one experiences a constant acceleration +a and the second one -a
    """
    T = duration
    f_delta = ending_frequency - starting_frequency
    phase = np.zeros_like(times, dtype=np.float64)
    t_half = T/2.0
    # Define first half of sweep
    mask1 = times <= t_half
    t1 = times[mask1]
    phase[mask1] = 2*np.pi*(starting_frequency * t1 + f_delta * (2 * t1**3 / (3*T**2))) + phi
    
    # Define second half of sweep
    mask2 = ~mask1
    t2 = times[mask2]
    t_prime = t2 - t_half
    phase[mask2] = 2*np.pi*(starting_frequency * t2 + f_delta * (T/12 + 0.5*t_prime + t_prime**2 / T - 2*t_prime**3 / (3*T**2))) + phi

    return phase


@numba.njit(parallel=True) # Fabrizio
def _pq_pulse(times, starting_frequency, duration, ending_frequency, amplitude, phase):
    """
    Function to generate a piecewise quadratic waveform.
    """
    return amplitude * np.sin(_pq_phase(times, starting_frequency, duration, ending_frequency, phase))

def pq_single_tone(sample_count, sample_rate, starting_frequency, duration, ending_frequency, amplitude=None, phase=None, round_frequency=True):  # Fabrizio
    """
    Generate a piecewise-quadratic sweep from frequency 1 to frequency 2 in a time T

    Arguments:
        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

        starting_frequency (numpy.ndarray):
            The starting frequency in Hz.

        duration (numpy.ndarray):
            Duration of the chirp in seconds.

        ending_frequency (numpy.ndarray):
            The ending frequency in Hz.

        amplitude (numpy.ndarray, optional):
            The amplitudes, 1 by default (if None is passed).
            If an array is given, modulates the signal with the given amplitudes per sample. 
        phases (numpy.ndarray, optional):
            The phase, 0 by default (if None is passed).

        round_frequency (bool, optional):
            Whether to round the frequency to the nearest multiple of the
            frequency resolution, True by default.

    Raises:
        ValueError:
            - If the frequency is incompatible with the sample rate
              and round_frequency is False.
            - If the amplitude is negative.
            - If the phase is not in [0, 2π).

    Returns:
        numpy.ndarray:
            The waveform.
    
    """
    starting_frequency = np.asarray_chkfinite(starting_frequency)
    ending_frequency = np.asarray_chkfinite(ending_frequency)
    
    if amplitude is None:
        amplitude = 1.0
        
    amplitude = np.asarray_chkfinite(amplitude)
    
    if amplitude.ndim == 0:  # Added amplitude modulation 20/11/25 (Fabrizio)
        amplitude = np.full(sample_count, amplitude.item(), dtype=float)
    elif amplitude.size != sample_count:
        raise ValueError("Length of amplitude array differs from sample_count!")

    if phase is None:
        phase = 0.0

    phase = np.asarray_chkfinite(phase)
    
    if round_frequency is True:
        starting_frequency = frequency_round(starting_frequency, sample_count, sample_rate)
        ending_frequency = frequency_round(ending_frequency, sample_count, sample_rate)
    else:
        _validate_frequency(starting_frequency, sample_count, sample_rate)
        _validate_frequency(ending_frequency, sample_count, sample_rate)
    _validate_amplitude(amplitude)
    
    times = np.arange(sample_count)/sample_rate
    return _pq_pulse(times, starting_frequency, duration, ending_frequency, amplitude, phase)

@numba.njit(parallel=True) # Riccardo, 16/02/2026
def _half_pq_phase(times, starting_frequency, duration, ending_frequency, phi):
    """
    Computes the phase of a piecewise quadratic function to move with
    constant acceleration +a.
    """
    T = duration
    f_delta = ending_frequency - starting_frequency
    phase = np.zeros_like(times, dtype=np.float64)
    phase = 2*np.pi*(starting_frequency * times + f_delta /T**2 * times**3/3 ) + phi

    return phase

@numba.njit(parallel=True) # Riccardo, 16/02/2026
def _half_pq_pulse(times, starting_frequency, duration, ending_frequency, amplitude, phase):
    """
    Function to generate a piecewise quadratic waveform.
    """
    return amplitude * np.sin(_half_pq_phase(times, starting_frequency, duration, ending_frequency, phase))

def half_pq_single_tone(sample_count, sample_rate, starting_frequency, duration, ending_frequency, amplitude=None, phase=None, round_frequency=True):  # Riccardo, 16/02/2026
    """
    Generate a piecewise-quadratic sweep from frequency 1 to frequency 2 in a time T

    Arguments:
        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

        starting_frequency (numpy.ndarray):
            The starting frequency in Hz.

        duration (numpy.ndarray):
            Duration of the chirp in seconds.

        ending_frequency (numpy.ndarray):
            The ending frequency in Hz.

        amplitude (numpy.ndarray, optional):
            The amplitudes, 1 by default (if None is passed).
            If an array is given, modulates the signal with the given amplitudes per sample. 
        phases (numpy.ndarray, optional):
            The phase, 0 by default (if None is passed).

        round_frequency (bool, optional):
            Whether to round the frequency to the nearest multiple of the
            frequency resolution, True by default.

    Raises:
        ValueError:
            - If the frequency is incompatible with the sample rate
              and round_frequency is False.
            - If the amplitude is negative.
            - If the phase is not in [0, 2π).

    Returns:
        numpy.ndarray:
            The waveform.
    
    """
    starting_frequency = np.asarray_chkfinite(starting_frequency)
    ending_frequency = np.asarray_chkfinite(ending_frequency)
    
    if amplitude is None:
        amplitude = 1.0
        
    amplitude = np.asarray_chkfinite(amplitude)
    
    if amplitude.ndim == 0:  # Added amplitude modulation 20/11/25 (Fabrizio)
        amplitude = np.full(sample_count, amplitude.item(), dtype=float)
    elif amplitude.size != sample_count:
        raise ValueError("Length of amplitude array differs from sample_count!")

    if phase is None:
        phase = 0.0

    phase = np.asarray_chkfinite(phase)
    
    if round_frequency is True:
        starting_frequency = frequency_round(starting_frequency, sample_count, sample_rate)
        ending_frequency = frequency_round(ending_frequency, sample_count, sample_rate)
    else:
        _validate_frequency(starting_frequency, sample_count, sample_rate)
        _validate_frequency(ending_frequency, sample_count, sample_rate)
    _validate_amplitude(amplitude)
    
    times = np.arange(sample_count)/sample_rate
    return _half_pq_pulse(times, starting_frequency, duration, ending_frequency, amplitude, phase)

@numba.njit(parallel=True) # Fabrizio&Ale, 04/02/26
def _pc_phase(times, starting_frequency, duration, ending_frequency, phi):
    """
    Computes the phase of a piecewise cubic function in position (piecewise quadratic in velocity) to 
    bring the atoms from initial velocity 0 to final velocity v_g uniquely determined by the two frequencies and the sweep duration
    """
    T = duration
    phase = np.zeros_like(times, dtype=np.float64)
    phi_dot = np.zeros_like(times, dtype=np.float64)
    phi_ddot = np.zeros_like(times, dtype=np.float64)

    t_half = T/2.0
    f_delta = ending_frequency - starting_frequency
    p2 = 8.0 * np.pi * f_delta / (T**3)
    
    # phi_mid and phi_dot_mid as derived:
    phi_mid = phi + 2.0*np.pi*starting_frequency * t_half + p2 * (t_half**4) / 12.0
    phi_dot_mid = 2.0*np.pi*starting_frequency + p2 * (t_half**3) / 3.0
    
    # Define first half of sweep
    mask1 = times <= t_half
    t1 = times[mask1]
    phi_ddot[mask1] = p2 * t1**2
    phi_dot[mask1] = 2.0*np.pi*starting_frequency + p2 * (t1**3) / 3.0
    phase[mask1] = phi + 2.0*np.pi*starting_frequency * t1 + p2 * (t1**4) / 12.0
    
    # Define second half of sweep
    mask2 = ~mask1
    t2 = times[mask2]
    t_prime = t2 - t_half
    phi_ddot[mask2] = p2*(T*T/4.0) + p2*T*t_prime - p2*(t_prime**2)
    phi_dot[mask2] = (2.0*np.pi*starting_frequency + p2 * (T**3) / 24.0 + p2*( (T*T/4.0)*t_prime + (T/2.0)*(t_prime**2) - (t_prime**3)/3.0 ))
    phase[mask2] = (phi_mid + phi_dot_mid * t_prime + p2*( (T*T/8.0)*(t_prime**2) + (T/6.0)*(t_prime**3) - (t_prime**4)/12.0 ))

    return phase

@numba.njit(parallel=True) # Fabrizio&Ale, 04/02/26
def _pc_pulse(times, starting_frequency, duration, ending_frequency, amplitude, phase):
    """
    Function to generate a piecewise cubic waveform in position.
    """
    return amplitude * np.sin(_pc_phase(times, starting_frequency, duration, ending_frequency, phase))

def pc_single_tone(sample_count, sample_rate, starting_frequency, duration, ending_frequency, amplitude=None, phase=None, round_frequency=True):  # Fabrizio&Ale, 04/02/26
    """
    Generate a piecewise-cubic sweep in position from frequency 1 to frequency 2 in a time T.
    Final velocity is non-zero and uniquely determined by the duration and the frequencies.

    Arguments:
        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

        starting_frequency (numpy.ndarray):
            The starting frequency in Hz.

        duration (numpy.ndarray):
            Duration of the total sweep in seconds.

        ending_frequency (numpy.ndarray):
            The ending frequency in Hz.

        amplitude (numpy.ndarray, optional):
            The amplitudes, 1 by default (if None is passed).
            If an array is given, modulates the signal with the given amplitudes per sample. 
        phases (numpy.ndarray, optional):
            The phase, 0 by default (if None is passed).

        round_frequency (bool, optional):
            Whether to round the frequency to the nearest multiple of the
            frequency resolution, True by default.

    Raises:
        ValueError:
            - If the frequency is incompatible with the sample rate
              and round_frequency is False.
            - If the amplitude is negative.
            - If the phase is not in [0, 2π).

    Returns:
        numpy.ndarray:
            The waveform.
    
    """
    starting_frequency = np.asarray_chkfinite(starting_frequency)
    ending_frequency = np.asarray_chkfinite(ending_frequency)
    
    if amplitude is None:
        amplitude = 1.0
        
    amplitude = np.asarray_chkfinite(amplitude)
    
    if amplitude.ndim == 0:  # Added amplitude modulation 20/11/25 (Fabrizio)
        amplitude = np.full(sample_count, amplitude.item(), dtype=float)
    elif amplitude.size != sample_count:
        raise ValueError("Length of amplitude array differs from sample_count!")

    if phase is None:
        phase = 0.0

    phase = np.asarray_chkfinite(phase)
    
    if round_frequency is True:
        starting_frequency = frequency_round(starting_frequency, sample_count, sample_rate)
        ending_frequency = frequency_round(ending_frequency, sample_count, sample_rate)
    else:
        _validate_frequency(starting_frequency, sample_count, sample_rate)
        _validate_frequency(ending_frequency, sample_count, sample_rate)
    _validate_amplitude(amplitude)
    
    times = np.arange(sample_count)/sample_rate
    return _pc_pulse(times, starting_frequency, duration, ending_frequency, amplitude, phase)


@numba.njit(parallel=True)  #Omar # modified by Fabrizio on 10/2025
def _chirp_phase(times, starting_frequency, duration, ending_frequency, phi): #since the chirp function by scipy does not support numba, I write a chirp function
    phase = 2 * np.pi * ((starting_frequency + 0.5 * ((ending_frequency - starting_frequency)/duration) * times) * times) + phi
    return phase

@numba.njit(parallel=True) #Omar # modified by Fabrizio on 10/2025
def _chirp_pulse(times, starting_frequency, duration, ending_frequency, amplitude, phase):
    """Optimized function to generate a chirped tone waveform."""
    # return amplitude * _chirp(times, starting_frequency, duration, ending_frequency, method = 'linear', phi = phase) #use this if you want to use scipy chirp function
    return amplitude * np.sin(_chirp_phase(times, starting_frequency, duration, ending_frequency, phase))

def chirp_single_pulse(sample_count, sample_rate, starting_frequency, duration, ending_frequency, amplitude,
                       phase=None, round_frequency=True): # Fabrizio # Added amplitude modulation 20/11/25 (Fabrizio)
    """
    Generate a single tone chirped waveform.

    Arguments:
        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

        starting_frequency (numpy.ndarray):
            The starting frequency in Hz.

        duration (numpy.ndarray):
            Duration of the chirp in seconds.

        ending_frequency (numpy.ndarray):
            The ending frequency in Hz.

        amplitude (numpy.ndarray, optional):
            The amplitudes, 1 by default (if None is passed).
            If an array is given, modulates the signal with the given amplitudes per sample. 
        phases (numpy.ndarray, optional):
            The phase, 0 by default (if None is passed).

        round_frequency (bool, optional):
            Whether to round the frequency to the nearest multiple of the
            frequency resolution, True by default.

    Raises:
        ValueError:
            - If the frequency is incompatible with the sample rate
              and round_frequency is False.
            - If the amplitude is negative.
            - If the phase is not in [0, 2π).

    Returns:
        numpy.ndarray:
            The waveform.
    """
    starting_frequency = np.asarray_chkfinite(starting_frequency)
    ending_frequency = np.asarray_chkfinite(ending_frequency)

    if amplitude is None:
        amplitude = 1.0

    amplitude = np.asarray_chkfinite(amplitude)

    if amplitude.ndim == 0:  # Added amplitude modulation 20/11/25 (Fabrizio)
        amplitude = np.full(sample_count, amplitude.item(), dtype=float)
    elif amplitude.size != sample_count:
        raise ValueError("Length of amplitude array differs from sample_count!")
    
    if phase is None:
        phase = 0.0

    phase = np.asarray_chkfinite(phase)

    
    if round_frequency is True:
        starting_frequency = frequency_round(starting_frequency, sample_count, sample_rate)
        ending_frequency = frequency_round(ending_frequency, sample_count, sample_rate)
    else:
        _validate_frequency(starting_frequency, sample_count, sample_rate)
        _validate_frequency(ending_frequency, sample_count, sample_rate)
    _validate_amplitude(amplitude)
    # _validate_phase(phase)

    times = time_steps(sample_count, sample_rate)
    return _chirp_pulse(
        times, starting_frequency, duration, ending_frequency, amplitude, phase)

@numba.njit(parallel=True) #Omar
def _chirp_multi_pulse(times, frequencies_count, starting_frequencies, durations, ending_frequencies, amplitudes, phases):
    """Optimized function to generate a chirped multi tone waveform."""
    summed = np.zeros_like(times, dtype=np.dtype('float'))
    for i in range(frequencies_count):
        summed += _chirp_pulse(
            times, starting_frequencies[i], durations[i], ending_frequencies[i], amplitudes[i], phases[i])

    return summed

def chirp_multi_pulse(sample_count, sample_rate, starting_frequencies, durations, ending_frequencies, amplitudes,
               phases=None, normalize_amplitudes=True, round_frequency=True): #Omar
    """
    Generate a multi tone chirped waveform consisting of multiple chirped single tone
    sinusoidal waveforms.

    Arguments:
        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

        starting_frequencies (numpy.ndarray):
            The starting frequencies in Hz.

        durations (numpy.ndarray):
            Duration of the chirp in seconds.

        ending_frequencies (numpy.ndarray):
            The ending frequencies in Hz.

        amplitudes (numpy.ndarray, optional):
            The amplitudes, 1 by default (if None is passed).

        phases (numpy.ndarray, optional):
            The phases, 0 by default (if None is passed).

        normalize_amplitudes (bool, optional):
            Whether to normalize the summmed amplitudes to 1 (True by default).

        round_frequencies (bool, optional):
            Whether to round the frequencies to the nearest multiple of the
            frequency resolution, True by default.

    Raises:
        ValueError:
            - If any of the frequencies is incompatible with the sample rate
              and round_frequencies is False.
            - If any of the amplitudes is negative.
            - If any of the phases is not in [0, 2π).

    Returns:
        numpy.ndarray:
            The waveform.
    """
    starting_frequencies = np.asarray_chkfinite(starting_frequencies)
    ending_frequencies = np.asarray_chkfinite(ending_frequencies)

    if amplitudes is None:
        amplitudes = np.ones_like(starting_frequencies)

    if phases is None:
        phases = np.zeros_like(starting_frequencies)

    amplitudes = np.asarray_chkfinite(amplitudes)
    phases = np.asarray_chkfinite(phases)

    frequencies_count = len(starting_frequencies)
    ending_frequencies_count = len(ending_frequencies)
    amplitudes_count = len(amplitudes)
    phases_count = len(phases)

    # if frequencies_count != ending_frequencies_count:
    #     raise ValueError(
    #         f'Len of starting frequencies: ({frequencies_count}) does not match '
    #         f'len of ending frequencies ({ending_frequencies_count}).')

    if amplitudes_count != frequencies_count:
        raise ValueError(
            f'Number of amplitudes ({amplitudes_count}) does not match '
            f'number of frequencies ({frequencies_count}).')

    if amplitudes_count != frequencies_count:
        raise ValueError(
            f'Number of amplitudes ({amplitudes_count}) does not match '
            f'number of frequencies ({frequencies_count}).')

    if phases_count != frequencies_count:
        raise ValueError(
            f'Number of phases ({phases_count}) does not match number '
            'of frequencies ({frequencies_count}).')

    for starting_frequency, ending_frequency, amplitude, phase in zip(starting_frequencies, ending_frequencies, amplitudes, phases):
        if round_frequency is True:
            starting_frequency = frequency_round(starting_frequency, sample_count, sample_rate)
            ending_frequency = frequency_round(ending_frequency, sample_count, sample_rate)
        else:
            _validate_frequency(starting_frequency, sample_count, sample_rate)
            _validate_frequency(ending_frequency, sample_count, sample_rate)
        _validate_amplitude(amplitude)
        # _validate_phase(phase)

    if normalize_amplitudes is True:
        amplitudes /= np.sum(amplitudes)

    times = time_steps(sample_count, sample_rate)
    return _chirp_multi_pulse(
        times, frequencies_count, starting_frequencies, durations, ending_frequencies, amplitudes, phases)


def dynamic_multi_tone(sample_count, sample_rate, frequencies, number_of_jumps, amplitudes=None,
               phases=None, normalize_amplitudes=False, round_frequencies=True): #Omar
    """
    Generate a multi tone waveform consisting of multiple single tone
    sinusoidal waveforms.

    Arguments:
        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

        frequencies (numpy.ndarray):
            The frequencies in Hz.

        amplitudes (numpy.ndarray, optional):
            The amplitudes, 1 by default (if None is passed).

        phases (numpy.ndarray, optional):
            The phases, 0 by default (if None is passed).

        normalize_amplitudes (bool, optional):
            Whether to normalize the summmed amplitudes to 1 (True by default).

        round_frequencies (bool, optional):
            Whether to round the frequencies to the nearest multiple of the
            frequency resolution, True by default.

    Raises:
        ValueError:
            - If any of the frequencies is incompatible with the sample rate
              and round_frequencies is False.
            - If any of the amplitudes is negative.
            - If any of the phases is not in [0, 2π).

    Returns:
        numpy.ndarray:
            The waveform.
    """
    frequencies = np.asarray_chkfinite(frequencies)
    sample_count /= number_of_jumps

    if amplitudes is None:
        amplitudes = np.ones_like(frequencies)

    if phases is None:
        phases = np.zeros_like(frequencies)

    amplitudes = np.asarray_chkfinite(amplitudes)
    phases = np.asarray_chkfinite(phases)

    frequencies_count = len(frequencies)
    amplitudes_count = len(amplitudes)
    phases_count = len(phases)

    if amplitudes_count != frequencies_count:
        raise ValueError(
            f'Number of amplitudes ({amplitudes_count}) does not match '
            f'number of frequencies ({frequencies_count}).')

    if phases_count != frequencies_count:
        raise ValueError(
            f'Number of phases ({phases_count}) does not match number '
            'of frequencies ({frequencies_count}).')

    for frequency, amplitude, phase in zip(frequencies, amplitudes, phases):
        if round_frequencies is True:
            frequency = frequency_round(frequency, sample_count, sample_rate)
        else:
            _validate_frequency(frequency, sample_count, sample_rate)
        _validate_amplitude(amplitude)
        # _validate_phase(phase)

    if normalize_amplitudes is True:
        amplitudes /= np.sum(amplitudes)

    times = time_steps(sample_count, sample_rate)
    return _multi_tone(
        times, frequencies_count, frequencies, amplitudes, phases)


@numba.njit(parallel=True) #Omar
def _damped_single_tone(times, frequency, amplitude, phase, tau):
    """Optimized function to generate a single tone waveform."""
    frequency *= 2 * np.pi
    return amplitude * np.sin(frequency * times + phase) * np.exp(-(times * tau))

@numba.njit(parallel=False) #Omar
def _damped_multi_tone(times, frequencies_count, frequencies, amplitudes, phases, tau):
    """Optimized function to generate a multi tone waveform."""
    summed = np.zeros_like(times, dtype=np.dtype('float'))
    for i in range(frequencies_count):
        summed += _damped_single_tone(
            times, frequencies[i], amplitudes[i], phases[i], tau[i])

    return summed

def damped_multi_tone(sample_count, sample_rate, frequencies, amplitudes, tau,
               phases=None, normalize_amplitudes=True, round_frequencies=True): #Omar
    """
    Generate a multi tone waveform consisting of multiple single tone
    sinusoidal waveforms.

    Arguments:
        sample_count (int):
            The number of samples in the waveform.

        sample_rate (float):
            The sample rate of the waveform in Hz.

        frequencies (numpy.ndarray):
            The frequencies in Hz.

        amplitudes (numpy.ndarray, optional):
            The amplitudes, 1 by default (if None is passed).

        phases (numpy.ndarray, optional):
            The phases, 0 by default (if None is passed).

        tau (float): decay time constant in Hz.

        normalize_amplitudes (bool, optional):
            Whether to normalize the summmed amplitudes to 1 (True by default).

        round_frequencies (bool, optional):
            Whether to round the frequencies to the nearest multiple of the
            frequency resolution, True by default.

    Raises:
        ValueError:
            - If any of the frequencies is incompatible with the sample rate
              and round_frequencies is False.
            - If any of the amplitudes is negative.
            - If any of the phases is not in [0, 2π).

    Returns:
        numpy.ndarray:
            The waveform.
    """
    frequencies = np.asarray_chkfinite(frequencies)

    if amplitudes is None:
        amplitudes = np.ones_like(frequencies)

    if phases is None:
        phases = np.zeros_like(frequencies)

    amplitudes = np.asarray_chkfinite(amplitudes)
    phases = np.asarray_chkfinite(phases)

    frequencies_count = len(frequencies)
    amplitudes_count = len(amplitudes)
    phases_count = len(phases)

    if amplitudes_count != frequencies_count:
        raise ValueError(
            f'Number of amplitudes ({amplitudes_count}) does not match '
            f'number of frequencies ({frequencies_count}).')

    if phases_count != frequencies_count:
        raise ValueError(
            f'Number of phases ({phases_count}) does not match number '
            'of frequencies ({frequencies_count}).')

    for frequency, amplitude, phase in zip(frequencies, amplitudes, phases):
        if round_frequencies is True:
            frequency = frequency_round(frequency, sample_count, sample_rate)
        else:
            _validate_frequency(frequency, sample_count, sample_rate)
        _validate_amplitude(amplitude)
        # _validate_phase(phase)

    if normalize_amplitudes is True:
        amplitudes /= np.sum(amplitudes)

    times = time_steps(sample_count, sample_rate)
    return _damped_multi_tone(
        times, frequencies_count, frequencies, amplitudes, phases, tau)


def _validate_frequency(frequency, sample_count, sample_rate, prec=16):
    """Helper function to validate a frequency."""
    resolution = frequency_resolution(sample_count, sample_rate)
    if np.round(frequency % resolution, prec) != 0:
        raise ValueError(
            f'Frequency {frequency:e} is incompatible with sample rate '
            f'{sample_rate:e} and sample count {sample_count:e}.')


def _validate_amplitude(amplitude):
    """Helper function to validate an amplitude."""
    if amplitude.any() < 0:
        raise ValueError(f'Invalid amplitude {amplitude}, must be positive.')


def _validate_phase(phase):
    """Helper function to validate a phase."""
    if phase < 0 or phase >= 2 * np.pi:
        raise ValueError(f'Invalid phase {phase}, must be in [0, 2π).')

def tones_array(n_wave, frequency, frequency_spacing): #Omar
    """
    Generate a an array of tones.

    Arguments:
        n_wave (int):
            The number of tones.

        frequency (float):
            frequency in Hz. It's the central frequency of the array if the number of tones is odd while it's the first element of the array if the number of tones is even.

        frequency_spacing (float):
            frequency spacing in Hz.

    Returns:
        numpy.ndarray:
            array of tones.
    """

    f_array = np.zeros((n_wave,), dtype = float)

    # if n_wave%2 != 0:
    #     f_array[int((n_wave-1)/2)] = frequency

    #     for i in range(0, int((n_wave-1)/2)):
    #         f_array[i] = (frequency - (-i + (n_wave-1)/2) * frequency_spacing)

    #     for i in range(int((n_wave+1)/2), n_wave):
    #         f_array[i] = (frequency - (-i + (n_wave-1)/2) * frequency_spacing)

    # if n_wave%2 == 0:
    #     for i in range(0, n_wave):
    #         f_array[i] = (frequency + i * frequency_spacing)

    for i in range(0, n_wave):
        f_array[i] = (frequency + i * frequency_spacing)

    return f_array


def RMS(wave): #Omar
    sq_elems = np.zeros((len(wave),), dtype = np.longdouble)
    for i in range(len(sq_elems)):
        sq_elems[i] = pow(wave[i], 2.0)
    return np.sqrt(1/(len(wave))*(np.sum(sq_elems)))

def Crest_Factor(wave): #Omar
    peak = np.amax(np.abs(wave))
    return 20 * np.log10(peak/RMS(wave))

def kitayoshi_array(n_wave): #Omar
    """
    Generate a an array of phases following Kitayoshi's algorithm.

    Arguments:
        n_wave (int):
            The number of tones.

    Returns:
        numpy.ndarray:
            array of phases.
    """


    phases_array = np.zeros((n_wave,), dtype = float)

    for i in range(0, n_wave):
        phases_array[i] = (np.pi/n_wave)*i*(i+1)

    return phases_array

def random_phases_array(n_wave): #Omar
    """
    Generate a an array of phases randomly distributed inside [0, 2pi) interval.

    Arguments:
        n_wave (int):
            The number of tones.

    Returns:
        numpy.ndarray:
            array of phases.
    """

    random_phases = [random.uniform(0, 2*np.pi) for _ in range(n_wave)]
    return random_phases

# import matplotlib.pyplot as plt
# plt.plot(single_tone(49920, 624e6, 80e6, 1.0, 0.0, True))
# plt.show()
# import numpy as np
# print(kitayoshi_array(5))
