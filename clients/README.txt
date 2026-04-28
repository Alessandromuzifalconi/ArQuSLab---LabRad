This client is used to homogenize the tweezer array produced from the AOD, driven with the Spectrum Card.
To use this client you need to:

- activate the SC server: \\ARQUS-NAS\ArQuS Shared\LabRad\servers\Spectrum_Card\m4i_6621_x8_server
- define the settings for the client (camera type, number of tones, sample rate ecc...)
- here the SC is used in trigger mode, so ensure that a TTL is feeding the SC before running the last cell

The script defines a waveform that the PC sends to the spectrum card. Then an image is acquired and saved into a
specific folder. The image is Gaussian fitted to retrieve the amplitude of each tone. Such amplitudes are used
to get an error for each tweezer and to correct the AOD driving tones to reduce the mismatch between each tone.
For the fit to work correctly, you have to give the initial y coordinate of the tweezer array (in pixel). Once this
is given it makes the fit automatically.
This procedure is iterated up to the number of times you have chosen at the start of the loop. Once you reach the
desired coefficient of variation (CV), you can interrupt the loop. Then you can copy the RF amplitude array relative to
the minimized CV to the client used for the tones generation.

Tips and possible troubles:
- ensure that the camera you are using is at the focus position before starting
- select a slice of the image to minimize the time needed for each fit. There are not particular trouble checks
  in the script, meaning that if the slice does not contain the tweezer array, it will give ugly errors (it could be
  necessary to comment some part of the script to let it print the array without errors to find the right slice, feel
  free to upgrade the script :))
- remember that when you change the number of tones, the VPP of the multitone waveform will change. Accordingly, you
  have to increase or reduce the output voltage of the SC to account it. I usually change it maximizing the power on
  the first order of the AOD.
- when using the ThorCam for image acquisition, use the ArqusCAM PC for running the script. For some unknown reasons
  I have never been able to use the pylablib library for the Thorcam in other PCs. It gives an error (feel free to debug)

That's it. Enjoy