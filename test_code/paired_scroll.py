import sys
if sys.version[0] < '3':
    from Tkinter import *
else:
    from tkinter import *


class ScrolledTextPair(Frame):
    '''Two Text widgets and a Scrollbar in a Frame'''

    def __init__(self, master, **kwargs):
        Frame.__init__(self, master) # no need for super

        # Different default width
        # if 'width' not in kwargs:
        #     kwargs['width'] = 30

        # Creating the widgets
        self.left = Text(self, **kwargs)
        self.left.pack(side=LEFT, fill=BOTH, expand=True)
        self.right = Text(self, **kwargs)
        self.right.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar = Scrollbar(self)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        # Changing the settings to make the scrolling work
        self.scrollbar['command'] = self.on_scrollbar
        self.left['yscrollcommand'] = self.on_textscroll
        self.right['yscrollcommand'] = self.on_textscroll

    def on_scrollbar(self, *args):
        '''Scrolls both text widgets when the scrollbar is moved'''
        self.left.yview(*args)
        self.right.yview(*args)

    def on_textscroll(self, *args):
        '''Moves the scrollbar and scrolls text widgets when the mousewheel
        is moved on a text widget'''
        self.scrollbar.set(*args)
        self.on_scrollbar('moveto', args[0])


# Example
if __name__ == '__main__':
    root = Tk()

    t = ScrolledTextPair(root, bg='white', fg='black')
    t.pack(fill=BOTH, expand=True)
    for i in range(50):
        t.left.insert(END,"foo %s\n" % i)
        t.right.insert(END,"bar %s\n" % i)

    root.title("Text scrolling example")
    root.mainloop()