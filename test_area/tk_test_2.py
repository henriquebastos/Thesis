# from tkinter import *

# root = Tk()

# def task():
#     print("hello")
#     root.after(2000, task)  # reschedule event in 2 seconds

# root.after(2000, task)
# root.mainloop()

from Tkinter import *
root = Tk(className ="My first GUI")
svalue = StringVar() # defines the widget state as string
w = Entry(root,textvariable=svalue) # adds a textarea widget
w.pack()


def act():
    print "you entered"
    print '%s' % svalue.get()

def task():
    print svalue.get()
    root.after(1000, task)  # reschedule event in 2 seconds
foo = Button(root,text="Press Me", command=act)
foo.pack()
foo.after(2000, task)
root.mainloop()
