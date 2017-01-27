# PyTree launcher script
# wrappers for viewing tree types in the book, plus test cases/gui
# Source: http://books.gigatux.nl/mirror/pythonprogramming/0596000855_python2-CHP-17-SECT-10.html

import string
from Tkinter import *
from treeview_wrappers import TreeWrapper, TreeViewer
import generic_object


class GenericObjectWrapper(TreeWrapper):
    def __init__(self):
        self.classes = []
        self.generic_objects = {}

    def children(self, node):
        try:
            return node.get_children(self.classes, self.generic_objects)
        except:
            return None
    def label(self, node):
        try:
            if len(node.name) > 0:
                for n in node.name:
                    if '.' not in n:
                        return n
                return '{0}_{1}'.format(node.class_name, node.simple_id)
                # return '*'
            else:
                return '{0}_{1}'.format(node.class_name, node.simple_id)
                # return '*'
        except:
            return str(node)
    def value(self, node):
        try:
            return node.__repr__()
        except:
            return str(node)


class GenericTree(generic_object.GenericObject):
    def __init__(self, viewer, generic_object):
        self.generic_object = generic_object
        self.viewer = viewer

    def view(self):
        self.viewer.drawTree(self.generic_object)
