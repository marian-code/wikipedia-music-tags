from functools import wraps
from threading import Thread, Lock
import os
import sys
import time
from pprint import pprint

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from lock import a, b

counter = 0

def synchronized(lock):
    """ Synchronization decorator. """

    def real_wrapper(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            lock.acquire()
            try:
                return function(*args, **kwargs)
            finally:
                lock.release()
        return wrapper
    return real_wrapper

@synchronized(a.lock)
def worker():
    print("a lock engaged:", a.lock.locked())
    pprint(globals())
    print("\n------------------------------------\n")
    print(locals())
    a.count += 1
    b = 1
    time.sleep(0.1)



threads = []
for i in range(2):
    t = Thread(target=worker)
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print(a.count)
print(b)

