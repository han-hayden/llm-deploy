"""Background task worker — ThreadPoolExecutor-based task management."""

import logging
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable

logger = logging.getLogger(__name__)

_executor: ThreadPoolExecutor | None = None
_futures: dict[str, Future] = {}


def get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="bg-worker")
    return _executor


def submit_task(task_id: str, fn: Callable, *args, **kwargs) -> Future:
    """Submit a background task. Returns a Future."""
    executor = get_executor()
    future = executor.submit(fn, *args, **kwargs)
    _futures[task_id] = future
    return future


def get_task_future(task_id: str) -> Future | None:
    return _futures.get(task_id)


def cancel_task(task_id: str) -> bool:
    """Attempt to cancel a task. Returns True if successfully cancelled."""
    future = _futures.get(task_id)
    if future and not future.done():
        return future.cancel()
    return False


def is_task_running(task_id: str) -> bool:
    future = _futures.get(task_id)
    return future is not None and future.running()


def shutdown():
    global _executor
    if _executor:
        _executor.shutdown(wait=False)
        _executor = None
    _futures.clear()
