import parser
import ast
import tokenize
import StringIO
import compiler

code = '1/(2+4) * (a + 4) - 5 / f(x)'
a = 5
print code

print '\nParser\n'
# st = parser.expr(code)
# print st
# print st.compile()
# print st.tolist()
# print st.totuple()
# print eval(st.compile())

print '\nAST\n'
tree = ast.parse('1 + 2 + f(3)')
# r = ''
# for e in st.body:
#    print e.value.op
#    print e.value.left.op
#    print e.value.left.left.n
#    print e.value.left.right.n
#    print e.value.right.n

# print st.body[0].Print()

# def str_node(node):
#     if isinstance(node, ast.AST):
#         fields = [(name, str_node(val)) for name, val in ast.iter_fields(node) if name not in ('left', 'right')]
#         rv = '%s(%s' % (node.__class__.__name__, ', '.join('%s=%s' % field for field in fields))
#         return rv + ')'
#     else:
#         return repr(node)
# def ast_visit(node, level=0):
#     print('  ' * level + str_node(node))
#     for field, value in ast.iter_fields(node):
#         if isinstance(value, list):
#             for item in value:
#                 if isinstance(item, ast.AST):
#                     ast_visit(item, level=level+1)
#         elif isinstance(value, ast.AST):
#             ast_visit(value, level=level+1)


# ast_visit(ast.parse('a + b * 3'))

print '\nTokenize\n'
s = '1 + 2 + 3'
token_list = [[]]
index = 0
with open('./code.py', 'rb') as f:
   tokens = tokenize.generate_tokens(f.readline)
   for toknum, tokval, a, b, c  in tokens:
      if tokval == '\n':
         index += 1
         token_list.append([])
      else:
         token_list[index].append(tokval)

for line in token_list:
   print line

# print '\nCompiler\n'
# c = compiler.parse(code)
# print c
# ast_V = compiler.visitor.ASTVisitor()
# v = compiler.walk(c, ast_V)
# print ast_V
# print v
# print ast_V.default(v)

import meta
node = ast.parse('sum_matrix(m1, m2)')
# meta.asttools.print_ast(node, indent='', newline='\n')
meta.asttools.python_source(node)

# (((1 / (2 + 4)) * (a + 4)) - (5 / f(x)))

# [0] - (2 + 4)
# [1] - (1 / (2 + 4))
# [2] - (a + 4)
# [3] - ((1 / (2 + 4)) * (a + 4))
# [4] - f(x)
# [5] - (5 / f(x))
# [6] - (((1 / (2 + 4)) * (a + 4)) - (5 / f(x)))

# [0] - 6
# [1] - 0.166666
# [2] - 9
# [3] - 1.5
# [4] - 7
# [5] - 0.7142857
# [6] - 6.2857142

class Node(object):
   def __init__(self):
      self.s = None

   def add_char(self, c):
      if self.s is None:
         self.s = c
      else:
         self.s += c

   def add_component(self, n):
      if self.s is None:
         self.s = '(' + n.s + ')'
      else:
         self.s += '(' + n.s + ')'

   def equals(self, n):
      return self.s == n.s


def build_list(s):
   l = []
   build_node_list(list(s), 0, Node(), l)
   return l

def add_function_call(s, i, l):
   n = Node()
   n.add_char(s[i])
   n.add_char('(')
   r, i = build_node_list(s, i+2, n, l)
   r.add_char(')')
   return r, i

def build_node_list(s, i, n, l):
   while i < len(s):
      node = None
      if s[i] == '(':
         node, i = build_node_list(s, i+1, Node(), l)
      elif s[i] == ')':
         l.append(n)
         return n, i
      elif s[i] != ' ':
         if s[i+1] == '(':
            node, i = add_function_call(s, i, l)
         else:
            n.add_char(s[i])
      i += 1
      if node is not None:
         n.add_component(node)
   return None, i

l = build_list('(((1 / (2.0 + 4)) * (a + 4.0)) - (5.0 / f(x)))')
print '----'
for n in l:
   print n.s
print
l = build_list('r[(len(r) - 1)].append((c1 + c2))')
for n in l:
   print n.s

# FOIL
