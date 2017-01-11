class Node():
   def __init__(self):
      self.value = None
      self.left = None
      self.right = None

   def set_value(self, v):
      self.value = v

   def get_value(self):
      return self.value

n = Node()
n.set_value(1)
n.left = Node()
n.left.set_value(2)
print n.value
print n.left.get_value()


# print n.get_value()
# print n.get_value()

# n2 = Node()



# def sum(x,y):
#    z = x + y
#    return z

# def mult(x,y):
#    z = y
#    return z

# a = 1
# b = 2
# c = sum(a,b)
# print c
# print sum(1, 2)
# q = mult(a, b)
# c = 7
# d = 8
# mult(c, sum(a,b))
# a = [0, 1, 2, 3]
# print a
# print len(a)
# i = 0
# while i < 10:
#    print i
#    i += 1

# def test():
#    print 1

# a = 1
# b = 3
# print 7
# a = 2
# test()
# user_input = input()
# print user_input
# print user_input + 1
# user_input2 = input()
# print user_input2
