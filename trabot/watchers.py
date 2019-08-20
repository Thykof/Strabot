from threading import Thread
import time


from trabot import helpers


class Watcher(Thread):
    def __init__(self, func, name):
        Thread.__init__(self)
        self.func = func
        self.start_time = None
        self.name = name

    def run(self):
        self.start_time = time.time()
        self.func()
        helpers.store_stats(time.time() - self.start_time, self.name + '.stat')
