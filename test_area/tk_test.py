from Tkinter import *
import ScrolledText as ST
import sys

sys.path.insert(0, '/Users/noahnegrey/Documents/thesis/src')

import communicate as Communicate

name = 'Noah\'s Live Programming Environment'
root = Tk(screenName=name, baseName=name, className=name)
user_code = ''

def debug_loop(from_box, to_box):
    global user_code
    new_user_code = from_box.get(0.0, END)
    if user_code != new_user_code:
        to_box.delete(0.0, END)
        user_code = new_user_code
        with open("user_code.py", "w") as code_file:
            code_file.write(user_code)
        communicator = Communicate.main('user_code.py')
        to_box.insert(0.0, communicator.executed_code)
    root.after(500, debug_loop, from_box, to_box)  # reschedule event in 2 seconds

class Application(Frame):
    def say_hi(self):
        print "hi there, everyone!"

    def createWidgets(self):
        self.bg = 'grey'
        main_frame = Frame(self, bg='grey')
        middle_frame = Frame(main_frame, bg='grey')
        menu_frame = Frame(middle_frame)
        code_frame = Frame(middle_frame)
        executed_code_frame = Frame(middle_frame)
        
        bottom_frame = Frame(main_frame, bg='grey')
        variable_frame = Frame(bottom_frame)
        output_frame = Frame(bottom_frame)

        main_frame.pack()
        middle_frame.pack(side=TOP)
        menu_frame.pack(side=TOP)
        code_frame.pack(side=LEFT)
        executed_code_frame.pack(side=LEFT)
        bottom_frame.pack(side=BOTTOM)
        variable_frame.pack(side=LEFT)
        output_frame.pack(side=LEFT)

        QUIT = Button(menu_frame)
        QUIT["text"] = "QUIT"
        QUIT["fg"]   = "red"
        QUIT["command"] =  self.quit
        QUIT.pack({"side": "left"})

        hi_there = Button(menu_frame)
        hi_there["text"] = "Hello",
        hi_there["command"] = self.say_hi
        hi_there.pack({"side": "left"})

        execution_step = Scale(menu_frame, orient=HORIZONTAL)
        execution_step.pack(side=LEFT)

        code_box = ST.ScrolledText(code_frame)
        code_box.pack({'side': 'left'})

        executed_code_box = Text(executed_code_frame)
        executed_code_box.insert(INSERT, 'Executed Code Frame')
        executed_code_box.pack({'side': 'left'})

        variable_box = Text(variable_frame)
        variable_box.insert(INSERT, 'Variable Frame')
        variable_box.pack({'side': 'left'})

        output_box = Text(output_frame)
        output_box.insert(INSERT, 'Output')
        output_box.pack({'side': 'left'})

        root.after(500, debug_loop, code_box, executed_code_box)


    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

app = Application(master=root)
app.mainloop()
root.destroy()

# tkFont
# tkMessageBox
# tkSimpleDialog
# Tkdnd
# TkDND