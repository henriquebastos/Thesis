class Node():
   def __init__(self, test):
      self.value = None
   def set_value(self, v, a, b, c, d):
      a = 2
      self.value = v
      self.q = 8
   def get_value(self):
      return self.value
test = 1
_test_obj_=Node(test)
v = 1
a = 2
b = 3
c = 4
d = 5
_test_obj_.set_value(v,a,b,c,d)
_test_obj_.get_value()
v = 6
a = 7
b = 8
c = 9
d = 10
_test_obj_.set_value(v,a,b,c,d)
_test_obj_.get_value()
