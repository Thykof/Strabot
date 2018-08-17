import time
import queue
from os import path, mkdir


from hitbtc import HitBTC


from trabot.fft import fft_plot
from trabot.trabot import algo


if not path.exists('data'):
    mkdir('data')

def main():
    fft_plot()
    algo()


if __name__ == "__main__":
    main()
