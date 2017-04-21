a = 1
b = 2
i = 0

def f(a, b, c, d):
   z = a + b + (c * d)
   return z

def g():
   return 1

while i < 3:
   a = f(a, b, 0, 0) + g()
   i += 1

print a

i = 0
while i < 5:
   x = input()
   print x
   i += 1

class List():
   def __init__(self):
      self.value = None
      self.next = None

   def set(self, v):
      self.value = v

   def add(self, n):
      self.next = n

l = List()
l.set(0)
h = l

i = 1
while i < 5:
   t = List()
   t.set(i)
   l.add(t)
   l = t
   i += 1
