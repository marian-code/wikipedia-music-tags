import queue
import time
import threading

num_worker_threads = 2


def do_work(item):
    print("doing work")
    time.sleep(0.2)


def source():
    return (i for i in range(10))


def worker():
    print("worker", threading.get_ident())
    while True:
        item = q.get()
        if item is None:
            break
        do_work(item)
        q.task_done()


q = queue.Queue()
threads = []
for i in range(num_worker_threads):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

for item in source():
    print("putting item")
    q.put(item)

# block until all tasks are done
print("joining")
q.join()

# stop workers
print("putting none")
for i in range(num_worker_threads):
    q.put(None)
print("joining threads")
for t in threads:
    t.join()