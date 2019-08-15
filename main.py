from os import path, mkdir


# from trabot.fft import fft_plot
# from trabot import trabot
from trabot import trader
# from trabot import stream


if not path.exists('data'):
    mkdir('data')

def main():
    trader.main()
    # stream.main()
    # fft_plot()
    # trabot.algo()


if __name__ == "__main__":
    main()
