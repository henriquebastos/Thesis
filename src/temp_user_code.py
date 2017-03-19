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
_test_obj_=Node()
n = 23
_test_obj_.set_left(n)
_test_obj_.get_left()
v = 23
a = 2
b = 2
c = 2
d = 2
_test_obj_.set_value(v,a,b,c,d)
_test_obj_.get_value()
