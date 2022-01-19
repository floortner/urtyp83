import jsonpickle
import datetime

class prop:
    def __init__(self, str, xyz):
        self.str = str
        self.xyz = xyz
    
    def __str__(self):
        return f'str={self.str}, xyz={self.xyz}'

class meh:
    def __init__(self, myname):
        self.myname = myname
        self.props = {}
        self.ts_start = None
    
    def __str__(self):
        return f'myname={self.myname}, len props={len(self.props)}'
    
    def add(self, p):
        self.props[p.str] = p
        
    def setnow(self):
        self.ts_start = datetime.datetime.now()

if __name__ == "__main__":
    p = prop('bla', 123)
    m = meh('hello')
    m.add(p)
    m.add(prop('blu', 666))
    m.setnow()

    print(m)
    for i in m.props:
        print(m.props[i])
    
    j = jsonpickle.encode(m)
    print(j)