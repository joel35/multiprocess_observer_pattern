"""
1. Register events
2. Create process executor
3. Create observers w/ callbacks
4. Register callbacks to events
5. Start process

"""
import asyncio
import concurrent.futures
import functools
import multiprocessing
from dataclasses import dataclass
from time import sleep

import data_gen_loop
import observable
import observers


def main():
    events = [
        'start',
        'stop',
        'data_ready',
        'print'
    ]

    fps = 10

    manager = multiprocessing.Manager()
    queue = manager.Queue()
    run_flag = manager.Event()
    thread_executor = concurrent.futures.ThreadPoolExecutor()
    process_executor = concurrent.futures.ProcessPoolExecutor()

    # main programme
    event_bus = observable.EventBus(events)

    notifiers = {
        event: observable.EventNotifier(event_bus, event)
        for event
        in events
    }

    futures_manager = observable.FuturesManager(
        cancelled_notify=notifiers['print'],
        error_notify=notifiers['stop'],
        result_notify=notifiers['print'],
    )

    executor_manager = observable.ExecutorManager(
        thread_executor=thread_executor,
        process_executor=process_executor,
        futures_manager=futures_manager
    )

    # event_bus.futures_manager = futures_manager
    event_bus.executor_manager = executor_manager

    # observers
    print_me = observers.PrintMe()

    loop = data_gen_loop.Loop(
        get_func=data_gen_loop.DataGen(data_len=10).generate_data,
        put_func=data_gen_loop.QueueAdder(queue),
        run_flag=run_flag,
        wait_len=1 / fps
    )

    queue_checker = data_gen_loop.QueueChecker(
        queue=queue,
        run_flag=run_flag,
        notify_func=notifiers['data_ready'],
        wait_len=1 / fps
    )

    run_flag_manager = data_gen_loop.RunFlagManager(run_flag)

    count_down = CountDown(
        run_flag=run_flag,
        count_notify=notifiers['print'],
        end_notify=notifiers['stop'],
        start=10
    )

    event_bus.register('start', print_me, print_me.callback)
    event_bus.register('start', run_flag_manager, run_flag_manager.set)
    event_bus.register('start', loop, loop.start, spawn_new_process=True)
    event_bus.register('start', queue_checker, queue_checker.loop)
    event_bus.register('start', count_down, count_down)

    event_bus.register('data_ready', print_me, print_me.callback)
    event_bus.register('stop', print_me, print_me.callback)
    event_bus.register('stop', run_flag_manager, run_flag_manager.clear)
    event_bus.register('print', print_me, print_me.callback)

    event_bus.notify('start', 'Program starting!')


@dataclass
class CountDown:
    run_flag: multiprocessing.Event()
    count_notify: observable.IEventNotifier
    end_notify: observable.IEventNotifier
    start: int

    def __call__(self, *args, **kwargs):
        i = self.start
        while self.run_flag.is_set() and i > 0:
            self.count_notify(i)
            i -= 1
            sleep(1)

        if self.run_flag.is_set():
            self.end_notify('Reached zero!')


if __name__ == '__main__':
    main()
