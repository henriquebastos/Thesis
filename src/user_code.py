# a3 = []
# a3.append(1)
# print a3
# a = 1
# a1 = []
# a2 = a1
# a1.append(1)
# a2.append(2)
# print a1
# print a2
# print 1
# a4 = [1, 2, 3, 4]
# a4.append(5)
# print a4


# class Node():
#    def __init__(self):
#       self.value = None
#       self.left = None
#       self.right = None
#       self.left_center = None
#       self.right_center = None
#       self.center = None

#    def set_value(self, v):
#       a = 2
#       self.value = v
#       self.q = 8

#    def get_value(self):
#       return self.value

# class really_long_name():
#    def __init__(self):
#       self.v = None

# n = Node()
# #n.center = Node()
# #n.left_center = Node()
# #n.right_center = Node()
# n.set_value(10)
# n.left = Node()
# n.left.left = Node()
# n.left.left.right = really_long_name()
# n.left.left.right.left = Node()
# n2 = n.left
# n.left.set_value(12)
# n.left.left.set_value(13)
# print n.value
# print n.left.get_value()

# i = 0
# head = n
# while i < 5:
#    head.right = Node()
#    head = head.right
#    head.value = i
#    i += 1


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
print sum(1, 2)
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
print a
