from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Any, Callable
import concurrent.futures as cf

import observers


class IObservable(ABC):
    """Interface for observable object"""

    @property
    @abstractmethod
    def events(self) -> dict:
        pass

    @abstractmethod
    def register(self, event, observer):
        pass

    @abstractmethod
    def unregister(self, event, observer):
        pass

    @abstractmethod
    def notify(self, event, message=None):
        pass

    @abstractmethod
    def get_observers(self, event):
        pass


class IObservableEventNotifier(ABC):
    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class IObserverExecutor(ABC):
    @abstractmethod
    def __call__(self, ob_id: Any, ob: observers.IObserver, msg: Any) -> None:
        pass


class Singleton:
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = object.__new__(cls)
        return cls._instances[cls]


@dataclass
class FutureObjectOutputManager:
    thread_id: Any
    on_done: Callable[[Any], None]
    on_cancelled: Callable[[str], None]
    on_exception: Callable[[BaseException], None]

    def __call__(self, fut: cf.Future, *args, **kwargs) -> None:
        if fut.cancelled():
            self.on_cancelled(f'Thread {self.thread_id} was cancelled before it could complete execution.')

        elif exception := fut.exception():
            self.on_exception(exception)
        else:
            result = fut.result()
            if result is not None:
                self.on_done(result)


class ObserverExecutor(IObserverExecutor):
    thread_executor = cf.ThreadPoolExecutor()
    process_executor = cf.ProcessPoolExecutor()

    def __call__(self, ob_id: int, ob: observers.IObserver, msg: Any) -> None:
        f = self._execute_in_new_process(ob.on_notify, msg) \
            if ob.spawn_new_process \
            else self._execute_in_new_thread(ob.on_notify, msg)
        f.add_done_callback(self._get_done_callback(ob_id, ob))

    def _execute_in_new_process(self, func: Callable[[Any], Any], msg: Any) -> cf.Future:
        return self.process_executor.submit(func, msg)

    def _execute_in_new_thread(self, func: Callable[[Any], Any], msg: Any) -> cf.Future:
        return self.thread_executor.submit(func, msg)

    @staticmethod
    def _get_done_callback(ob_id: int, ob: observers.IObserver) -> FutureObjectOutputManager:
        return FutureObjectOutputManager(
            thread_id=ob_id,
            on_done=ob.on_done,
            on_cancelled=ob.on_cancelled,
            on_exception=ob.on_exception
        )


class EventBus(IObservable, Singleton):
    _events = {}  # empty dict

    def __init__(self, events: list = None, executor: IObserverExecutor = None) -> None:
        if events:
            [self._add_event(event) for event in events]

        self._executor = executor or ObserverExecutor()

    @property
    def events(self) -> dict:
        return self._events

    def register(self, event: str, observer: observers.IObserver) -> None:
        key = self._generate_id(observer)
        self.get_observers(event)[key] = observer

    def unregister(self, event: str, observer: observers.IObserver) -> None:
        key = self._generate_id(observer)
        del self.get_observers(event)[key]

    def notify(self, event: str, message=None) -> None:
        obs = self.get_observers(event)
        [self._executor(ob_id, ob, message) for ob_id, ob in obs.items()]

    def get_observers(self, event: str) -> dict:
        if not self._event_exists(event):
            self._add_event(event)
        return self.events[event]

    @staticmethod
    def _generate_id(obj) -> int:
        return id(obj)

    def _add_event(self, event: str) -> None:
        self.events[event] = {}

    def _event_exists(self, event: str) -> bool:
        return event in self.events


@dataclass
class ObservableEventNotifier(IObservableEventNotifier):
    observable: IObservable
    event: str

    def __call__(self, msg: Any, *args, **kwargs) -> None:
        self.observable.notify(self.event, msg)
