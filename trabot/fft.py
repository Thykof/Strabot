import sys


import numpy as np
import matplotlib.pyplot as plt
from scipy.fftpack import fft, fftfreq


from trabot.stream import *
from trabot.utils import *


def fft_plot():
    """Get prices from file or hitbtc, fft and plot.
    Read sys argument, if any, get from ticker the given number of prices,
    else, read a default file for a seq.
    """
    print("Start fft")
    if len(sys.argv) == 2:
        n_seq = int(sys.argv[1])
        steps, prices = get_seq(n_seq=n_seq)
        print(steps)
        print(prices)
        if steps == [] and prices == []:
            print('no data')
            return
        save_seq(prices, steps, 'data/seq')
    else:
        steps, prices = read_seq('data/seq-1')

    fe = 1.0/average(steps)  # Hz
    prices_fft = abs(fft(prices))
    prices_freq = fftfreq(len(prices), 1.0/fe)

    # extraction des valeurs réelles de la FFT et du domaine fréquentiel:
    prices_fft = prices_fft[0:len(prices_fft)//2]
    prices_freq = prices_freq[0:len(prices_freq)//2]
    # Graph
    print(type(np.linspace(0, sum(steps), sum(steps)*fe))) # begin, end, N
    # x axis
    t = list()
    t.append(steps[0])
    for i in range(1, len(steps)):
        t.append(steps[i] + t[i-1])
    print(steps)
    print(t)
    ## Prices
    plt.subplot(2, 1, 1)
    plt.plot(t, prices)
    plt.ylim(min(prices), max(prices))
    plt.xlim(t[0], t[-1])

    ## FFT prices
    plt.subplot(2, 1, 2)
    plt.plot(prices_freq, prices_fft)
    """
    # demo fft with sin
    fe = 300#Hz
    plt.subplot(2, 1, 1)
    seq = np.sin(2*np.pi*t*50)
    plt.plot(t, seq)
    plt.subplot(2, 1, 2)
    seq_fft = abs(fft(seq))
    seq_fft = seq_fft[0:len(seq_fft)//2]
    seq_freq = fftfreq(len(seq), 1.0/fe)
    seq_freq = seq_freq[0:len(seq_freq)//2]
    plt.plot(seq_freq, seq_fft)
    """
    plt.show()
