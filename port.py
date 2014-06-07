import math
import random
import time
import itertools

def baseN(num,b,numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
    return ((num == 0) and numerals[0]) or (baseN(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])

class Key:
    def r(self, ss):
        return int(math.floor(ss))
    def i(self, _arg1):
        return self.r(random.random() * _arg1)
    def j(self):
        return 8
    def k (self, _arg1, _arg2):
        return _arg1 ^ _arg2
    def l(self, _arg1, _arg2, _arg3):
        try:
            if len(_arg1) <= _arg2:
                return 1
            if  _arg1[_arg2] == '.':
                return 12345 # not a one bit number
            return int(_arg1[_arg2:_arg2+_arg3])
        except Exception as e:
            print _arg2, _arg3
            print '_arg1',_arg1
            print e
            exit(0)
    def m(self, _arg1, _arg2):
        return _arg1 - _arg2
    def n(self):
        return self.r(time.time())
    def o(self, _arg1, _arg2):
        return _arg2 / _arg1
    def p(self, _arg1, _arg2):
        return _arg2 % _arg1
    def q(self, ):
        return 1.44269504088896
    def s(self, _arg1, _arg2=10):
        return str(int(str(int(_arg1)), _arg2))
        # return baseN(int(_arg1), _arg2)
    def t(self, *_args):
        return ''.join(_args)
    def u(self, _arg1, _arg2):
        return _arg1 + _arg2
    def v(self, ):
        return 16
    def w(self, ):
        return 2
    def x(self, ):
        return 4
    def y(self, _arg1):
        return math.sqrt(_arg1)
    def z(self, _arg1, _arg2):
        return _arg1 * _arg2

key = Key()
Il = [1623,5727,9278,3527,4976,7180734,6632,3708,4796,9675,13,6631,2987,10,1901,9881,1000,3527]

def I1(II, lI):
    ll = 0
    while not (II == lI.l(repr(lI.y(Il[Il[13]])), ll, 1)):
        ll += 1
    return ll

def __(ll, lI):
    return lI.t( \
        lI.s(lI.u(lI.z(Il[lI.v()], lI.u(lI.i(9), 1)), lI.p(Il[lI.v()], ll))), \
        lI.s(lI.z(lI.m(lI.z(Il[(lI.x() | 1)], lI.l(lI.s(ll), 0, lI.x())), lI.u(lI.n(), ll)), Il[I1(lI.p(10, ll), lI)])), \
        lI.s(lI.u(lI.i(lI.z(9, Il[lI.v()])), Il[lI.v()])));

def generate(member_id):
    u = int(member_id)
    return __(u, key)