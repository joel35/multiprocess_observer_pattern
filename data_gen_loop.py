import concurrent.futures
import multiprocessing
import queue
import random
from dataclasses import dataclass, field
from time import sleep
from typing import Callable, Any

import numpy as np

from chaos import timebomb


@dataclass
class RunFlagManager:
    run_flag: multiprocessing.Event

    def set(self, *args, **kwargs):
        print('setting run flag')
        self.run_flag.set()

    def clear(self, *args, **kwargs):
        print('clearing run flag')
        self.run_flag.clear()


class DataGen:
    def __init__(self, data_len=10):
        self.data_len = data_len

    # @timebomb(random.randint(1, 20))
    def generate_data(self, *args, **kwargs):
        return np.random.random_sample(self.data_len)


@dataclass
class Loop:
    get_func: Callable[[Any], Any]
    put_func: Callable[[Any], Any]
    run_flag: multiprocessing.Event
    wait_len: float

    def loop(self, *args, **kwargs):
        print('data gen loop starting')
        while self.run_flag.wait(timeout=self.wait_len):
            result = self.get_func(*args, **kwargs)
            self.put_func(result)
            sleep(self.wait_len)
        print('data gen loop stopped')

    def start(self, *args, **kwargs):
        self.loop()


@dataclass
class QueueAdder:
    queue: multiprocessing.Queue

    def __call__(self, obj, *args, **kwargs):
        self.queue.put(obj)


@dataclass
class QueueChecker:
    queue: multiprocessing.Queue
    wait_len: float

    def __call__(self, *args, **kwargs):
        data = None
        try:
            data = self.queue.get(timeout=self.wait_len)
        except queue.Empty:
            pass
        finally:
            return data
