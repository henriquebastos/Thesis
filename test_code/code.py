# def add(x, y):
#    z = x + y + 5 * 3 + x * y
#    return z

# class Add(object):
#    def __init__(self):
#       self.x = 1
#       self.y = 2
#       self.z = self.x

#    def plus1(self, n):
#       return n + self.x

#    def magic(self, x, y, z):
#       a = b = c = 123
#       x = a + c * self.x + c * (b - self.y / y)
#       return x + a % self.z


# a = 1
# b = 2
# c = add(a, b)
# c = add(c, c)
# print c
# a = b = c = d = 0
# a = 1
# b = 2
# c = 3
# d = 4
# e = a + b + c + d
# f = a * b * (c + e) - a / b * (a + b)
# z = a & b

# if a > 0 and \
#       (b < 5 or a == b):
#    a = 2
# if a > 0 and b < 5 or a == b:
#    a = 2
# if not a:
#    a = 2

# if not a and not (a or b):
#    a = 2
# l = [1, a, b, 4]
# for i in l:
#    i += 1
#    i += c
#    print i
# i = 0
# while i < len(l):
#    l[i+1*a] = i


# print e
# print f

# for x,y in zip(l, l):
#    x + y
# l = [1, a, b, 4]
# del l[a]

# with open('output.txt', 'w') as f:
#    x + y
#    f.write('Hi there!')
# try:
#    f = None
#    l[f] = 0
#    print l[f]
# except:
#    raise KeyError
d = {}

d['hi'] = 'hello world'
d[a] = c*d
d[a+10] = c*d+10

d = {
   'hi': 1,
   'bye': a + b
}

# Needed for Assignment statements
# Assignee = Result
# a = 1
# { Dictionary of line numbers line number}
#     { Dictionary of information}
#     Keys: 'type',   'assigned', 'result (final equation or number', 'expressions'}
#           'assign', 'e'         '(((a+b)+c)+d)'                   , ['a', 'b', '(a+b)', 'c', '((a+b)+c)', 'd', '(((a+b)+c)+d)']

#
# {
#   1: { 'type': 'assign', 'assigned': 'a', 'result': '0', 'expressions': [] },
#   2: { 'type': 'if', 'assigned': None, 'result': '(a>0 and (b<5 or a==b))', 'expressions': ['a', '0', 'a>0', 'b', '5', 'b<5', 'a==b', '(b<5 or a==b)', '(a>0 and (b<5 or a==b))'] },
#   3: { 'type': 'for', 'assigned': ['i'], 'result': 'l', 'expressions': ['l'] }
# }