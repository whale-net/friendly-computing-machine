import concurrent.futures
import datetime
import logging
import threading
from typing import Optional


def ts_to_datetime(ts: str):
    # yes ts is a str in the event payload
    return datetime.datetime.fromtimestamp(float(ts))


logger = logging.getLogger(__name__)


class NamedThreadPool(concurrent.futures.ThreadPoolExecutor):
    def submit(
        self, fn, /, thread_name: Optional[str] = None, *args, **kwargs
    ) -> concurrent.futures.Future:
        def exec_and_rename_thread():
            if thread_name is not None and len(thread_name) > 0:
                logger.debug(
                    f"renaming {threading.current_thread().name} to {thread_name}"
                )
                threading.current_thread().name = thread_name
            fn(*args, **kwargs)

        return super().submit(exec_and_rename_thread)
