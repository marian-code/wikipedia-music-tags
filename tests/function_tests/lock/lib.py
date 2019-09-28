from threading import Lock

class A():

    def __init__(self):
        self.count = 0
        self.lock = Lock()

b = 0