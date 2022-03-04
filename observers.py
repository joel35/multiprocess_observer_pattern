from abc import ABC, abstractmethod


class IObserver(ABC):
    @abstractmethod
    def callback(self, *args, **kwargs):
        pass


class PrintMe(IObserver):
    def callback(self, msg, *args, **kwargs):
        print(msg)
