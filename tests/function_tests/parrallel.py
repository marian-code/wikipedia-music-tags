from time import sleep
import multiprocess as mp
import os
import ctypes

count = mp.Value('i', 0)


def counter(count, a, index):
    print("Starting counter func")

    sleep(1)
    print(a)
    a[index] = "counter"
    print("inside: ")
    for i in a:
        print(i)

    for _ in range(10):
        count.value += 1
        sleep(0.1)
        print("Waking up for the {} time".format(count.value))

def printCounter(count, a, index):
    print("Printing function")

    a[index] = "printcounter"
    print("inside: ")
    for i in a:
        print(i)

    for _ in range(10):
        print("Counter value at {}".format(count.value))
    sleep(0.55)

def main():

    arr = mp.Array(ctypes.c_wchar_p, ["nic"]*5)

    p1 = mp.Process(target = counter, args=(count, arr, 0, ))
    p2 = mp.Process(target = printCounter, args =(count, arr, 1, ))
    
    p1.start()
    p2.start()

    p1.join()
    p2.join()

    print(arr[:])

    for a in arr:
        print(a)

    print("ahoj")

if __name__ == "__main__":
    main()