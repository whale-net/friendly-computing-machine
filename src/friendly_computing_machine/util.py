import concurrent.futures
import datetime
import threading
from typing import Optional


def ts_to_datetime(ts: str):
    # yes ts is a str in the event payload
    return datetime.datetime.fromtimestamp(float(ts))


class NamedThreadPool(concurrent.futures.ThreadPoolExecutor):
    def submit(
        self, fn, /, thread_name: Optional[str] = None, *args, **kwargs
    ) -> concurrent.futures.Future:
        def exec_and_rename_thread():
            if thread_name is not None and len(thread_name) > 0:
                threading.current_thread().name = thread_name
            fn(*args, **kwargs)

        return super().submit(exec_and_rename_thread)
