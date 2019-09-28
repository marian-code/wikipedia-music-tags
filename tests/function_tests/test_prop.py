class clas():

    _p = None

    @classmethod
    def prnt(cls):
        print(cls._p)

a = clas()

print(a._p)

b = clas()

print(b._p)
clas._p = 1
print(a._p)
print(b._p)
print(clas._p)
print()
b.prnt()
a.prnt()
clas.prnt()