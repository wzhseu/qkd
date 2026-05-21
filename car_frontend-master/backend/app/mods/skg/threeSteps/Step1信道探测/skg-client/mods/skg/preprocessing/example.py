import numpy as np
from scipy import signal
from scipy import fft

## This is an example for preprocessing.
class MyFirstPreprocessingMod:
    def __init__(self, send_waveform_from):
        self._sent_waveform = np.fromfile(open(send_waveform_from), dtype=np.complex64)

    def process(self, save_waveform_to):
        dumped_waveform = np.fromfile(open(save_waveform_to), dtype=np.complex64)
        if len(dumped_waveform) <= 0:
            return []
        corr = np.abs(signal.correlate(dumped_waveform, self._sent_waveform))
        lags = signal.correlation_lags(len(dumped_waveform), len(self._sent_waveform))
        max_corr = 0.0
        delay = 0
        for idx, cor in enumerate(corr):
            if cor > max_corr:
                delay = lags[idx]
                max_corr = cor
        ## The m-sequence is 4095-bit.
        dumped_waveform = dumped_waveform[delay:delay+4095]

        corr = signal.correlate(self._sent_waveform, dumped_waveform)
        corr /= np.max(corr)
        impulse_resp = corr
        sinc_func = np.sinc(4096)
        window = np.blackman(4096)
        sinc_func = sinc_func * window
        sinc_func = sinc_func / np.sum(sinc_func)
        impulse_resp = np.convolve(impulse_resp, sinc_func)
        impulse_resp = signal.resample(impulse_resp, 512)
        impulse_resp = np.abs(impulse_resp)
        ## impulse_resp = signal.savgol_filter(np.abs(impulse_resp), 55, 11)
        impulse_resp /= np.max(impulse_resp)
        return impulse_resp.tolist()
