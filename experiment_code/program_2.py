class List():
   def __init__(self):
      self.value = None
      self.next = None

   def set(self, v):
      self.value = v

   def add(self, n):
      self.next = n

head = List()
head.set(0)
runner = head
i = 1
while i < 5:
   temp = List()
   temp.set(i)
   runner.add(temp)
   runner = temp
   i += 1
