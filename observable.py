from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Callable
import concurrent.futures as cf

from chaos import timebomb


class IObservable(ABC):
    @abstractmethod
    def register(self, event, observer, callback):
        pass

    @abstractmethod
    def unregister(self, event, observer):
        pass

    @abstractmethod
    def notify(self, event, message=None):
        pass

    @abstractmethod
    def get_subscribers(self, event):
        pass


class IEventNotifier(ABC):
    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class EventBus(IObservable):
    def __init__(self, events: List[str]):
        self.events = {event: dict() for event in events}
        self.executor_manager: ExecutorManager = None

    def generate_id(self, obj: object) -> int:
        return id(obj)

    def register(self, event: str, observer: object, callback: Callable, spawn_new_process: bool = False):
        observer_id = self.generate_id(observer)
        self.get_subscribers(event)[observer_id] = (callback, spawn_new_process)

    def unregister(self, event, observer):
        observer_id = self.generate_id(observer)
        del self.get_subscribers(event)[observer_id]

    def notify(self, event, message=None):
        subscribers = self.get_subscribers(event)
        self.executor_manager(subscribers, message)

    def get_subscribers(self, event):
        return self.events[event]


@dataclass
class FuturesManager:
    cancelled_notify: IEventNotifier
    error_notify: IEventNotifier
    result_notify: IEventNotifier

    def manage_done(self, fn: cf.Future):
        if fn.cancelled():
            self.cancelled_notify(f'{fn} was cancelled!')
        elif error := fn.exception():
            self.error_notify(f'ERROR: {error}')
            raise error
        else:
            result = fn.result()
            if result is not None:
                self.result_notify(result)


@dataclass
class ExecutorManager:
    thread_executor: cf.ThreadPoolExecutor
    process_executor: cf.ProcessPoolExecutor
    futures_manager: FuturesManager

    def __call__(self, subscribers: dict, msg):
        for func, spawn in subscribers.values():
            if spawn:
                f: cf.Future = self.process_executor.submit(func, msg)
            else:
                f: cf.Future = self.thread_executor.submit(func, msg)

            f.add_done_callback(self.futures_manager.manage_done)



@dataclass
class EventNotifier(IEventNotifier):
    observable: IObservable
    event: str

    def __call__(self, msg, *args, **kwargs):
        self.observable.notify(self.event, msg)
