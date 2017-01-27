#########################################################################
# PyTree: sketch arbitrary tree data structures in a scrolled canvas;
# this version uses tree wrapper classes embedded in the viewer gui 
# to support arbitrary trees (i.e.. composition, not viewer subclassing);
# also adds tree node label click callbacks--run tree specific actions;
# see treeview_subclasses.py for subclass-based alternative structure;
# subclassing limits one tree viewer to one tree type, wrappers do not;
# see treeview_left.py for an alternative way to draw the tree object;
# see and run treeview.py for binary and parse tree wrapper test cases;
#########################################################################
# Source: http://books.gigatux.nl/mirror/pythonprogramming/0596000855_python2-CHP-17-SECT-10.html

from Tkinter import *
from tkMessageBox import showinfo

Width, Height = 560, 350                    # start canvas size (reset per tree)
Rowsz = 100                                 # pixels per tree row
Colsz = 100                                 # pixels per tree col

###################################
# interface to tree object's nodes
###################################

class TreeWrapper:                          # subclass for a tree type
    def children(self, treenode):
        assert 0, 'children method must be specialized for tree type'
    def label(self, treenode):
        assert 0, 'label method must be specialized for tree type'
    def value(self, treenode):
        return ''
    def onClick(self, treenode):            # node label click callback
        return ''

##################################
# tree view gui, tree independent
##################################

class TreeViewer(Frame):
    def __init__(self, wrapper, parent=None, tree=None, bg='white', fg='gray'):
        Frame.__init__(self, parent)
        self.pack(expand=YES, fill=BOTH)
        self.makeWidgets(bg)                    # build gui: scrolled canvas
        # self.master.title('PyTree 1.0')         # assume I'm run standalone
        self.wrapper = wrapper                  # embed a TreeWrapper object
        self.fg = fg                            # setTreeType changes wrapper 
        if tree:
           self.drawTree(tree)

    def makeWidgets(self, bg):
        # self.title = Label(self, text='PyTree 1.0')
        self.canvas = Canvas(self, bg=bg, borderwidth=0)
        vbar = Scrollbar(self)
        hbar = Scrollbar(self, orient='horizontal')

        # self.title.pack(side=TOP, fill=X)
        vbar.pack(side=RIGHT,  fill=Y)                  # pack canvas after bars
        hbar.pack(side=BOTTOM, fill=X)
        self.canvas.pack(side=TOP, fill=BOTH, expand=YES)

        vbar.config(command=self.canvas.yview)          # call on scroll move
        hbar.config(command=self.canvas.xview)
        self.canvas.config(yscrollcommand=vbar.set)     # call on canvas move
        self.canvas.config(xscrollcommand=hbar.set)
        self.canvas.config(height=Height, width=Width)  # viewable area size

    def clearTree(self):
        # mylabel = 'PyTree 1.0 - ' + self.wrapper.__class__.__name__
        # self.title.config(text=mylabel)
        self.unbind_all('<Button-1>')
        self.canvas.delete('all')                       # clear events, drawing

    def drawTree(self, tree):
        self.clearTree()
        wrapper = self.wrapper
        levels, maxrow = self.planLevels(tree, wrapper)
        self.canvas.config(scrollregion=(                     # scrollable area
            0, 0, (Colsz * (maxrow+3)), (Rowsz * len(levels)) ))  # upleft, lowright
        self.drawLevels(levels, maxrow, wrapper)

    def planLevels(self, root, wrap):
        levels = []
        maxrow = 0                                       # traverse tree to 
        currlevel = [(root, None)]                       # layout rows, cols
        while currlevel:
            levels.append(currlevel)
            size = len(currlevel)
            if size > maxrow:
                maxrow = size
            nextlevel = []
            for (node, parent) in currlevel:
                if node != None:
                    children = wrap.children(node)             # list of nodes
                    if not children:
                        nextlevel.append((None, None))         # leave a hole
                    else:
                        for child in children:
                            nextlevel.append((child, node))    # parent link
            currlevel = nextlevel
        return levels, maxrow

    def get_line_name(self, node, parent):
        for k,v in parent.variables.iteritems():
            if node.instance_id in v:
                return k
        return ''

    def drawLevels(self, levels, maxrow, wrap):
        rowpos = 0                                         # draw tree per plan
        for level in levels:                               # set click handlers
            colinc = (maxrow * Colsz) / (len(level) + 1)   # levels is treenodes
            colpos = 0
            for (node, parent) in level:
                colpos = colpos + colinc
                if node != None:
                    text = wrap.label(node)
                    win = Label(self.canvas, text=text, 
                                             bg=self.fg, bd=3, relief=RAISED)
                    win.pack()
                    win.bind('<Button-1>', 
                        lambda e, n=node, handler=self.onClick: handler(e, n))
                    win_width = Colsz*.5
                    if len(text) > 5:
                        win_width = Colsz*(.5 + (.5 * len(text) / 10))
                    self.canvas.create_window(colpos, rowpos, anchor=NW, 
                                window=win, width=win_width, height=Rowsz*.5)
                    if parent != None:
                        self.canvas.create_line(
                            parent.__colpos + Colsz*.25,    # from x-y, to x-y
                            parent.__rowpos + Rowsz*.5,
                            colpos + win_width*.5, rowpos, arrow='last', width=1)
                        line_name = self.get_line_name(node, parent)
                        if parent.__colpos >= colpos:
                            # draw text on left
                            self.canvas.create_text(
                                colpos + Colsz*.05,
                                rowpos - Rowsz*.25,
                                text=line_name)
                        else:
                            # draw text on right
                            self.canvas.create_text(
                                colpos + Colsz*.35,
                                rowpos - Rowsz*.25,
                                text=line_name)
                    node.__rowpos = rowpos
                    if len(text) > 5:
                        node.__colpos = colpos + win_width*.25
                        colpos += win_width * 0.5
                    else:
                        node.__colpos = colpos
            rowpos = rowpos + Rowsz

    def onClick(self, event, node):
        label = event.widget
        wrap  = self.wrapper
        text  = '{0}'.format(wrap.value(node))       # on label click
        result = wrap.onClick(node)                 # run tree action if any
        if result:
            text = text + '\n' + result             # add action result
        showinfo('PyTree', text)                    # popup std dialog
