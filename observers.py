from abc import ABC, abstractmethod
from typing import Callable, Any


class IObserver(ABC):

    @property
    @abstractmethod
    def spawn_new_process(self) -> bool:
        pass

    @abstractmethod
    def on_notify(self, msg: Any, *args, **kwargs) -> Any:
        """Method to be called by subscribed observable object"""
        pass

    @abstractmethod
    def on_done(self, result: Any, *args, **kwargs) -> None:
        """Method to be called when a thread running on_notify() method is completes successfully."""
        pass

    @abstractmethod
    def on_exception(self, exception: BaseException, *args, **kwargs) -> None:
        """Method to be called when a thread running on_notify() raises an exception"""
        pass

    @abstractmethod
    def on_cancelled(self, *args, **kwargs) -> None:
        """Method to be called when a thread running on_notify() is cancelled prior to successful completion"""
        pass


class Observer(IObserver):
    def __init__(
            self,
            call_on_notify,
            spawn_new_process: bool = False,
            call_on_done: Callable = None,
            call_on_exception: Callable = None,
            call_on_cancelled: Callable = None
    ) -> None:
        self._spawn_new_process = spawn_new_process
        self._call_on_notify = call_on_notify
        self._call_on_done = call_on_done
        self._call_on_exception = call_on_exception
        self._call_on_cancelled = call_on_cancelled

    @property
    def spawn_new_process(self) -> bool:
        return self._spawn_new_process

    def on_notify(self, msg: Any, *args, **kwargs) -> Any:
        return self._call_on_notify(msg)

    def on_done(self, result: Any, *args, **kwargs) -> None:
        if self._call_on_done and result is not None:
            self._call_on_done(result)

    def on_exception(self, exception: BaseException, *args, **kwargs) -> None:
        if self._call_on_exception and exception:
            self._call_on_exception(exception)
        elif exception:
            raise exception

    def on_cancelled(self, *args, **kwargs) -> None:
        if self._call_on_cancelled:
            self._call_on_cancelled()
