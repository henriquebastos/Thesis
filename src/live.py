from Tkinter import *
import os
import ScrolledText as ST

from pygments import lex
from pygments.lexers import PythonLexer

import communicate as Communicate

# RENAME to Environment

name = 'Noah\'s Live Programming Environment'
root = Tk(screenName=name, baseName=name, className=name)
user_code = ''
FILE_NAME = 'user_code.py'
scale_size = 0
prev_scale_setting = 0
executed_code = None

def display_executed_code(executed_code, executed_code_box, variable_box, output_box, total):
    display_map = {}
    tab_count = 0
    for key,value in executed_code.iteritems():
        display_line = ''
        if total >= 0:
            if 'result' in value:
                display_line += '{0}'.format(value['result'])
                if 'assigned' in value:
                    variable_box.insert(INSERT, value['result'] + '\n')
                if 'print' in value:
                    output_box.insert(INSERT, value['result'] + '\n')
            else:
                no_comma = True
                for k,v in value['values'].iteritems():
                    if no_comma:
                        no_comma = False
                    else:
                        display_line += ', '
                    display_line += '{0}={1}'.format(k,v)
        total -= 1
        tabs = ''
        for i in range(tab_count):
            tabs += '  '
        if value['lineno'] in display_map:
            current_length = len(display_map[value['lineno']])
            if current_length >= len(tabs):
                tab_count += 2
                tabs += '    '
            display_map[value['lineno']] += tabs[current_length:] + display_line
        else:
            display_map[value['lineno']] = tabs + display_line
        tab_count += 1
    for key,value in display_map.iteritems():
        executed_code_box.insert(float(key), value)


def reset_boxes(new_user_code, executed_code_box, variable_box, output_box):
    executed_code_box.delete(0.0, END)
    variable_box.delete(0.0, END)
    output_box.delete(0.0, END)
    for i in range(len(new_user_code.split('\n'))):
        executed_code_box.insert(float(i), '\n')


def highlight_code(textPad, event=None):
    textPad.mark_set("range_start", "1.0")
    data = textPad.get("1.0", "end-1c")
    for token, content in lex(data, PythonLexer()):
        textPad.mark_set("range_end", "range_start + %dc" % len(content))
        textPad.tag_add(str(token), "range_start", "range_end")
        print 'Token: {0} - Content: {1}'.format(str(token), content)
        textPad.mark_set("range_start", "range_end")



def debug_loop(from_box, executed_code_box, variable_box, output_box, scale, input_field):
    global user_code
    global scale_size
    global executed_code
    global prev_scale_setting
    new_user_code = from_box.get(0.0, END)[:-1]

    if user_code != new_user_code:
        highlight_code(from_box)
        user_code = new_user_code
        with open(FILE_NAME, "w") as code_file:
            code_file.write(user_code)
        try:
            communicator = Communicate.main('user_code.py', input_field)
            executed_code = communicator.executed_code
            reset_boxes(new_user_code, executed_code_box, variable_box, output_box)
            scale.config(to=len(executed_code))
            scale.set(len(executed_code))
            scale_size = len(executed_code)
            prev_scale_setting = scale_size
            display_executed_code(executed_code, executed_code_box, variable_box, output_box, scale_size)
        except:
            pass
    elif scale.get() < scale_size or scale.get() != prev_scale_setting:
        prev_scale_setting = scale.get()
        reset_boxes(new_user_code, executed_code_box, variable_box, output_box)
        display_executed_code(executed_code, executed_code_box, variable_box, output_box, scale.get())
    root.after(500, debug_loop, from_box, executed_code_box, variable_box, output_box, scale, input_field)  # reschedule event in 2 seconds

class Application(Frame):
    def get_input(self):
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
        QUIT["command"] =  self.quit
        QUIT.pack(side=LEFT)

        execution_step = Scale(menu_frame, orient=HORIZONTAL)
        execution_step.pack(side=LEFT)

        input_label = Label(menu_frame, text='Input')
        input_label.pack(side=LEFT)

        input_field = Entry(menu_frame)
        input_field.pack(side=LEFT)

        # input_button = Button(menu_frame)
        # input_button["text"] = "Enter",
        # input_button["command"] = self.get_input
        # input_button.pack(side=LEFT)


        code_box = ST.ScrolledText(code_frame, foreground='white', background='gray15')
        code_box.tag_configure('Token.Keyword', foreground='red')
        code_box.tag_configure('Token.Operator', foreground='red')
        code_box.tag_configure('Token.Name.Function', foreground='green')
        code_box.tag_configure('Token.Literal.Number.Integer', foreground='purple')
        code_box.tag_configure('Token.Name.Builtin', foreground='cyan')
        code_box.tag_configure('Token.Literal.String.Single', foreground='yellow')
        if os.path.isfile(FILE_NAME):
            with open(FILE_NAME, 'r') as code_file:
                lines = code_file.readlines()
                for line in lines:
                    code_box.insert(INSERT, line)
        code_box.pack({'side': 'left'})

        executed_code_box = Text(executed_code_frame)
        executed_code_box.pack({'side': 'left'})

        variable_box = Text(variable_frame)
        variable_box.pack({'side': 'left'})

        output_box = Text(output_frame)
        output_box.pack({'side': 'left'})

        root.after(500, debug_loop, code_box, executed_code_box, variable_box, output_box, execution_step, input_field)


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