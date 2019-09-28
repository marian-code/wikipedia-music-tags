from functools import wraps
from threading import Thread, Lock

counter = 0

def synchronized(lock):
    """ Synchronization decorator. """

    def real_wrapper(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            global lock
            lock.acquire()
            try:
                return function(*args, **kwargs)
            finally:
                lock.release()
        return wrapper
    return real_wrapper

def worker():
    a.count += 1

class A():

    def __init__(self):
        self.count = 0
        self.lock = Lock()


a = A()

threads = []
for i in range(10):
    t = Thread(target=worker)
    threads.append(t)
    t.start()

print(a.count)

