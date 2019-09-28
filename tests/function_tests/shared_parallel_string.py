from multiprocessing import Process, Value, Array, Manager
import ctypes

def f(n, a):
    n.value = "cau"
    a[0].value = "a"
    a[1].value = "hovno"

    a[9].value = "nic"
    print(len(a))
    #a[1] = ctypes.c_wchar_p("dddd".encode('utf-8'))

if __name__ == '__main__':
    manager = Manager()
    num = manager.Value(ctypes.c_wchar_p, "ahoj")

    pole = []
    for i in range(10):
        pole.append(manager.Value(ctypes.c_wchar_p, "ahoj"))
        print(pole[i].value)

    print(len(pole))
    print("đ#đđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđđ")

    p = Process(target=f, args=(num, pole, ))
    p.start()
    p.join()

    print(len(pole))

    for i in range(10):
        print(pole[i].value)
