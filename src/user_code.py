def long_name_function(long_name_variable_1, long_name_variable_2):
   return long_name_variable_1 + long_name_variable_2

def f(a, b, c, d):
   z = a + b + (c * d)
   return z

# This is a comment
def g():
   return 1

a = 1
b = 2
i = 0

while i < 3:
   a = f(a, b, 0, 0) + g()
   i += 1

print qart

print a
print 2

a12 = 1
a3 = []
a3.append(1)
print a3
a = 1
a1 = []
a2 = a1
a1.append(1)
a2.append(2)
print a1
print a2
print 1
a4 = [1, 2, 3, 4]
a4.append(5)
f_ = a4.append
print a4
f_(6)
print a4
f_2 = a4.append

for i in [1,2,3,4]:
   print i

for i in a4:
   print i

class Node():
   def __init__(self):
      self.value = None
      self.left = None
      self.right = None
      self.left_center = None
      self.right_center = None
      self.center = None

   def set_value(self, v, a, b, c, d):
      a = 2
      self.value = v
      self.q = 8

   def get_value(self):
      return self.value

   def set_left(self, n):
      self.left = n

   def get_left(self):   
      return self.left   
               
class really_long_name():
   def __init__(self):
      self.v = None

n8 = Node()
n = Node()
print n
n7 = Node()
n.center = Node()
n.left_center = Node()
n.right_center = Node()
n.set_value(10, 1, 2, 3, 4)
n.left = Node()
n.left.left = Node()
n.left.left.right = really_long_name()
n.left.left.right.left = Node()
n2 = n.left
n2.right = Node()
n2.right.right = n2
n.left.set_value(12, 1, 2, 3, 4)
n.left.left.set_value(13, 1, 2, 3, 4)
print n.value
print n.left.get_value()

i = 0
head = n
while i < 5:
   head.right = Node()
   head = head.right
   head.value = i
   i += 1
head.right = n


def sum(x,y):
   z = x + y
   return z

def mult(x,y):
   z = x * y
   return z


a = 1
b = 2
c = sum(a,b)
print c
print sum(5, 5)
q = mult(a, b)
c = 7
d = 8
mult(c, sum(a,b))
a = [0, 1, 2, 3]
print a
print len(a)
i = 0
while i < 10:
   print i
   i += 1

def test():
   print 1

a = 1
b = 3
print 7
a = 2
test()
user_input = input()
print user_input
print user_input + 1
user_input2 = input()
print user_input2

