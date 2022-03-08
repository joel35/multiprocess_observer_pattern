import concurrent.futures
import multiprocessing
from dataclasses import dataclass, field
from time import sleep
from typing import Callable

import data_gen_loop
import observable
import observers


def main():
    events = [
        'start',
        'stop',
        'clock_cycle',
        'data_ready',
        'print'
    ]

    fps = 100

    manager = multiprocessing.Manager()
    queue = manager.Queue()
    run_flag = manager.Event()

    # main programme
    event_bus = observable.EventBus()

    notifiers = {
        event: observable.ObservableEventNotifier(event_bus, event)
        for event
        in events
    }

    clock = Clock(run_flag=run_flag, cycles_per_second=fps, clock_func=notifiers['clock_cycle'])

    loop = data_gen_loop.Loop(
        get_func=data_gen_loop.DataGen(data_len=10).generate_data,
        put_func=data_gen_loop.QueueAdder(queue),
        run_flag=run_flag,
        wait_len=1 / fps
    )

    queue_checker = data_gen_loop.QueueChecker(
        queue=queue,
        wait_len=1 / fps
    )

    count_down = CountDown(
        run_flag=run_flag,
        count_notify=print,
        start=3
    )

    run_flag_manager = data_gen_loop.RunFlagManager(run_flag)

    set_run_flag = observers.Observer(run_flag_manager.set)
    clear_run_flag = observers.Observer(run_flag_manager.clear)
    start_count_down = observers.Observer(call_on_notify=count_down, call_on_done=notifiers['stop'])

    check_data_queue = observers.Observer(
        call_on_notify=queue_checker,
        call_on_done=notifiers['data_ready'],
    )

    start_data_gen = observers.Observer(
        call_on_notify=loop.start,
        call_on_cancelled=print,
        spawn_new_process=True,
        call_on_exception=RaiseException(call_before_raise=notifiers['stop'])
    )

    start_clock = observers.Observer(call_on_notify=clock.start)
    printer = observers.Observer(call_on_notify=print)

    start_event_observers = [
        printer,
        set_run_flag,
        start_data_gen,
        start_clock,
        start_count_down
    ]

    clock_cycle_event_observers = [
        check_data_queue
    ]

    data_ready_event_observers = [
        printer
    ]

    stop_event_observers = [
        printer,
        clear_run_flag
    ]

    registrations = dict(
        start=start_event_observers,
        clock_cycle=clock_cycle_event_observers,
        data_ready=data_ready_event_observers,
        stop=stop_event_observers
    )

    for event, obs in registrations.items():
        [event_bus.register(event, ob) for ob in obs]

    event_bus.notify('start', 'Program starting!')


@dataclass
class CountDown:
    run_flag: multiprocessing.Event()
    count_notify: Callable
    start: int

    def __call__(self, *args, **kwargs):
        i = self.start
        while self.run_flag.is_set() and i > 0:
            self.count_notify(i)
            i -= 1
            sleep(1)

        if self.run_flag.is_set():
            return 'Program Stopping!'


class Clock:
    def __init__(
            self,
            run_flag: multiprocessing.Event,
            cycles_per_second: int,
            clock_func: Callable[[int], None]
    ) -> None:
        self._run_flag = run_flag
        self._clock_func = clock_func
        self._cycles_per_second = cycles_per_second
        self._wait_length = 1 / cycles_per_second

    def start(self, *args, **kwargs):
        self._loop()

    def _loop(self):
        count = 0
        print(f'Starting clock @ {self._cycles_per_second} cycles per second')
        while self._run_flag.wait(self._wait_length):
            self._clock_func(count)
            count += 1
            sleep(self._wait_length)

        print('Stopping clock')


@dataclass
class RaiseException:
    call_before_raise: Callable = field(default=None)

    def __call__(self, exception: BaseException):
        if self.call_before_raise:
            self.call_before_raise(exception)
        raise exception


if __name__ == '__main__':
    main()
