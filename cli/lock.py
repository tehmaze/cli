"""Locking mechamisms."""

import threading


class ThreadLock:
    """Thread safe lock, to be used as a context manager.

    >>> lock = ThreadLock()
    >>> with lock:
    ...     do_thread_safe_thing()
    """

    def __init__(self):
        """Thread safe lock."""
        self.lock = threading.Lock()

    def __enter__(self):
        """Context wrapper for the lock."""
        self.acquire(True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context releasing the previously acquired lock."""
        self.release()

    def acquire(self, block=True, timeout=-1):
        """Acquire a lock, blocking or non-blocking."""
        self.lock.acquire(block, timeout)

    def release(self):
        """Release a lock."""
        self.lock.release()
