# PyTree launcher script
# wrappers for viewing tree types in the book, plus test cases/gui
# Source: http://books.gigatux.nl/mirror/pythonprogramming/0596000855_python2-CHP-17-SECT-10.html

import string
from Tkinter import *
from treeview_wrappers import TreeWrapper, TreeViewer
import generic_object

# generic_objects = {}

class GenericObjectWrapper(TreeWrapper):
    def __init__(self):
        # TreeWrapper.__init__(self)
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
                return '*'
            else:
                return '*'
        except:
            return str(node)
    def value(self, node):
        try:
            return node.__repr__()
        except:
            return str(node)


class GenericTree(generic_object.GenericObject):
    def __init__(self, viewer, generic_object):
        # global generic_objects
        # generic_object.GenericObject.__init__(self, class_name, name, instance_id)
        # generic_objects[instance_id] = self
        # self = generic_object
        self.generic_object = generic_object
        self.viewer = viewer

    def view(self):
        self.viewer.drawTree(self.generic_object)


###################################################################
# build viewer with extra widgets to test tree types
###################################################################

if __name__ == '__main__':
    root = Tk()                             # build a single viewer gui
    wrapper = GenericObjectWrapper()
    viewer   = TreeViewer(wrapper, root)   # start out in binary mode
    
    # tree = GenericTree(viewer, 'Node', 'n1', '01')
    # tree2 = GenericTree(viewer, 'Node', 'n2', '02')
    # tree3 = GenericTree(viewer, 'Node', '', '03')
    # tree4 = GenericTree(viewer, 'Node', 'head', '04')
    # tree5 = GenericTree(viewer, 'Node', 'center', '05')
    # tree.add_variable('left', 'n.left=<__main__.Node instance at 02>')
    # tree.add_variable('right', 'n.right=<__main__.Node instance at 03>')
    # tree3.add_variable('right', 'head.right=<__main__.Node instance at 04>')
    # tree.add_variable('center', 'n.center=<__main__.Node instance at 05>')
    # tree.add_function('f')
    # tree.add_function_variable('f', 'v', 'v=1')
    tree.view()

    root.mainloop()                                       # start up the gui
