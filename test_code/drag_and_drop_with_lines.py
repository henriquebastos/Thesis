# import Tkinter as tk
# import ttk

# def bDown_Shift(event):
#     tv = event.widget
#     select = [tv.index(s) for s in tv.selection()]
#     select.append(tv.index(tv.identify_row(event.y)))
#     select.sort()
#     for i in range(select[0],select[-1]+1,1):
#         tv.selection_add(tv.get_children()[i])

# def bDown(event):
#     tv = event.widget
#     if tv.identify_row(event.y) not in tv.selection():
#         tv.selection_set(tv.identify_row(event.y))    

# def bUp(event):
#     tv = event.widget
#     if tv.identify_row(event.y) in tv.selection():
#         tv.selection_set(tv.identify_row(event.y))    

# def bUp_Shift(event):
#     pass

# def bMove(event):
#     tv = event.widget
#     moveto = tv.index(tv.identify_row(event.y))    
#     for s in tv.selection():
#         tv.move(s, '', moveto)

# root = tk.Tk()

# tree = ttk.Treeview(columns=("col1","col2"), 
#                     displaycolumns="col2", 
#                     selectmode='none')

# # insert some items into the tree
# for i in range(10):
#     tree.insert('', 'end',iid='line%i' % i, text='line:%s' % i, values=('', i))

# tree.grid()
# tree.bind("<ButtonPress-1>",bDown)
# tree.bind("<ButtonRelease-1>",bUp, add='+')
# tree.bind("<B1-Motion>",bMove, add='+')
# tree.bind("<Shift-ButtonPress-1>",bDown_Shift, add='+')
# tree.bind("<Shift-ButtonRelease-1>",bUp_Shift, add='+')

# root.mainloop()

import os
import tkinter as tk
import tkinter.ttk as ttk


class App(object):
    def __init__(self, master, path):
        self.nodes = dict()
        frame = tk.Frame(master)
        self.tree = ttk.Treeview(frame)
        ysb = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        xsb = ttk.Scrollbar(frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.tree.heading('#0', text='Project tree', anchor='w')

        self.tree.grid()
        ysb.grid(row=0, column=1, sticky='ns')
        xsb.grid(row=1, column=0, sticky='ew')
        frame.grid()

        abspath = os.path.abspath(path)
        self.insert_node('', abspath, abspath)
        self.tree.bind('<<TreeviewOpen>>', self.open_node)

    def insert_node(self, parent, text, abspath):
        node = self.tree.insert(parent, 'end', text=text, open=False)
        if os.path.isdir(abspath):
            self.nodes[node] = abspath
            self.tree.insert(node, 'end')

    def open_node(self, event):
        node = self.tree.focus()
        abspath = self.nodes.pop(node, None)
        if abspath:
            self.tree.delete(self.tree.get_children(node))
            for p in os.listdir(abspath):
                self.insert_node(node, p, os.path.join(abspath, p))


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root, path='.')
    root.mainloop()